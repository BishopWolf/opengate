#!/bin/bash
set -e

# Install docker to build the linux wheel on ubuntu 24.04
#sudo apt-get update && sudo apt-get install ca-certificates curl gnupg
#sudo install -m 0755 -d /etc/apt/keyrings
#curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
#sudo chmod a+r /etc/apt/keyrings/docker.gpg
#echo \
#  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
#  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
#  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
#sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

source $GITHUB_WORKSPACE/env_dump.txt
export PYTHONFOLDER="cp314-cp314"

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install cibuildwheel
pip install cibuildwheel==3.4.0
pip install wget colored setuptools

# Setup the environment for the build
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  export CIBW_ARCHS="aarch64"
  export CIBW_MANYLINUX_AARCH64_IMAGE=tbaudier/opengate_core:${GEANT4_VERSION}$ARMDOCKER
else
  export CIBW_ARCHS="x86_64"
  export CIBW_MANYLINUX_AARCH64_IMAGE=tbaudier/opengate_core:${GEANT4_VERSION}
fi
export CIBW_PLATFORM="linux"
export CIBW_REPAIR_WHEEL_COMMAND_LINUX=""
export CIBW_SKIP="*-musllinux_*"
export CIBW_BEFORE_BUILD="
python -m pip install colored
mkdir opengate_core/plugins
cp -r /lib64/qt6/plugins/platforms/* opengate_core/plugins/
cp -r /lib64/qt6/plugins/imageformats opengate_core/plugins/
"

# expose external libraries to build environment
export CIBW_ENVIRONMENT="
CMAKE_PREFIX_PATH=/software/geant4/install:/software/itk/install
Geant4_DIR=/software/geant4/install/lib/cmake/Geant4
ITK_DIR=/software/itk/install/lib/cmake/ITK
LD_LIBRARY_PATH=/software/geant4/install/lib:/software/itk/install/lib
QT_PLUGIN_PATH=$QT_PLUGIN_DIR
QT_QPA_PLATFORM_PLUGIN_PATH=$QT_PLUGIN_DIR/platforms
"

# Run the build without docker
python -m cibuildwheel --output-dir dist 
for whl in dist/*.whl; do
  auditwheel repair $whl -w wheelhouse/ --plat manylinux_2_34_$CIBW_ARCHS
done

rm -rf dist
mkdir -p $GITHUB_WORKSPACE/dist
cp -r wheelhouse/. $GITHUB_WORKSPACE/dist