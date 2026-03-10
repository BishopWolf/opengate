#!/bin/bash

set -e -x
echo ${PYTHONFOLDER}
cd /home/core/
export PATH=/software/cmake/cmake/bin/:${PATH}
source /software/geant4/bin/geant4make.sh
export CMAKE_PREFIX_PATH=/software/geant4/bin:/software/itk/bin/:${CMAKE_PREFIX_PATH}
. /opt/rh/gcc-toolset-14/enable

# Install docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf remove podman buildah
dnf -y install docker-ce docker-ce-cli containerd.io
usermod -aG docker ${USER}
newgrp docker
dockerd &
sleep 10 # Wait for docker to start

# Build the wheel
mkdir opengate_core/plugins
cp -r /lib64/qt6/plugins/platforms/* opengate_core/plugins/
cp -r /lib64/qt6/plugins/imageformats opengate_core/plugins/
/opt/python/${PYTHONFOLDER}/bin/pip install wget colored setuptools
/opt/python/${PYTHONFOLDER}/bin/pip install cibuildwheel==3.4.0
export CIBW_BUILD_PLATFORM="build[uv]"
export CIBW_ARCHS="x86_64 aarch64"
export CIBW_PLATFORM="linux"
export CIBW_BEFORE_BUILD="python -m pip install colored"
/opt/python/${PYTHONFOLDER}/bin/python -m cibuildwheel --output-dir /home/core/dist
archi=`uname -m`
if [ "$(uname -m)" = "aarch64" ]; then
  auditwheel repair /home/core/dist/*.whl -w /software/wheelhouse/ --plat "manylinux_2_34_aarch64"
else
  auditwheel repair /home/core/dist/*.whl -w /software/wheelhouse/ --plat "manylinux_2_34_x86_64"
fi
cp -r /software/wheelhouse /home/
#/opt/python/${PYTHONFOLDER}/bin/pip install twine
#/opt/python/${PYTHONFOLDER}/bin/twine upload --repository-url https://test.pypi.org/legacy/ wheelhouse/*manylinux2014*.whl
