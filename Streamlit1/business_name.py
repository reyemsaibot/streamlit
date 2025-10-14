import pandas as pd
import streamlit as st
import utils
import json

def get_business_and_technical_name(artifact):
    query = f'''
        SELECT A.CSN
        FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
        INNER JOIN (
          SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
          FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
          WHERE SCHEMA_NAME = '{st.session_state.dsp_space}'  AND ARTIFACT_NAME = '{artifact}'
          GROUP BY ARTIFACT_NAME

        ) B
        ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
        AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
    '''
    csn_files = utils.database_connection(query)
    for csn in csn_files:
        csn = csn[0]
        csn_loaded = json.loads(csn)
        print(csn_loaded)
        objectName = list(csn_loaded['definitions'].keys())[0]
        elements = csn_loaded["definitions"][objectName]["elements"]

        result =  [
                    (key, val["@EndUserText.label"])
                    for key, val in elements.items()
                    if "@EndUserText.label" in val
                ]
        
    return  pd.DataFrame(result, columns=['Field', 'Description'])