import streamlit_app  as app
import streamlit as st
import pandas as pd
import json

def get_objects_in_taskchain():

    list_of_descriptions = []
    list_of_objects_in_taskchains = []
    list_of_tf_descriptions = []

    csn_files = get_taskchain_description()

    # Get all descriptions for artifacts
    csn_description = get_description()

    # Get description for Transformation Flows
    tf_description = get_transformationflow_description()

    for description in csn_description:
        csn_loaded = json.loads(description[1])
        objectName = list(csn_loaded['definitions'].keys())[0]
        label = csn_loaded['definitions'][objectName]['@EndUserText.label']
        list_of_descriptions.append((objectName, label))

    for description in tf_description:
        technicalName = description[0]
        taskchain_json = json.loads(description[1])
        description = taskchain_json['csn']['transformationflows'][technicalName]['@EndUserText.label']
        list_of_tf_descriptions.append((technicalName, description))

    for csn in csn_files:
        technicalName = csn[0]
        taskchain_json = json.loads(csn[1])
        description = taskchain_json['csn']['taskchains'][technicalName]['@EndUserText.label']
        nodes = taskchain_json['csn']['taskchains'][technicalName]['nodes'][1:]

        for node in nodes:
            if node['type'] == 'TASK':
                try:
                    space = taskchain_json['#spaceName']
                except KeyError:
                    space = ''
                
                # Extracting the required fields
                applicationId = node['taskIdentifier']['applicationId']
                activity = node['taskIdentifier']['activity']
                objectId = node['taskIdentifier']['objectId']
                label = ''.join([t[1]for t in list_of_descriptions if t[0] == objectId])

                # Special case Transformation Flow
                if applicationId == 'TRANSFORMATION_FLOWS':
                    label = [t[1] for t in list_of_tf_descriptions if t[0] == objectId]
                    
                list_of_objects_in_taskchains.append((space,technicalName, description, applicationId,objectId, label, activity))
    return pd.DataFrame(list_of_objects_in_taskchains, columns=['Space', 'Task Chain', 'Label', 'Application ID', 'Object','Description', 'Activity'])

def get_taskchain_description():
    query = f'''
        SELECT NAME, JSON
        FROM "{st.session_state.dsp_space}$TEC"."DEPLOYED_METADATA"
        WHERE REPOSITORY_OBJECT_TYPE = 'DWC_TASKCHAIN';
    '''

    return app.database_connection(query)


def get_transformationflow_description():
    query = f'''
        SELECT NAME, JSON
        FROM "{st.session_state.dsp_space}$TEC"."DEPLOYED_METADATA"
        WHERE REPOSITORY_OBJECT_TYPE = 'DWC_TRANSFORMATIONFLOW';
    '''
    return app.database_connection(query)


def get_description():
    query = f'''
        SELECT A.ARTIFACT_NAME, A.CSN, A.ARTIFACT_VERSION
        FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
        INNER JOIN (
          SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
          FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
          WHERE SCHEMA_NAME = '{st.session_state.dsp_space}' AND ARTIFACT_NAME NOT LIKE '%$%' AND PLUGIN_NAME in ('tableFunction', 'InAModel')
          GROUP BY ARTIFACT_NAME

        ) B
        ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
        AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
    '''
    return app.database_connection(query)