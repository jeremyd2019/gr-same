INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_SAME same)

FIND_PATH(
    SAME_INCLUDE_DIRS
    NAMES same/api.h
    HINTS $ENV{SAME_DIR}/include
        ${PC_SAME_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    SAME_LIBRARIES
    NAMES gnuradio-same
    HINTS $ENV{SAME_DIR}/lib
        ${PC_SAME_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(SAME DEFAULT_MSG SAME_LIBRARIES SAME_INCLUDE_DIRS)
MARK_AS_ADVANCED(SAME_LIBRARIES SAME_INCLUDE_DIRS)

