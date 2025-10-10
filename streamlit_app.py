from Streamlit1 import object_dependencies, exposed_views, database_tables, objects_in_taskchain, userlist, taskchain_start, notifcations, delete_objects, view_overview, unused_objects
import streamlit as st
import json
import pandas as pd
from hdbcli import dbapi  
from requests_oauthlib import OAuth2Session
import urllib.parse
import requests
import datetime

st.set_page_config(
    page_title="Datasphere Tools",
    page_icon="🛠️",
    layout="wide",
)



def intro():
    st.write("# SAP Datasphere Tools 👋")


def settings():
    processed = False

    # Initialisierung der Session-State-Variablen
    for key in [
        "dsp_host",
        "hdb_address",
        "hdb_port",
        "hdb_user",
        "hdb_password",
        "token",
        "secret",
        "oauth",
        "token_received",
    ]:
        st.session_state.setdefault(key, "")

    st.write("# Settings ⚙️")
    st.write("")

    with st.container(border=True):

        st.write('### New Configuration File')
        if st.button('Create new empty configuration', icon="🆕"):
            st.write("TODO")


       
        st.write("### Upload Configuration File")
        uploaded_file = st.file_uploader("Choose a file", type="json")
        
        if uploaded_file is not None:       
           
            config = json.load(uploaded_file)
            st.session_state['dsp_host'] = config["DATASPHERE"]["dsp_host"]
            st.session_state['hdb_address'] = config["HDB"]["hdb_address"]
            st.session_state['hdb_port'] = config["HDB"]["hdb_port"] 
            st.session_state['hdb_user'] = config["HDB"]["hdb_user"]
            st.session_state['hdb_password'] = config["HDB"]["hdb_password"]
            st.session_state['secret'] = config["SETTINGS"]["secrets_file"]
            st.session_state['token'] = config["SETTINGS"]["token_file"]
            
    
            processed = True
    placeholder = st.empty()
    if processed:

        with placeholder.container(border=True):
            st.write("Configuration Details:")

            st.write("DSP Host: ", st.session_state.get('dsp_host'))
            
            st.write("HDB Address: ", st.session_state.get('hdb_address'))
            st.write("HDB Port: ", st.session_state.get('hdb_port'))
            st.write("HDB User: ", st.session_state.get('hdb_user'))
            st.write("HDB Password: ", '*' * len(st.session_state.hdb_password))

            st.write("Token:", st.session_state.get('token'))
            st.write("Secret:", st.session_state.get('secret'))
            st.success("Configuration loaded successfully!", icon="🎉")
    else:
        st.info("Please upload a configuration file to proceed.", icon="ℹ️")

    with st.container(border=True):
        st.write("### OAuth Connection")

        if st.button('Start OAuth', icon="🔑"):
            oauth_process()
            if st.session_state.token_received != '':
                st.success("Token received and saved successfully!", icon="🎉")
            else:
                st.error("Failed to retrieve token. Please try again.", icon="❌")
        
@st.dialog("Cast your vote")
def oauth_process():
   
    code_url = get_initial_token(st.session_state.secret, st.session_state.token)   
    st.page_link(code_url, label=code_url, icon="🌎")
    st.info("Please enter the code you received after the OAuth process below.", icon="ℹ️")
    with st.form("my_form",clear_on_submit=False, enter_to_submit=True, border=True, width="stretch", height="content"):
        code = st.text_input("Enter Code", value='', help='Enter the code you received after the OAuth process', label_visibility="visible")
        submitted = st.form_submit_button(label="Submit", on_click=None)

    if submitted:
        with st.spinner("Wait for it...", show_time=True):
            st.session_state.token_received = access_request(st.session_state.secret,st.session_state.token,code) 
            st.rerun()

def get_initial_token(path_of_secret_file, token_file):
    f = open(path_of_secret_file)
    secrets = json.load(f)
    client_id_encode = urllib.parse.quote(secrets['client_id'])
    code_url = secrets['authorization_url'] + '?response_type=code&client_id=' + client_id_encode
    return code_url

