#!/bin/bash
set -e

SSL_DIR="/home/ubuntu/ai-swautomorph/ssl"
CERT_FILE="$SSL_DIR/STAR_swautomorph_com.crt"
KEY_FILE="$SSL_DIR/privateKey_STAR_swautomorph_com.key"
BUNDLE_URL="https://crt.sh/?d=2835394"

cd "$SSL_DIR"

# Download intermediate certificate bundle (adjust URL based on your CA)
echo "📥 Downloading intermediate certificates..."
curl -s https://ssl-tools.net/certificates/dac9024f54d8f6df94935fb1732638ca6ad77c13.pem -o intermediate.pem 2>/dev/null || \
wget -q https://letsencrypt.org/certs/lets-encrypt-r3.pem -O intermediate.pem 2>/dev/null || \
echo "# Add your CA's intermediate certificate here" > intermediate.pem

# Create full chain: your cert + intermediate + root
echo "🔗 Creating certificate chain..."
cat "$CERT_FILE" > fullchain.pem
[ -s intermediate.pem ] && cat intermediate.pem >> fullchain.pem

# Use the proper key
cp "$KEY_FILE" key.pem
chmod 600 key.pem

# Backup old files
[ -f cert.pem ] && mv cert.pem cert.pem.bak

# Set final certificate
cp fullchain.pem cert.pem
chmod 644 cert.pem

echo "✅ SSL chain fixed!"
echo "🔍 Verify with: openssl s_client -connect www.swautomorph.com:443 -showcerts"
