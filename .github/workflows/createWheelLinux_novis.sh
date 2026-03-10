#!/bin/bash

set -e -x
echo ${PYTHONFOLDER}
cd /home/core/
rm -rf build opengate_core.egg-info opengate_core/plugins opengate_core/opengate_core.cpython*.so
sed -i 's/name="opengate-core"/name="opengate-core-novis"/' setup.py
export PATH=/software/cmake/cmake/bin/:${PATH}
source /software/geant4/bin/geant4make.sh
export CMAKE_PREFIX_PATH=/software/geant4/bin:/software/itk/bin/:${CMAKE_PREFIX_PATH}

# Install docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf remove podman buildah
dnf -y install docker-ce docker-ce-cli containerd.io
systemctl start docker
systemctl enable docker

# Build the wheel
/opt/python/${PYTHONFOLDER}/bin/pip install wget colored setuptools
/opt/python/${PYTHONFOLDER}/bin/pip install cibuildwheel==3.4.0
export CIBW_BUILD_PLATFORM="build[uv]"
export CIBW_ARCHS="x86_64 aarch64"
export CIBW_PLATFORM="linux"
export CIBW_BEFORE_BUILD="python -m pip install colored"
/opt/python/${PYTHONFOLDER}/bin/python -m cibuildwheel --output-dir /home/core/dist
auditwheel repair /home/core/dist/*.whl -w /software/wheelhouse/ --plat "manylinux2014_x86_64"
cp -r /software/wheelhouse /home/
#/opt/python/${PYTHONFOLDER}/bin/pip install twine
#/opt/python/${PYTHONFOLDER}/bin/twine upload --repository-url https://test.pypi.org/legacy/ wheelhouse/*manylinux2014*.whl

