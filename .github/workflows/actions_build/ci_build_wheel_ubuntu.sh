#!/bin/bash
set -e

sudo apt-get install docker
source $GITHUB_WORKSPACE/env_dump.txt
export PYTHONFOLDER="cp314-cp314"
mkdir -p $HOME/software
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  export ARMDOCKER="_arm64"
fi
docker run --rm -e "PYTHONFOLDER=${PYTHONFOLDER}" -v $GITHUB_WORKSPACE:/home tbaudier/opengate_core:${GEANT4_VERSION}$ARMDOCKER /home/.github/workflows/createWheelLinux.sh
ls wheelhouse
rm -rf dist
mv wheelhouse dist
sudo chown -R runner:docker dist