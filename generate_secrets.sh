#!/bin/bash
# Script to generate secure random secret keys for Smartbook

echo "==========================================
 Smartbook Secret Key Generator
==========================================
"

echo "1. Generating SECRET_KEY (for general application security):"
SECRET_KEY=$(openssl rand -hex 32)
echo "   SECRET_KEY=$SECRET_KEY"
echo ""

echo "2. Generating JWT_SECRET_KEY (for JWT token signing):"
JWT_SECRET_KEY=$(openssl rand -hex 32)
echo "   JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""

echo "==========================================
IMPORTANT: Copy these values to your .env file
==========================================
"

echo "After getting your Google OAuth credentials, update .env with:"
echo ""
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com"
echo "GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-<your-client-secret>"
echo ""
