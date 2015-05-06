#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2015 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy
import math
from gnuradio import gr

# TODO test with sample rates other than 11050
class same_decode_fb(gr.basic_block):
    """
    docstring for block same_decode_fb
    """
    def __init__(self, samp_rate):
        gr.basic_block.__init__(self,
            name="same_decode_fb",
            in_sig=[numpy.float32],
            out_sig=[numpy.byte])
        self.samp_rate = samp_rate
        self.CORRLEN = 18
        self.BPHASESTEP = int(0x10000/(1920e-6*samp_rate))
        self.ref = numpy.empty((2,2,self.CORRLEN))
        self.ref[0,0,:] = numpy.sin(numpy.arange(self.CORRLEN)/float(samp_rate)*(2*math.pi*(3/1920e-6)))
        self.ref[0,1,:] = numpy.cos(numpy.arange(self.CORRLEN)/float(samp_rate)*(2*math.pi*(3/1920e-6)))
        self.ref[1,0,:] = numpy.sin(numpy.arange(self.CORRLEN)/float(samp_rate)*(2*math.pi*(4/1920e-6)))
        self.ref[1,1,:] = numpy.cos(numpy.arange(self.CORRLEN)/float(samp_rate)*(2*math.pi*(4/1920e-6)))
        self.bphase = self.bitcount = self.lastbit = self.byte = self.lastbyte = self.bits = self.samebytes = 0
        self.hindex = -5
        self.set_history(self.CORRLEN+1)


    def forecast(self, noutput_items, ninput_items_required):
        #setup size of input_items[i] for work call
        #TODO this seems pretty good for 11050 sample rate.
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items * 100

    def general_work(self, input_items, output_items):
        n = len(input_items[0])
        if (n < self.CORRLEN):
            return 0
        buf = input_items[0]
        out = output_items[0]
        r = 0

        c00 = numpy.correlate(buf, self.ref[0,0,0:self.CORRLEN], mode='valid')
        c01 = numpy.correlate(buf, self.ref[0,1,0:self.CORRLEN], mode='valid')
        c10 = numpy.correlate(buf, self.ref[1,0,0:self.CORRLEN], mode='valid')
        c11 = numpy.correlate(buf, self.ref[1,1,0:self.CORRLEN], mode='valid')
        bits = ((c10*c10 + c11*c11) - (c00*c00 + c01*c01)) > 0
        consumed = len(bits)

        for i in xrange(0, len(bits)):
            if bits[i]:
                if self.bitcount < 6:
                    self.bitcount += 1
            else:
                if self.bitcount > -6:
                    self.bitcount -= 1

            if bits[i] != self.lastbit:
                if self.bphase < 0x6000:
                    self.bphase += self.BPHASESTEP/8
                else:
                    self.bphase -= self.BPHASESTEP/8

            self.lastbit = bits[i]
            self.bphase += self.BPHASESTEP
            if self.bphase >= 0x10000:
                self.bphase &= 0xffff
                r += self.gotbit(self.bitcount > 0, out, r)
                if r >= len(out):
                    consumed = i+1
                    break
        
        #output_items[0][:] = input_items[0]
        self.consume(0, consumed)
        #self.consume_each(len(input_items[0]))
        #print len(input_items[0]), consumed, len(out), r
        return r

    def gotbit(self, bit, out, r):
        self.byte >>= 1
        if bit:
            self.byte |= 0x80
        self.bits += 1
        if self.bits >= 8:
            self.bits = 0
            if self.byte & 0x80:
                if self.byte == 0xab:
                    out[r] = self.byte
                    return 1
                elif self.byte == 0xae:
                    self.byte >>= 2
                    self.bits = 6
                elif self.byte == 0xba:
                    self.byte >>= 4
                    self.bits = 4
                elif self.byte == 0xea:
                    self.byte >>= 6
                    self.bits = 2
                elif self.byte == 0xd5:
                    self.byte >>= 7
                    self.bits = 1
                out[r] = 0
                return 1
            elif self.byte == 0x57 and self.samebytes >= 4:
                self.byte >>= 1
                self.bits = 7
            elif self.byte == 0x5d and self.samebytes >= 4:
                self.byte >>= 3
                self.bits = 5
            elif self.byte == 0x75 and self.samebytes >= 4:
                self.byte >>= 5
                self.bits = 3
            else:
                if self.byte == self.lastbyte:
                    self.samebytes += 1
                else:
                    self.samebytes = 0
                out[r] = self.byte
                self.lastbyte = self.byte
                return 1
        return 0


