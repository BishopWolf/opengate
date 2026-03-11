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
mkdir -p $HOME/software

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

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
export CIBW_BUILD_FRONTEND="build[uv]"
export CIBW_PLATFORM="linux"
export CIBW_REPAIR_WHEEL_COMMAND_LINUX=""
export CIBW_SKIP="*-musllinux_*"
export CIBW_BEFORE_BUILD="
pwd &&
ls -la &&
ls -la /project &&
cd core &&
export PATH=/software/cmake/cmake/bin/:${PATH} &&
source /software/geant4/bin/geant4make.sh &&
export CMAKE_PREFIX_PATH=/software/geant4/bin:/software/itk/bin/:${CMAKE_PREFIX_PATH} &&
. /opt/rh/gcc-toolset-14/enable &&
mkdir opengate_core/plugins &&
cp -r /lib64/qt6/plugins/platforms/* opengate_core/plugins/ && 
cp -r /lib64/qt6/plugins/imageformats opengate_core/plugins/ &&
/opt/python/${PYTHONFOLDER}/bin/pip install colored"

# Run the build in docker
#docker run --rm -e "PYTHONFOLDER=${PYTHONFOLDER}" -v $GITHUB_WORKSPACE:/home tbaudier/opengate_core:${GEANT4_VERSION}$ARMDOCKER /home/.github/workflows/createWheelLinux.sh

# Run the build without docker
python -m cibuildwheel --output-dir dist 
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  auditwheel repair dist/*.whl -w wheelhouse/ --plat "manylinux_2_34_aarch64"
else
  auditwheel repair dist/*.whl -w wheelhouse/ --plat "manylinux_2_34_x86_64"
fi
rm -rf dist
cp -r wheelhouse/* $GITHUB_WORKSPACE
#sudo chown -R runner:docker $GITHUB_WORKSPACE/dist