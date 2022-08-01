import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

if __name__ == "__main__":
    if os.path.exists('../credentials/token.pickle'):
        print("'../credentials/token.pickle' already exists. Exiting.")
        sys.exit(0)

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.metadata",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]

    flow = InstalledAppFlow.from_client_secrets_file('../credentials/google-credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('../credentials/token.pickle', 'wb') as token:
        pickle.dump(creds, token)
