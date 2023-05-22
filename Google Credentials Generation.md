# Google Credentials Generation

How to generate Google credentials:

1. Navigate to [Google Cloud's Console](https://console.cloud.google.com/)
2. Login with desired Google account
3. Create/select project
4. *(Optional)* Configure OAuth consent screen
   1. Go to `APIs & Services` -> `OAuth consent screen`
   2. Select User Type
   3. Click `CREATE`
   4. Enter required fields
   5. Click `SAVE AND CONTINUE`
   6. Click `SAVE AND CONTINUE` (no scopes need to be added)
   7. (Optional) Add test users
   8. Click `SAVE AND CONTINUE`
5. Create OAuth credentials
   1. Go to `APIs & Services` -> `Credentials`
   2. Click `CREATE CREDENTIALS`
   3. Select `OAuth client ID`
   4. Select `Desktop app` application type
   5. Enter a client name
   6. Click `CREATE`
   7. Download JSON
6. Enable APIs
   1. Go to `APIs & Services` -> `Library`
   2. Search for `Gmail`
   3. Click on `Gmail API`
   4. Click `ENABLE`
   5. Go to `APIs & Services` -> `Library`
   6. Search for `YouTube`
   7. Click on `YouTube Data API v3`
   8. Click `ENABLE`
7. Generate Pickle file
   1. Move/Copy downloaded JSON to `./credentials/google-credentials.json`
   2. Run token generation script: `cd ./scripts && python ./generateTokenFile.py`
   3. Login through Google
   4. Close window
