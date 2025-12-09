#!/bin/bash
# Fix SSL certificate chain for swautomorph.com

curl -s http://crt.sectigo.com/SSL2BUYEMEARSADomainValidationSecureServerCA.crt -o /tmp/ssl2buy_ca.crt
openssl x509 -inform DER -in /tmp/ssl2buy_ca.crt -out /tmp/ssl2buy_ca.pem
sudo cp /tmp/ssl2buy_ca.pem /usr/local/share/ca-certificates/ssl2buy_ca.crt
sudo update-ca-certificates
rm /tmp/ssl2buy_ca.*
