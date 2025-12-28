# Google OAuth2 Setup Guide for Smartbook

This guide walks you through setting up Google OAuth2 authentication for Smartbook.

## Prerequisites

- Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click project dropdown → "New Project"
3. Name: `Smartbook` (or your choice)
4. Click "Create" and wait ~30 seconds

### 2. Enable Required APIs

1. Go to "APIs & Services" → "Library"
2. Search and enable:
   - **Google+ API**
   - **People API**

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose **"External"** user type
3. Fill in **App Information**:
   - App name: ``
   - User support email: Your email
   - Application home page: `http://localhost:3001`
   - Developer contact email: Your email

4. Add **Scopes** (click "Add or Remove Scopes"):
   - ✅ `email` - See your primary Google Account email
   - ✅ `profile` - See your personal info
   - ✅ `openid` - Associate you with your info on Google

5. Add **Test Users**:
   - Click "+ Add Users"
   - Add your email and any test user emails
   - Click "Save and Continue"

6. Review and click "Back to Dashboard"

### 4. Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "+ Create Credentials" → "OAuth client ID"
3. Configure:
   - **Application type**: Web application
   - **Name**: `Smartbook OAuth Client`

4. Add **Authorized JavaScript origins**:
   ```
   http://localhost:3001
   http://localhost:8000
   ```

5. Add **Authorized redirect URIs**:
   ```
   http://localhost:8000/api/auth/google/callback
   http://localhost:3001/auth/callback
   ```

6. Click "Create"

7. **Save your credentials** (you'll see a popup):
   - **Client ID**: `123456789-abc...apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-abc123...`
   - Optionally download the JSON file

### 5. Update Environment Variables

1. **Generate secret keys**:
   ```bash
   ./generate_secrets.sh
   ```

   This will output:
   ```
   SECRET_KEY=<64-character-hex>
   JWT_SECRET_KEY=<64-character-hex>
   ```

2. **Edit `.env` file**:
   Open `.env` and update these values:

   ```bash
   # Security
   SECRET_KEY=<paste-SECRET_KEY-from-generator>

   # OAuth2 - Google
   GOOGLE_OAUTH_CLIENT_ID=<paste-your-client-id>.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-<paste-your-client-secret>
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
   FRONTEND_URL=http://localhost:3001
   BACKEND_URL=http://localhost:8000

   # JWT Tokens
   JWT_SECRET_KEY=<paste-JWT_SECRET_KEY-from-generator>
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7

   # CORS
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8000
   ```

### 6. Restart Services

After updating `.env`:

```bash
# Rebuild and restart backend
docker-compose build backend
docker-compose up -d backend

# Rebuild and restart admin frontend
docker-compose build admin-app
docker-compose up -d admin-app
```

### 7. Test OAuth Login

1. Open browser to: http://localhost:3001/login
2. Click "Continue with Google"
3. You should be redirected to Google's OAuth consent screen
4. Sign in with a test user you added in Step 3
5. Grant permissions
6. You'll be redirected back to Smartbook dashboard

## Troubleshooting

### Error: "redirect_uri_mismatch"
- **Cause**: The redirect URI in your OAuth request doesn't match what's configured
- **Fix**: Verify the redirect URI in Google Console exactly matches:
  ```
  http://localhost:8000/api/auth/google/callback
  ```

### Error: "Access blocked: This app's request is invalid"
- **Cause**: OAuth consent screen not properly configured
- **Fix**: Go back to OAuth consent screen and ensure all required fields are filled

### Error: "This app isn't verified"
- **Expected**: Normal for apps in testing mode
- **Action**: Click "Advanced" → "Go to Smartbook (unsafe)"
- **Note**: Only appears for external users not added to test users list

### Error: "Admin access required"
- **Cause**: User's Google account doesn't have admin role in Smartbook
- **Fix**: First user to login automatically gets admin role. Check database:
  ```bash
  docker-compose exec db psql -U smartbook -d smartbook \
    -c "SELECT email, role FROM users;"
  ```

## Production Setup

For production deployment:

1. **Change User Type to "Internal"** (if using Google Workspace)
   - Or keep "External" but submit for verification

2. **Update Authorized Origins**:
   ```
   https://admin.yourdomain.com
   https://api.yourdomain.com
   ```

3. **Update Redirect URIs**:
   ```
   https://api.yourdomain.com/api/auth/google/callback
   https://admin.yourdomain.com/auth/callback
   ```

4. **Update `.env` for production**:
   ```bash
   GOOGLE_OAUTH_REDIRECT_URI=https://api.yourdomain.com/api/auth/google/callback
   FRONTEND_URL=https://admin.yourdomain.com
   BACKEND_URL=https://api.yourdomain.com
   CORS_ORIGINS=https://checkin.yourdomain.com,https://admin.yourdomain.com,https://api.yourdomain.com
   ```

5. **Verify App** (if external):
   - Go to OAuth consent screen
   - Click "Publish App"
   - Submit for verification (required for >100 users)

## Security Best Practices

1. ✅ Never commit `.env` file to git (already in `.gitignore`)
2. ✅ Use different `SECRET_KEY` and `JWT_SECRET_KEY`
3. ✅ Rotate secrets periodically in production
4. ✅ Use environment-specific OAuth clients (dev, staging, prod)
5. ✅ Enable 2FA on Google Cloud project owner account
6. ✅ Regularly review OAuth consent screen settings
7. ✅ Monitor OAuth usage in Google Cloud Console

## Support

For issues:
1. Check Google Cloud Console → "APIs & Services" → "Credentials" for errors
2. Review backend logs: `docker-compose logs backend`
3. Check browser console for frontend errors
4. Verify all environment variables are set correctly

## References

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI OAuth Documentation](https://fastapi.tiangolo.com/advanced/security/)
- [Authlib Documentation](https://docs.authlib.org/en/latest/)
