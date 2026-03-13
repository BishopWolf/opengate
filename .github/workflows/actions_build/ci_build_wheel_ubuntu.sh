#!/bin/bash
set -e

source $GITHUB_WORKSPACE/env_dump.txt
export PYTHONFOLDER="cp314-cp314"

# install cibuildwheel
pip install cibuildwheel==3.4.0
pip install wget colored setuptools

# Setup the environment for the build
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  export ARMDOCKER="_arm64"
  export CIBW_ARCHS="aarch64"
  export CIBW_MANYLINUX_AARCH64_IMAGE=tbaudier/opengate_core:${GEANT4_VERSION}$ARMDOCKER
else
  export CIBW_ARCHS="x86_64"
  export CIBW_MANYLINUX_X86_64_IMAGE=tbaudier/opengate_core:${GEANT4_VERSION}
fi
export CIBW_PLATFORM="linux"
# export CIBW_REPAIR_WHEEL_COMMAND_LINUX=""
export CIBW_SKIP="*-musllinux_*"
export CIBW_BEFORE_BUILD='
python -m pip install colored &&
mkdir -p opengate_core/plugins &&
export QT_PLUGIN_DIR=$(qtpaths6 --plugin-dir) &&
cp -r -n $QT_PLUGIN_DIR/platforms/* opengate_core/plugins/ &&
cp -r -n $QT_PLUGIN_DIR/imageformats opengate_core/plugins/ &&
source /software/geant4/bin/geant4make.sh &&
. /opt/rh/gcc-toolset-14/enable
'

# expose external libraries to build environment
export CIBW_ENVIRONMENT='
CMAKE_PREFIX_PATH=/software/geant4/bin:/software/itk/bin/
Geant4_DIR=/software/geant4/lib/cmake/Geant4
ITK_DIR=/software/itk/lib/cmake/ITK
LD_LIBRARY_PATH=/software/geant4/lib:/software/itk/lib
'

# Run the build in custom docker
cd core
python -m cibuildwheel --output-dir dist 
mkdir -p $GITHUB_WORKSPACE/dist
mv dist/*.whl $GITHUB_WORKSPACE/dist/ 