def access_request(path_of_secret_file, token_file, code):
    f = open(path_of_secret_file)
    secrets = json.load(f)
    session = requests.session()
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
    token = OAuth_AccessRequest.json()
    expire = datetime.datetime.now() + datetime.timedelta(0,token['expires_in'])

    token['expire'] = expire.strftime("%Y-%m-%d %H:%M:%S")

    # Write token to file
    with open(token_file, 'w') as f:
        json.dump(token, f)
    return OAuth_AccessRequest.json()['access_token']


def check_session_state():
    if ('hdb_address' or 'hdb_user' or 'hdb_password' or 'secret' or 'token') not in st.session_state:
        st.warning("Please go to the Settings page and upload a configuration file first.", icon="⚠️")
        return True



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


def get_list_of_space():
    query = f'''
        SELECT SPACE_ID
        FROM "DWC_TENANT_OWNER"."SPACE_SCHEMAS"
        WHERE SCHEMA_TYPE = 'space_schema';
    '''
    return database_connection(query) 
    
def exposed_views_gui():
    if check_session_state():
        return

    st.write("# Exposed Views 👀")   
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  

        if st.button('Get Exposed Views', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                df = exposed_views.get_exposed_views()    
                with st.container(width=2000, border=True, horizontal="True"):
                    st.dataframe(df, width="stretch")  



def object_dependencies_gui():
    if check_session_state():
        return

    st.write("# Object Dependencies 📦")   
    with st.container(width=2000, border=True):

        object_name = st.text_input(label='Enter Object Name', value='', help='Enter the name of the object you want to analyze', label_visibility="visible")  

        if st.button('Get Object Dependencies', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                df = object_dependencies.get_object_dependencies(object_name)
                with st.container(width=2000, border=True, horizontal="True"):
                    st.dataframe(df, width="stretch")  

def get_memory_usage(seconds):

    query = f'''SELECT 
    SUBSTRING("TIME", 12, 8) as TIME,
    ROUND(MEMORY_USED / MEMORY_ALLOCATION_LIMIT * 100,2) as Memory

    FROM M_LOAD_HISTORY_HOST
    WHERE TO_DATE(LEFT(TIME,10)) = LEFT(NOW(),10) AND 
    TIME > ADD_SECONDS(NOW(), -{seconds})
    ORDER BY TIME ASC
    ;'''

    columns = [  "Time", "Memory"]
    data = database_connection(query)

    df = pd.DataFrame(data, columns=columns)
    with st.container(width=2000, border=True, horizontal="True"):
        placeholder = st.empty()
        placeholder.line_chart(df,x='Time', y='Memory', x_label='Time', y_label='Memory %', width=2000, height=600)


def memory_usage():
    if ('hdb_address' or 'hdb_user' or 'hdb_password') not in st.session_state:
        st.warning("Please go to the Settings page and upload a configuration file first.", icon="⚠️")
        return

    st.write("# Memory Usage 🧠")   
    with st.container(width=2000, border=True):

        seconds = st.text_input(label='Enter seconds', value='600', help='Enter how many seconds you want to look back', label_visibility="visible")  

        if st.button('Refresh', icon="🔄"):
            with st.spinner("Wait for it...", show_time=True):
                get_memory_usage(seconds)
        else:
            get_memory_usage(seconds)

def get_system_monitor():
    query = f''' SELECT 
    		"ACTIVE"."CONNECTION_ID",
    		CONN.CLIENT_APPLICATION,
    		CONN.CLIENT_TYPE,
    		CONN.CREATED_BY,
    		CONN.USER_NAME,
            MDX."APPLICATION_USER_NAME" AS USER,
    		"ACTIVE"."STATEMENT_STRING",
    		("ACTIVE"."ALLOCATED_MEMORY_SIZE"/1048576) as Allocated_Memory,
    		"ACTIVE"."LAST_EXECUTED_TIME",
    		"ACTIVE"."LAST_ACTION_TIME"
    	FROM "M_ACTIVE_STATEMENTS" AS ACTIVE
    		LEFT JOIN "M_CONNECTIONS" CONN ON ACTIVE."CONNECTION_ID" = CONN."CONNECTION_ID"
            LEFT JOIN 
            (SELECT DISTINCT "STATEMENT_ID", "APPLICATION_USER_NAME" FROM "M_SERVICE_THREADS") AS MDX ON MDX."STATEMENT_ID" = ACTIVE."STATEMENT_ID"
    	WHERE ACTIVE."STATEMENT_STATUS" = 'ACTIVE'
        ORDER BY MDX."APPLICATION_USER_NAME", ACTIVE."CONNECTION_ID", ACTIVE."ALLOCATED_MEMORY_SIZE" DESC;'''
    
    data = database_connection(query)   

    df = pd.DataFrame(data, columns=['Connection ID', 'Client Application', 'Client Type', 'Created By', 'User Name', 'User', 'Statement', 'Allocated Memory (MB)', 'Last Executed Time', 'Last Action Time'])
    with st.container(width=2000, border=True, horizontal="True"):
        placeholder = st.empty()
        placeholder.dataframe(df, width="stretch")

def system_monitor():
    if check_session_state():
        return

    st.write("# System Monitor 💻")   
    
    with st.container(width=2000, border=True):
        if st.button('Refresh', icon="🔄"):
            with st.spinner("Wait for it...", show_time=True):
                get_system_monitor()
        else:
            get_system_monitor()

def get_orphaned_objects():
    result = []
    query = f'''
    SELECT DISTINCT ARTIFACT_NAME
    FROM "{st.session_state.dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
    WHERE ARTIFACT_NAME NOT IN ('SPACE_TEC_OBJECTS', 'DEPLOYED_METADATA', 'ECN_OBJECTS_METADATA', 'VIEW_ANALYZER_RESULTS', 'NOTIFICATION_MAILING_LISTS',
                                'REPLICATIONFLOW_RUN_DETAILS','DELTA_PROVIDER_SUBSCRIBER', 'TRFFL_EXECUTE_RT_DATA', 'TRFFL_EXECUTE_RT_SETTINGS', 'VALIDATION_TASK_LOG',
                                'NOTIFICATION_MAILING_RUN_CONFIG','LOCAL_TABLE_VARIANTS','LOCAL_TABLE_OUTBOUND_METRICS','JUSTASK_NLQ_SAMPLES',
                                
                                'SAP.CURRENCY.VIEW.TCURC','SAP.CURRENCY.VIEW.TCURV','SAP.CURRENCY.VIEW.TCURX','SAP.CURRENCY.VIEW.TCURF','SAP.CURRENCY.VIEW.TCURT','SAP.CURRENCY.VIEW.TCURN',
                                'SAP.CURRENCY.VIEW.TCURW', 'SAP.CURRENCY.VIEW.TCURX'
                                );
    '''


    artifacts = database_connection(query)

    where = ', '.join(f"'{a[0]}'" for a in artifacts)
    query = f'''
            SELECT *
            FROM "SYS"."OBJECT_DEPENDENCIES"
            WHERE BASE_OBJECT_NAME IN ({where});
        '''

    dependencies = database_connection(query)
    query = f'''
                SELECT *
                FROM "SYS"."ASSOCIATIONS"
                WHERE TARGET_OBJECT_NAME IN({where});
            '''
    associations = database_connection(query)

    for artifact in artifacts:

        dependencies_count = [row for row in dependencies if artifact[0] in row]
        associations_count = [row for row in associations if artifact[0] in row]

        result.append((st.session_state.dsp_space, artifact[0],len(dependencies_count), len(associations_count)))
    # DataFrame bauen
    df = pd.DataFrame(result, columns=['Space', 'Artifact', 'Dependencies', 'Associations'])
    # nur Objekte ohne Dependencies & Associations
    df_orphaned= df[(df["Dependencies"] == 0) & (df["Associations"] == 0)]
    with st.container(width=2000, border=True, horizontal="True"):
        st.dataframe(df_orphaned, width="stretch")  



def orphaned_objects():
    if check_session_state():
        return

    st.write("# Find Orphaned Objects 🕵️‍♂️")   
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  

        if st.button("Let's go digging", icon="🚜"):
            with st.spinner("Wait for it...", show_time=True):
                get_orphaned_objects()

def taskchain_gui():
    if check_session_state():
        return

    st.write("# Find Objects in Taskchains 🕵️‍♂️")   
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  
       
        if st.button("Searching", icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                df = objects_in_taskchain.get_objects_in_taskchain()
                if df.empty:
                    st.info("No taskchain found.", icon="ℹ️")
                else:

                    object_name = st.text_input(label='Enter Object Name', value='', help='Enter the name of the object you want to filter', label_visibility="visible", key="object_name")

                    if st.button("Filter Object List"):
                        df = df[df['Object'].str.contains(object_name)]
                    st.dataframe(df, width="stretch")


def database_tables_gui():
    if check_session_state():
        return

    st.write("# Database Tables Size 📚")   
    with st.container(width=2000, border=True):
        if st.button('Get Database Tables', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                df = database_tables.get_database_tables()    
                with st.container(width=2000, border=True, horizontal="True"):
                    st.dataframe(df, width="stretch")


def userlist_gui():
    if check_session_state():
        return
    
    st.write("# User Overview 👥")
    with st.container(width=2000, border=True):
        with st.spinner("Wait for it...", show_time=True):
            df = userlist.get_user_overview()    
            st.dataframe(df, width="stretch")

def taskchain_start_gui():
    if check_session_state():
        return
    
    st.write("# Start Taskchain ▶️")
    with st.container(width=2000, border=True): 
        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  
        taskchain_name = st.text_input(label='Enter Taskchain Name', value='', help='Enter the name of the taskchain you want to start', label_visibility="visible", key="taskchain_name")
        if st.button('Start Taskchain', icon="▶️"):
            with st.spinner("Wait for it...", show_time=True):
                taskchain_start.start_taskchain(st.session_state.dsp_space, taskchain_name)

def notifications_gui():
    if check_session_state():
        return
    
    st.write("# Notifications 🔔")
    with st.container(width=2000, border=True): 
        with st.spinner("Wait for it...", show_time=True):
            df = notifcations.get_notifications()
            if df.empty:
                st.info("No notifications found.", icon="ℹ️")
            else:
                st.dataframe(df, width="stretch")


def unused_objects_gui():
    if check_session_state():
        return
    
    st.write("# Unused Objects 🙈")
    with st.container(width=2000, border=True): 
        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible")  
       

        with st.spinner("Wait for it...", show_time=True):
            df = unused_objects.get_unused_objects()
            if df.empty:
                st.info("No unused objects found.", icon="ℹ️")
            else:
                st.dataframe(df, width="stretch")


def delete_mass_gui():
    if check_session_state():
        return
    
    st.write("# Delete Objects 🚮")
       
    with st.container(width=1000, border=True):     
        st.session_state.dsp_space = st.selectbox(label='Select Space', options=[row[0] for row in get_list_of_space()], help='Select the DSP Space you want to use', index=0, label_visibility="visible")  
        ids = st.text_area(label="", help="Enter the IDs of the objects you want to delete")
        if st.button('Delete Objects'):
            with st.spinner("Wait for it...", show_time=True):
                status_code, text = delete_objects.delete_object(ids)
                st.write(status_code, text)

def view_overview_gui():
    if check_session_state():
        return
    
    st.write("# View Persistency Overview 👨‍💻")
    with st.container(width=1000, border=True):     
        with st.spinner("Wait for it...", show_time=True):
            df = view_overview.get_persisted_views()
            st.dataframe(df, width="stretch")


pages = {
    "Home": [
        st.Page(intro, title="Start"),
        st.Page(settings, title="Manage your settings"),
    ],
    "System": [
        st.Page(memory_usage, title="Memory Usage"),
        st.Page(system_monitor, title="System Monitor"),
        st.Page(notifications_gui, title="Notifications"),
        #st.Page(taskchain_logs_gui, title="TaskChain Logs"),
    ],
    "Tools": [
        st.Page(taskchain_start_gui, title="TaskChain Start"),
    ],
    
    "HouseKeeping": [
        st.Page(orphaned_objects, title="Orphaned Objects"),
        st.Page(unused_objects_gui, title="Unused Objects"),
        st.Page(delete_mass_gui, title="Delete Objects"),
        st.Page(view_overview_gui, title="View Persistency Overview")
    ],

    "Administration": [
        st.Page(taskchain_gui, title="Taskchain Objects"),
        st.Page(exposed_views_gui, title="Exposed Views"),
        st.Page(object_dependencies_gui, title="Object Dependencies"),
        st.Page(database_tables_gui, title="Database Tables Size"),
        st.Page(userlist_gui, title="User Overview"),
    ]
   
}

pg = st.navigation(pages)
pg.run()


