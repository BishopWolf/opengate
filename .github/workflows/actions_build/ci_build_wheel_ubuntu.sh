#!/bin/bash
set -e

# Install docker to build the linux wheel on ubuntu 24.04
sudo apt-get update && sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

source $GITHUB_WORKSPACE/env_dump.txt
export PYTHONFOLDER="cp314-cp314"
mkdir -p $HOME/software
if [ ${MATRIX_OS} == "ubuntu-24.04-arm" ]; then
  export ARMDOCKER="_arm64"
fi
# Run the build in docker
docker run --rm --privileged --cgroupns=host \
    -e "PYTHONFOLDER=${PYTHONFOLDER}" \
    -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/bin/docker:/usr/bin/docker
    -v $GITHUB_WORKSPACE:/home \
    tbaudier/opengate_core:${GEANT4_VERSION}$ARMDOCKER \
    /home/.github/workflows/createWheelLinux.sh
ls wheelhouse
rm -rf dist
mv wheelhouse dist
sudo chown -R runner:docker dist