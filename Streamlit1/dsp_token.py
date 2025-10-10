import json
from requests_oauthlib import OAuth2Session
import urllib.parse
import requests
import datetime
def get_initial_token(path_of_secret_file, token_file):

    f = open(path_of_secret_file)

    secrets = json.load(f)

    client_id_encode = urllib.parse.quote(secrets['client_id'])

    code_url = secrets['authorization_url'] + '?response_type=code&client_id=' + client_id_encode
    print(code_url)

    session = requests.session()
    print('Enter the code: ')
    code = input()
    OAuth_AccessRequest = session.post( secrets['token_url'],
                                        auth=(secrets['client_id'], secrets['client_secret']),
                                        headers={"x-sap-sac-custom-auth": "true",
                                                 "content-type": "application/x-www-form-urlencoded",
                                                 "redirect_uri": 'http://localhost'
                                                },
                                        data={'grant_type': 'authorization_code',
                                              'code': code,
                                              'response_type': 'token'
                                             }
                                      )
    print(OAuth_AccessRequest.json())
    token = OAuth_AccessRequest.json()
    expire = datetime.datetime.now() + datetime.timedelta(0,token['expires_in'])

    token['expire'] = expire.strftime("%Y-%m-%d %H:%M:%S")

    write_file(token_file,token)
    return OAuth_AccessRequest.json()['access_token']
def refresh_token(path_of_secret_file, token_file):
    token = read_file(token_file)

    f = open(path_of_secret_file)

    secrets = json.load(f)

    extra = { 'client_id': secrets['client_id'],
              'client_secret': secrets['client_secret']
            }

    datasphere = OAuth2Session(secrets['client_id'], token=token)
    token = datasphere.refresh_token(token_url=secrets['token_url'], **extra)

    return token['access_token']

def read_file(path):
    # Open JSON file
    f = open(path)

    data = json.load(f)
    return data

def write_file(path, data):
    # Write JSON file
    with open(path, 'w') as f:
        json.dump(data, f)



