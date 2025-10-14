import requests
import json
import pandas as pd
import utils
import streamlit as st
import streamlit_app as app



def allSharesFromOneSpace(artifact):
    shares_per_space = [] # List of all objects

    if artifact != '':
        where_condition = f'''ARTIFACT_NAME = '{artifact}' '''
    else:
        where_condition = f'''ARTIFACT_NAME NOT LIKE '%$%' '''

    # select statement to fetch remote table csn's. Selection on highest ARTIFACT_VERSION for each object.
    query = f'''
        SELECT A.ARTIFACT_NAME, A.CSN, A.ARTIFACT_VERSION
        FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
        INNER JOIN (
          SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
          FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
          WHERE SCHEMA_NAME = '{st.session_state.dsp_space}' AND {where_condition} 
          
          GROUP BY ARTIFACT_NAME

        ) B
        ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
        AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
    '''

    # Get Database Objects
    dsp_objects = utils.database_connection(query)

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    space_name = utils.get_space_names()

    for dsp_object in dsp_objects:
        objectName = dsp_object[0]
        url = utils.get_url(st.session_state.dsp_host, "shares_per_space").format(**{"spaceID": st.session_state.dsp_space},**{"objectName": objectName})

        response = requests.get(url, headers=header)
        if response.text != "":
            # Get Object
            try:
                object = list(response.json()[objectName])
            except KeyError:
                continue

            csn = json.loads(dsp_object[1])
            description = csn['definitions'][objectName]['@EndUserText.label']

            # Get each shared space
            for space in object:

                # Issue in the API, sometimes the space is missing
                shared_space = space['name']
                shares_per_space.append((objectName, description, shared_space, space_name[shared_space]))

    return pd.DataFrame(shares_per_space, columns=['Object', 'Description', 'Shared Space', 'Space Name'])
     

def shares_with_target_space():
    shares_per_target = []

    space_names = utils.get_space_names()

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token,st.session_state.secret)

    url = utils.get_url(st.session_state.dsp_host, 'shares_per_target').format(**{"spaceID": st.session_state.dsp_space})
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        objects = response.json()

        for object in objects['results']:
            space = object['properties']['#spaceName']
            technicalName = object['name']
            description = object['businessName']

            shares_per_target.append((space,space_names[space], technicalName, description ))

        return pd.DataFrame(shares_per_target, columns=['Space','Space Name', 'Technical Name', 'Description'])
          




