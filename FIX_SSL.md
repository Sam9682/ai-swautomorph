# Fix SSL Certificate Chain (Error 21)

## Quick Fix

1. **Get intermediate certificates from your CA:**
   - Check your certificate provider's email
   - Download the CA bundle/intermediate certificate
   - Common names: `ca-bundle.crt`, `intermediate.crt`, `chain.pem`

2. **Create full chain:**
```bash
cd /home/ubuntu/ai-swautomorph/ssl
cat STAR_swautomorph_com.crt intermediate.crt > fullchain.pem
cp fullchain.pem cert.pem
cp privateKey_STAR_swautomorph_com.key key.pem
chmod 644 cert.pem
chmod 600 key.pem
``` 

3. **Restart application:**
```bash
cd /home/ubuntu/ai-swautomorph
docker-compose restart || python3 ControlPlanFlaskApp.py
```

## Identify Your CA

```bash
openssl x509 -in ssl/STAR_swautomorph_com.crt -text -noout | grep "Issuer:"
```

## Common CA Intermediate Certificates

**Let's Encrypt:**
```bash
wget https://letsencrypt.org/certs/lets-encrypt-r3.pem -O ssl/intermediate.pem
```

**Sectigo/Comodo:**
```bash
wget https://crt.sh/?d=2835394 -O ssl/intermediate.pem
```

**DigiCert:**
```bash
wget https://cacerts.digicert.com/DigiCertCA.crt -O ssl/intermediate.pem
```

## Verify Fix

```bash
openssl s_client -connect www.swautomorph.com:443 -showcerts < /dev/null 2>&1 | grep "Verify return code"
```

Expected: `Verify return code: 0 (ok)`
