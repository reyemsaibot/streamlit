import streamlit as st
import json
import pandas as pd
from hdbcli import dbapi  



def get_exposed_views():
    exposedViews = []
    dac_objects = []
    dac_items = []

    # Get objects which are exposed
    csn_files = get_csn_files()

    for csn in csn_files:
        csn = csn[1]
        csn_loaded = json.loads(csn)
        dac_objects.clear()
        dac_items.clear()

        objectName = list(csn_loaded['definitions'].keys())[0]
        label = csn_loaded['definitions'][objectName]['@EndUserText.label']
        try:
            exposed = csn_loaded['definitions'][objectName]['@DataWarehouse.consumption.external']
        except KeyError:
            exposed = False
        try:
            for dac in csn_loaded['definitions'][objectName]['@DataWarehouse.dataAccessControl.usage']:

                if len(dac['on']) == 3: # one column mapping
                    dac_items.append(dac['on'][0]['ref'][0])

                if len(dac['on']) == 7: # two column mapping
                    dac_items.append(dac['on'][0]['ref'][0])
                    dac_items.append(dac['on'][4]['ref'][0])

                dac_objects.append(dac["target"])

        except KeyError:
            dac_items.clear()
            dac_objects.clear()

        exposedViews.append((dsp_space, objectName, label, exposed, ', '.join(f'{item}' for item in dac_items), ', '.join(f'{object}' for object in dac_objects)))

    df = pd.DataFrame(exposedViews, columns=['Space', 'Object', 'Description', 'Exposed', 'DAC Item', 'DAC Object'])
    
    with st.container(width=2000, border=True, horizontal="True"):
        st.dataframe(df, width="stretch")  





def get_csn_files():
    # Connect to HDB
    conn = dbapi.connect(
        address=hdb_address,
        port=int(hdb_port),
        user=hdb_user,
        password=hdb_password
    )
    cursor = conn.cursor()

    # select statement to fetch remote table csn's. Selection on highest ARTIFACT_VERSION for each object.
    st = f'''
        SELECT A.ARTIFACT_NAME, A.CSN, A.ARTIFACT_VERSION
        FROM "{dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
        INNER JOIN (
          SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
          FROM "{dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
          WHERE SCHEMA_NAME = '{dsp_space}' AND ARTIFACT_NAME NOT LIKE '%$%' AND PLUGIN_NAME in ('tableFunction', 'InAModel')
          GROUP BY ARTIFACT_NAME

        ) B
        ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
        AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
    '''
    cursor.execute(st)
    rows = cursor.fetchall()
    conn.close()
    total_rows = len(rows)
    print('Total rows: ' + str(total_rows))
    return rows

def get_list_of_space():
    # Connect to HDB
    conn = dbapi.connect(
        address=hdb_address,
        port=int(hdb_port),
        user=hdb_user,
        password=hdb_password
    )
    cursor = conn.cursor()

    st = f'''
        SELECT SPACE_ID
        FROM "DWC_TENANT_OWNER"."SPACE_SCHEMAS"
        WHERE SCHEMA_TYPE = 'space_schema';
    '''
    cursor.execute(st)
    rows = cursor.fetchall()
    conn.close()
    return rows 



def draw_button():
    if st.button('Get Exposed Views', icon="🔍"):
        with st.spinner("Wait for it...", show_time=True):
            get_exposed_views()

with open('config_files/enercon.json', 'r') as f:
    config = json.load(f)

    dsp_host = config["DATASPHERE"]["dsp_host"]
    
    hdb_address = config["HDB"]["hdb_address"]
    hdb_port = config["HDB"]["hdb_port"]
    hdb_user = config["HDB"]["hdb_user"]
    hdb_password = config["HDB"]["hdb_password"]

st.title('🗒️ Datasphere Exposed Views')
st.set_page_config(layout="wide")
with st.container(width=2000, border=True, horizontal="True"):
    


    
    
    
   

    dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  

draw_button() 

