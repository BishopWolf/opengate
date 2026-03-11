#!/bin/bash

set -e -x
echo ${PYTHONFOLDER}
cd /home/core/
export PATH=/software/cmake/cmake/bin/:${PATH}
source /software/geant4/bin/geant4make.sh
export CMAKE_PREFIX_PATH=/software/geant4/bin:/software/itk/bin/:${CMAKE_PREFIX_PATH}
. /opt/rh/gcc-toolset-14/enable
archi=`uname -m`

# Install docker
# dnf update -y
# dnf remove podman runc -y
# dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
# dnf install docker-ce-cli  -y

# Build the wheel
mkdir opengate_core/plugins
cp -r /lib64/qt6/plugins/platforms/* opengate_core/plugins/
cp -r /lib64/qt6/plugins/imageformats opengate_core/plugins/
/opt/python/${PYTHONFOLDER}/bin/pip install wget colored setuptools
/opt/python/${PYTHONFOLDER}/bin/pip install cibuildwheel==3.4.0
export CIBW_BUILD_PLATFORM="build[uv]"
if [ "$(uname -m)" = "aarch64" ]; then
  export CIBW_ARCHS="aarch64"
else
  export CIBW_ARCHS="x86_64"
fi
export CIBW_PLATFORM="linux"
export CIBW_REPAIR_WHEEL_COMMAND_LINUX=""
export CIBW_BEFORE_BUILD="python -m pip install colored"
/opt/python/${PYTHONFOLDER}/bin/python -m cibuildwheel --output-dir /home/core/dist

if [ "$(uname -m)" = "aarch64" ]; then
  auditwheel repair /home/core/dist/*.whl -w /software/wheelhouse/ --plat "manylinux_2_34_aarch64"
else
  auditwheel repair /home/core/dist/*.whl -w /software/wheelhouse/ --plat "manylinux_2_34_x86_64"
fi
cp -r /software/wheelhouse /home/
#/opt/python/${PYTHONFOLDER}/bin/pip install twine
#/opt/python/${PYTHONFOLDER}/bin/twine upload --repository-url https://test.pypi.org/legacy/ wheelhouse/*manylinux2014*.whl
