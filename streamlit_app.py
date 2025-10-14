from Streamlit1 import object_dependencies, exposed_views, database_tables, objects_in_taskchain, userlist, taskchain_start, notifcations, delete_objects, view_overview, unused_objects, taskchainlogs, shares_per_space, find_column, orphaned_objects, system_monitor, memory_usage
import streamlit as st
import json
import pandas as pd

from requests_oauthlib import OAuth2Session
import urllib.parse
import requests
import datetime
import utils

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
        "display",
        "df",
        "count"
    ]:
        st.session_state.setdefault(key, "")

    st.write("# Settings ⚙️")
    st.write("")

    with st.container(border=True):

        st.write('### New Configuration File')
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                    label="📥 Create new configuration file",
                    data=utils.create_config_template(),
                    file_name="config.json",
                    mime="application/json")
        with col2:
            st.download_button(                
                    label="📥 Create new secret file",
                    data=utils.create_secret_template(),
                    file_name="secret.json",
                    mime="application/json")
       
    with st.container(border=True):
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
   
    code_url = get_initial_token(st.session_state.secret)   
    st.page_link(code_url, label=code_url, icon="🌎")
    st.info("Please enter the code you received after the OAuth process below.", icon="ℹ️")
    with st.form("my_form",clear_on_submit=False, enter_to_submit=True, border=True, width="stretch", height="content"):
        code = st.text_input("Enter Code", value='', help='Enter the code you received after the OAuth process', label_visibility="visible")
        submitted = st.form_submit_button(label="Submit", on_click=None)

    if submitted:
        with st.spinner("Wait for it...", show_time=True):
            st.session_state.token_received = access_request(st.session_state.secret,st.session_state.token,code) 
            st.rerun()

def get_initial_token(path_of_secret_file):

    with open(path_of_secret_file, "r", encoding="utf-8") as f:    
        data = f.read()

    secrets = json.load(data)
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

    #if 

def selectbox_space():
    return st.selectbox(label='Select Space', options=[row for row in get_space_names()], help='Select the DSP Space you want to analyze', index=0, label_visibility="visible").split(' ')[0]  

def get_space_names():
    list_of_spaces = []
    spaces = utils.get_list_of_space()
    business_lookup = utils.get_space_names()
    for space in spaces:
        list_of_spaces.append(str(space[0]) + " [" + business_lookup[space[0]] + "]")
    return list_of_spaces


def exposed_views_gui():
    if check_session_state():
        return

    st.write("# Exposed Views 👀")   
    st.markdown("""Find views which are exposed for consumption and check if they have a Data 
                Access Control assigned.
            """)
    with st.container(width=2000, border=True):
        st.session_state.dsp_space = selectbox_space()
        if st.button('Get Exposed Views', icon="🔍"):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df = exposed_views.get_exposed_views()    
                if st.session_state.df.empty:
                   st.info("No exposed views found.", icon="ℹ️")
                   st.session_state.display = False
                else:
                   st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False



def object_dependencies_gui():
    if check_session_state():
        return

    st.write("# Object Dependencies 📦")   
    st.markdown("""Find the dependencies for a certain object
            """)
    with st.container(width=2000, border=True):

        object_name = st.text_input(label='Enter Object Name', value='', help='Enter the name of the object you want to analyze', label_visibility="visible")  

        if st.button('Find Object Dependencies'):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df = object_dependencies.get_object_dependencies(object_name)
                if st.session_state.df.empty:
                   st.info("No dependencies found.", icon="ℹ️")
                   st.session_state.display = False
                else:
                   st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False

def memory_usage_gui():
    if check_session_state():
        return

    st.write("# Memory Usage 🧠")   
    with st.container(width=2000, border=True):

        seconds = st.text_input(label='Enter seconds', value='600', help='Enter how many seconds you want to look back', label_visibility="visible")  

        if st.button('Refresh', icon="🔄"):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df = memory_usage.get_memory_usage(seconds)
        else:
            st.session_state.df = memory_usage.get_memory_usage(seconds)

    result = st.empty()
    with result.container(width=2000, border=True):    
        placeholder = st.empty()
        placeholder.line_chart(st.session_state.df,x='Time', y='Memory', x_label='Time', y_label='Memory %', width=2000, height=600)




