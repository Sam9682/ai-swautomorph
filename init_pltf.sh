#!/bin/bash

# Install Python and pip
sudo apt update
sudo apt --fix-broken install
sudo apt install -y python3 python3-pip python3-venv net-tools unzip

# Install Amazon Kiro CLI Chat
# wget https://desktop-release.q.us-east-1.amazonaws.com/latest/amazon-q.deb
curl -fsSL https://cli.kiro.dev/install | bash
sudo dpkg -i amazon-q.deb

# Install OVH shai
curl -fsSL https://raw.githubusercontent.com/ovh/shai/main/install.sh | sh
echo 'export PATH="/home/ubuntu/.local/bin:$PATH"' >> ~/.bashrc


# Install AWS shai
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
newgrp docker
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose

mkdir logs
chmod +x setup_modsecurity_config.sh

# Create a config file in ~/.aws/config
mkdir -p ~/.aws
cat > ~/.aws/config <<EOF
[profile OVH-SWAUTOMORPH]
region = gra
output = json
EOF

# Create a config file in ~/.aws/credentials
mkdir -p ~/.aws
cat > ~/.aws/credentials <<EOF
[OVH-SWAUTOMORPH]
aws_access_key_id = XXX
aws_secret_access_key = YYY
endpoint_url = https://s3.gra.io.cloud.ovh.net/
signature_version = s3v4
EOF

export AWS_DEFAULT_PROFILE=OVH-SWAUTOMORPH
export AWS_ENDPOINT_URL_S3=https://s3.gra.io.cloud.ovh.net/

# Clone AiSwAutoMorph PLTF including submodule shared
git clone git@github.com:Sam9682/ai-swautomorph.git
cd ai-swautomorph
git submodule update --init --recursive

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

echo "Modify the name of the PLTF in ./conf/deploy.ini !"