import json
import dsp_token
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
from hdbcli import dbapi  
import requests

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

def get_list_of_space():
    query = f'''
        SELECT SPACE_ID
        FROM "DWC_TENANT_OWNER"."SPACE_SCHEMAS"
        WHERE SCHEMA_TYPE = 'space_schema';
    '''
    return database_connection(query) 


def get_space_names():
    import streamlit as st
    # Get Space Names
    header = initializeGetOAuthSession(st.session_state.token, st.session_state.secret)


    url = get_url(st.session_state.dsp_host, "spaces_name")
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        data = response.json()
        data = data['results']
        return {e["qualifiedName"]: e["businessName"] for e in data}

def database_connection(query):
    import streamlit as st
    try:
        conn = dbapi.connect(
            address=st.session_state.hdb_address,
            port=int(st.session_state.hdb_port),
            user=st.session_state.hdb_user,
            password=st.session_state.hdb_password
        )
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return []
    

def create_config_template():

    data = """{
                "DATASPHERE": {
                "dsp_host": "https://hcs.cloud.sap"
            },
            "HDB": {
                "hdb_address": ".hana.prod-eu10.hanacloud.ondemand.com",
                "hdb_port": 443,
                "hdb_user": "#",
                "hdb_password": ""
            },
            "SETTINGS": {
                "secrets_file": "PATH_TO_secret.json",
                "token_file": "PATH_TO_token.json"
            }
            }"""
    
    return data

def create_secret_template():
    data = """{

  "client_id": "",
  "client_secret": "",
  "authorization_url": "",
  "token_url": ""

}"""

    return data