def system_monitor_gui():
    if check_session_state():
        return

    st.write("# System Monitor 💻")   
    st.markdown("""The System Monitor shows all current working connections to the database. 
                """)
 
    with st.container(width=2000, border=True):
        if st.button('Refresh', icon="🔄"):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df  = system_monitor.get_system_monitor()
        else:
            st.session_state.df  = system_monitor.get_system_monitor()

    result = st.empty()
    with result.container(width=2000, border=True):    
        st.dataframe(data=st.session_state.df, hide_index=True)   

def orphaned_objects_gui():
    if check_session_state():
        return

    st.write("# Find Orphaned Objects 🚜")   
    st.markdown("""Find all orphaned objects in a certain space.
            """)
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = selectbox_space()

        if st.button("Let's go digging"):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df = orphaned_objects.get_orphaned_objects()
                if st.session_state.df.empty:
                   st.info("No orphaned objects found.", icon="ℹ️")
                   st.session_state.display = False
                else:
                   st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False


def taskchain_gui():
    if check_session_state():
        return

    st.write("# Find Objects in Taskchains 🕵️‍♂️")   
    with st.container(width=2000, border=True):

        st.session_state.dsp_space = selectbox_space()

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
    st.markdown(""" 
                Overview of all tables and views with the consuming disk and memory as well as number of records.""")
    with st.container(width=2000, border=True):
        with st.spinner("Wait for it...", show_time=True):
            st.session_state.df = database_tables.get_database_tables()    
            if st.session_state.df.empty:
                st.info("No shares found.", icon="ℹ️")
                st.session_state.display = False
            else:
                st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, use_container_width=True, hide_index=True)
            st.session_state.display = False

def userlist_gui():
    if check_session_state():
        return
    
    st.write("# User Overview 👥")
    st.markdown(""" 
                Overview of all users in the tenant with time of login, last login and days since the last login.""")
    with st.container(width=2000, border=True):
        with st.spinner("Wait for it...", show_time=True):
            df = userlist.get_user_overview()    
            st.dataframe(df, width="stretch")

def taskchain_start_gui():
    if check_session_state():
        return
    
    st.write("# Run Taskchain ▶️")
    st.markdown(""" 
                Run a TackChain in your tenant. Select a certain space and enter the technical 
                name of the TackChain""")
    with st.container(width=2000, border=True): 
        st.session_state.dsp_space = selectbox_space()
        taskchain_name = st.text_input(label='Enter Taskchain Name', value='', help='Enter the name of the taskchain you want to start', label_visibility="visible", key="taskchain_name")
        if st.button('Start Taskchain', icon="▶️"):
            with st.spinner("Wait for it...", show_time=True):
                logId = taskchain_start.start_taskchain(st.session_state.dsp_space, taskchain_name)
                st.info(f"The log id is {logId}")

def notifications_gui():
    if check_session_state():
        return
    
    st.write("# Notifications 🔔")
    with st.container(width=2000, border=True): 
        option = st.selectbox("What notifications should be displayed?",
                                ("All", "Successful", "Error"))


        with st.spinner("Wait for it...", show_time=True):
            df = notifcations.get_notifications(option)
            if df.empty:
                st.info("No notifications found.", icon="ℹ️")
            else:
                st.dataframe(df, width="stretch")


def unused_objects_gui():
    if check_session_state():
        return
    
    st.write("# Unused Objects 🙈")
    with st.container(width=2000, border=True): 
        st.session_state.dsp_space = selectbox_space()

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
        st.session_state.dsp_space = selectbox_space()
        ids = st.text_area(label="", help="Enter the IDs of the objects you want to delete")
        if st.button('Delete Objects'):
            with st.spinner("Wait for it...", show_time=True):
                status_code, text = delete_objects.delete_object(ids)
                st.write(status_code, text)

def view_overview_gui():
    if check_session_state():
        return
    
    st.write("# View Persistency Overview 👨‍💻")
    with st.container(width=2000, border=True, horizontal=True):     
        with st.spinner("Wait for it...", show_time=True):
            df = view_overview.get_persisted_views()
            st.dataframe(df, width="stretch")

