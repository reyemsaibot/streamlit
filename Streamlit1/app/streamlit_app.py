import streamlit as st
import json
import pandas as pd
from hdbcli import dbapi  


# Global variables
dsp_space = ''


st.set_page_config(layout="wide")


def intro():
    st.write("# SAP Datasphere Tools 👋")
    st.sidebar.success("Tools loaded")



def settings():
    processed = False

    # Initialization session variables
    if 'dsp_host' not in st.session_state:
        st.session_state['dsp_host'] = ''
    if 'hdb_address' not in st.session_state:
        st.session_state['hdb_address'] = ''
    if 'hdb_port' not in st.session_state:
        st.session_state['hdb_port'] = ''
    if 'hdb_user' not in st.session_state:   
        st.session_state['hdb_user'] = ''
    if 'hdb_password' not in st.session_state:
        st.session_state['hdb_password'] = ''

    st.write("# Settings ⚙️")
    st.write("")
    with st.container(border=True):
        

        uploaded_file = st.file_uploader("Choose a file", type="json")
        
        if uploaded_file is not None:       
           
            config = json.load(uploaded_file)
            st.session_state['dsp_host'] = config["DATASPHERE"]["dsp_host"]
            st.session_state['hdb_address'] = config["HDB"]["hdb_address"]
            st.session_state['hdb_port'] = config["HDB"]["hdb_port"] 
            st.session_state['hdb_user'] = config["HDB"]["hdb_user"]
            st.session_state['hdb_password'] = config["HDB"]["hdb_password"]
            st.write("HDB Address: ", st.session_state.hdb_address)


            processed = True
        if processed:
            st.success("Configuration loaded successfully!", icon="🎉")
        else:
            st.info("Please upload a configuration file to proceed.", icon="ℹ️")


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
    import streamlit as st
    # Connect to HDB
    conn = dbapi.connect(
        address=st.session_state.hdb_address,
        port=int(st.session_state.hdb_port),
        user=st.session_state.hdb_user,
        password=st.session_state.hdb_password
    )
    cursor = conn.cursor()

    # select statement to fetch remote table csn's. Selection on highest ARTIFACT_VERSION for each object.
    st = f'''
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
    cursor.execute(st)
    rows = cursor.fetchall()
    conn.close()
    total_rows = len(rows)
    return rows

def get_list_of_space():
    import streamlit as st
    # Connect to HDB
    conn = dbapi.connect(
        address=st.session_state.hdb_address,
        port=int(st.session_state.hdb_port),
        user=st.session_state.hdb_user,
        password=st.session_state.hdb_password
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

    
    
def exposed_views():
    import streamlit as st

    if 'hdb_address' or 'hdb_user' or 'hdb_password' not in st.session_state:
        st.warning("Please go to the Settings page and upload a configuration file first.", icon="⚠️")
        return

    st.write("# Exposed Views 👀")   
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  

        if st.button('Get Exposed Views', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                get_exposed_views()    


def get_objects(object):
    # Connect to HDB
    
    conn = dbapi.connect(
        address=st.session_state.hdb_address,
        port=int(st.session_state.hdb_port),
        user=st.session_state.hdb_user,
        password=st.session_state.hdb_password
    )
    cursor = conn.cursor()

    # select statement to fetch object dependencies.
    st = f'''
        SELECT *
        FROM "SYS"."OBJECT_DEPENDENCIES"
        WHERE BASE_OBJECT_NAME = '{object}';
    '''
    cursor.execute(st)
    rows = cursor.fetchall()
    conn.close()
    total_rows = len(rows)
    print('Total rows: ' + str(total_rows))
    return rows

def get_object_dependencies(object):
    list_of_dependencies = []


    list_of_objects = get_objects(object)

    for object in list_of_objects:
         list_of_dependencies.append((object[3], object[6],object[7]))

    df = pd.DataFrame(list_of_dependencies, columns=['Object', 'Space', 'Dependency'])


def object_dependencies():
    import streamlit as st

    if 'hdb_address' or 'hdb_user' or 'hdb_password' not in st.session_state:
        st.warning("Please go to the Settings page and upload a configuration file first.", icon="⚠️")
        return

    st.write("# Object Dependencies 📦")   
    with st.container(width=2000, border=True):

        object_name = st.text_input(label='Enter Object Name', value='MY_VIEW', help='Enter the name of the object you want to analyze', label_visibility="visible")  

        if st.button('Get Object Dependencies', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                get_object_dependencies(object_name)









page_names_to_funcs = {
    "Start": intro,
    "Settings": settings,
    "Exposed Views": exposed_views,
    "Object Dependencies": object_dependencies
}

demo_name = st.sidebar.selectbox("Choose a tool", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()