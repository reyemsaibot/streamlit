import json
import dsp_token
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta

def get_url(dsp_url, url_name):

    f = open('url.json')
    urls = json.load(f)

    # Get the specified URL from the Datasphere urls.  Update the tenant prefix
    return urls[url_name].replace("#dsp_url", dsp_url)

def initializeGetOAuthSession(token_file, secrets_file):
    token = ''
    expire = datetime(1970, 1, 1)
    # Get token if available
    f = open(token_file)

    try:
        token = json.load(f)
        expire = datetime.strptime(token['expire'], "%Y-%m-%d %H:%M:%S")
    except JSONDecodeError:
        pass

    if token == '':
        # Get Code
        dsp_token.get_initial_token(secrets_file, token_file)

    else:

        if expire + timedelta(days=30) <= datetime.now():
            token = ''

        # If expire date time is lower than current time
        if expire <= datetime.now() and token == '':
            # Get Code
            dsp_token.get_initial_token(secrets_file, token_file)

        # Refresh existing token
        token = dsp_token.refresh_token(secrets_file, token_file)

    header = {'authorization': "Bearer " + token,
              "accept": "application/vnd.sap.datasphere.object.content+json"}
    return header


def initializePutOAuthSession(token_file, secrets_file):
    token = ''
    expire = datetime(1970, 1, 1)
    # Get token if available
    f = open(token_file)

    try:
        token = json.load(f)
        expire = datetime.strptime(token['expire'], "%Y-%m-%d %H:%M:%S")
    except JSONDecodeError:
        pass

    if token == '':
        # Get Code
        dsp_token.get_initial_token(secrets_file, token_file)

    else:
        # Refresh existing token
        token = dsp_token.refresh_token(secrets_file, token_file)

        # If expire date time is lower than current time
        if expire <= datetime.now() and token == '':
            # Get Code
            dsp_token.get_initial_token(secrets_file, token_file)

    header = {'authorization': "Bearer " + token,
              "content-type": "application/json"}
    return header
