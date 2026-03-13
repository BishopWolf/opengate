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

# Install CMAKE, OpenGL, X11 and qt6
sudo apt-get update && sudo apt-get install -y cmake build-essential openssl libssl-dev git zip unzip pkg-config ninja-build \
  libgl1-mesa-dev libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev libxcb1-dev \
  qt6-base-dev qt6-base-dev-tools qt6-tools-dev qt6-tools-dev-tools qt6-image-formats-plugins qt6-wayland \
  libxerces-c-dev libfftw3-dev libexpat1-dev libmotif-dev libxmu-dev

# Répertoire des plugins Qt6
QT_PLUGIN_DIR=$(qtpaths6 --plugin-dir)

echo "Répertoire plugins : $QT_PLUGIN_DIR"
ls "$QT_PLUGIN_DIR/platforms"
ls "$QT_PLUGIN_DIR/imageformats"
export QT_PLUGIN_PATH=$QT_PLUGIN_DIR
export QT_QPA_PLATFORM_PLUGIN_PATH=$QT_PLUGIN_DIR/platforms

mkdir -p $HOME/software
mkdir -p $HOME/software/cmake $HOME/software/geant4/src $HOME/software/geant4/bin $HOME/software/itk/src $HOME/software/itk/bin $HOME/software/wheelhouse

if [ "${MATRIX_CACHE}" == 'true' ]; then
  # Install geant4
  cd $HOME/software/geant4
  git clone --branch $GEANT4_VERSION https://github.com/Geant4/geant4.git --depth 1 src
  cd bin
  cmake -DCMAKE_CXX_FLAGS=-std=c++17 \
    -DGEANT4_INSTALL_DATA=OFF \
    -DGEANT4_USE_QT=ON \
    -DGEANT4_USE_OPENGL_X11=ON \
    -DGEANT4_USE_QT_QT6=ON \
    -DGEANT4_BUILD_TLS_MODEL=global-dynamic \
    -DGEANT4_BUILD_MULTITHREADED=ON \
    -DGEANT4_USE_GDML=ON \
    ../src
  cmake --build . --config Release

  # Install ITK
  cd $HOME/software/itk
  git clone --branch $ITK_VERSION https://github.com/InsightSoftwareConsortium/ITK.git --depth 1 src
  cd bin
  cmake -DCMAKE_CXX_FLAGS=-std=c++17 \
    -DBUILD_TESTING=OFF \
    -DITK_USE_FFTWD=ON \
    -DITK_USE_FFTWF=ON \
    -DITK_USE_SYSTEM_FFTW:BOOL=ON \
    ../src
  cmake --build . --config Release
fi

cd $GITHUB_WORKSPACE
source $HOME/software/geant4/bin/geant4make.sh
export CMAKE_PREFIX_PATH=$HOME/software/geant4/bin:$HOME/software/itk/bin/:${CMAKE_PREFIX_PATH}
cd core

# copy qt6 plugins to bundle inside the wheel
# mkdir opengate_core/plugins
# cp -r $QT_PLUGIN_DIR/platforms/* opengate_core/plugins/
# cp -r $QT_PLUGIN_DIR/imageformats opengate_core/plugins/

# Setup the environment for the build
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  export CIBW_ARCHS="aarch64"
else
  export CIBW_ARCHS="x86_64"
fi
export CIBW_BUILD_FRONTEND="build[uv]"
export CIBW_PLATFORM="linux"
export CIBW_REPAIR_WHEEL_COMMAND_LINUX=""
export CIBW_SKIP="*-musllinux_*"
export CIBW_BEFORE_BUILD="python -m pip install colored"

# Run the build without docker
python -m cibuildwheel --output-dir dist 
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  auditwheel repair dist/*.whl -w wheelhouse/ --plat "manylinux_2_34_aarch64"
else
  auditwheel repair dist/*.whl -w wheelhouse/ --plat "manylinux_2_34_x86_64"
fi
rm -rf dist
mkdir -p $GITHUB_WORKSPACE/dist
cp -r wheelhouse/. $GITHUB_WORKSPACE/dist