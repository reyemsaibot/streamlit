import streamlit as st
import requests
import pandas as pd
import utils

def get_database_tables():
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    database_tables = []

    url = utils.get_url(st.session_state.dsp_host, 'list_of_spaces')
    response = requests.get(url,headers=header)
    space_list = response.json()

    for spaceID in space_list:
        url = utils.get_url(st.session_state.dsp_host, 'space_tables').format(**{"spaceID": spaceID})
        response = requests.get(url, headers=header)
        space_json = response.json()
        try:
            for table in space_json[spaceID]['tables']:
                tableName = table['tableName']
                usedDisk = round((table['usedDisk'] / 1000 / 1000),2) # MB
                usedMemory = round(table['usedMemory'] / 1000 / 1000,2)
                records = table['recordCount']
                database_tables.append((spaceID, tableName, usedDisk, usedMemory, records))
        except KeyError:
            continue

    df = pd.DataFrame(database_tables, columns=['Space', 'Table Name', 'Used Disk', 'Used Memory', 'Records'])
    # Change column B and C's values to integers
    df = df.astype({'Used Disk': float, 'Used Memory': float, 'Records': int})
    df['Records'] = df['Records'].apply(lambda x: f"{x:,}".replace(",", "."))
    

    return df