def taskchain_logs_gui():
    if check_session_state():
        return
    
    st.write("# Task Chain Logs 🔗")
    with st.container(width=2000, border=True):   
        st.session_state.dsp_space = selectbox_space()
        if st.button('Get Logs'):
            with st.spinner("Wait for it...", show_time=True):
                df = taskchainlogs.get_log_information(st.session_state.dsp_space)
                st.dataframe(df, width="stretch")

def shares_per_space_gui():
   
    if check_session_state():
        return

    st.write("# Shares per Space 🕵️‍♂️")
    st.markdown(""" 
                Find all shares from the selected space. Either for a certain object or for all objects.""")
    with st.container(width=2000, border=True):   
        st.session_state.dsp_space = selectbox_space()
        artifact = st.text_input(label='Enter Object Name', value='', help='Enter the name of the object', label_visibility="visible")
        if st.button('Get Shares'):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df = shares_per_space.allSharesFromOneSpace(artifact)
                if st.session_state.df.empty:
                   st.info("No shares found.", icon="ℹ️")
                   st.session_state.display = False
                else:
                   st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False


def shares_per_target_gui():

    if check_session_state():
        return

    st.write("# Shares per Target 💠")
    st.markdown(""" 
                Find all objects which are shared from one space to the selected target space.""")
    with st.container(width=2000, border=True):   
        st.session_state.dsp_space = selectbox_space()
        if st.button('Get Shares'):
            with st.spinner("Wait for it...", show_time=True):
                st.session_state.df  = shares_per_space.shares_with_target_space()
                if st.session_state.df.empty:
                   st.info("No shares found.", icon="ℹ️")
                   st.session_state.display = False
                else:
                   st.session_state.display = True

    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False

def dac_per_user_gui():
    print('Y')


def column_in_object_gui():

    if check_session_state():
        return
     
    st.write("# Find column in Object 🤞")
             
    st.markdown(""" 
                You can enter a technical column name and search overall objects in the 
                Datasphere tenant!""")

    with st.container(width=2000, border=True):   
        column = st.text_input(label='Enter Column Name', value='', help='Enter the column of the object', label_visibility="visible")
        if st.button('Find Objects'):
            with st.spinner("Wait for it...", show_time=True):
               st.session_state.df = find_column.find_objects(column)
               if  st.session_state.df.empty:
                   st.info("No object found.", icon="ℹ️")
                   st.session_state.display = False
               else:
                   st.session_state.display  = True
        
    result = st.empty()
    if st.session_state.display:
        with result.container(width=2000, border=True):    
            st.dataframe(data=st.session_state.df, hide_index=True)   
            st.session_state.display = False


pages = {
    "Home": [
        st.Page(intro, title="Start"),
        st.Page(settings, title="Manage your settings", icon="⚙️"),
    ],
    "System": [
        st.Page(memory_usage_gui, title="Memory Usage", icon="🧠"),
        st.Page(system_monitor_gui, title="System Monitor", icon="💻"),
        st.Page(notifications_gui, title="Notifications"),
        st.Page(taskchain_logs_gui, title="TaskChain Logs"),

    ],
    "Tools": [
        st.Page(taskchain_start_gui, title="Run TaskChain", icon="▶️"),
        st.Page(column_in_object_gui, title="Column in Object", icon="🤞"),
        st.Page(dac_per_user_gui, title="DataAccessControl per User"),
    ],
    
    "HouseKeeping": [
        st.Page(orphaned_objects_gui, title="Orphaned Objects", icon="🚜"),
        st.Page(object_dependencies_gui, title="Find Object Dependencies", icon="📦"),
        st.Page(unused_objects_gui, title="Unused Objects"),
        st.Page(delete_mass_gui, title="Delete Objects"),
        st.Page(view_overview_gui, title="View Persistency Overview")
    ],

    "Administration": [
        st.Page(taskchain_gui, title="Taskchain Objects"),
        st.Page(exposed_views_gui, title="Exposed Views", icon="👀"),

        st.Page(database_tables_gui, title="Database Tables Size", icon="📚"),
        st.Page(userlist_gui, title="User Overview", icon="👥"),
        st.Page(shares_per_space_gui, title="Shares per Space", icon="🕵️‍♂️"),
        st.Page(shares_per_target_gui, title="Shares per Target", icon="💠"),
    ]
   
}

pg = st.navigation(pages)
pg.run()


