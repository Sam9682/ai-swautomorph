#!/bin/bash

# Install Python and pip
sudo apt update
sudo apt install -y python3 python3-pip

# Install Python requirements
pip3 install -r requirements.txt

# Install Amazon Q Chat
wget https://desktop-release.q.us-east-1.amazonaws.com/latest/amazon-q.deb
sudo dpkg -i amazon-q.deb

# Install OVH shai
curl -fsSL https://raw.githubusercontent.com/ovh/shai/main/install.sh | sh
echo 'export PATH="/home/ubuntu/.local/bin:$PATH"' >> ~/.bashrc

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
newgrp docker
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose

