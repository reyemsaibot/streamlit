import streamlit as st
import utils
import requests
import pandas as pd

#Constants
objects_to_check_ids = []
unused_objects = []
number_of_entries = 100

def get_unused_objects():
    no_auth = ""

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    remote_tables = get_objects('N',0, "remote_table_list")
    views = get_objects('N',0,"view_list")
    local_tables = get_objects('N',0, 'local_table_list')
    dataflows = get_objects('N', 0, 'data_flow_list')

    objects = remote_tables + views + local_tables  + dataflows
    url = utils.get_url(st.session_state.dsp_host, "all_design_objects").format(**{"spaceID": st.session_state.dsp_space})
    # check if no authorization for a space is given
    try:
        all_design_objects = requests.get(url, headers=header).json()
        
    except requests.exceptions.JSONDecodeError:
        no_auth = st.warning("No authorization for this space", icon="ℹ️")
        return pd.DataFrame(), no_auth
    
    design_objects_dict = {obj['qualified_name']: obj['id'] for obj in all_design_objects['results']}

    # Iteriere über remote_tables und prüfe direkt, ob der Name im Dictionary existiert
    for object in objects:
        technical_name = object['technicalName']
        if technical_name in design_objects_dict:
           objects_to_check_ids.append(design_objects_dict[technical_name])

    url = utils.get_url(st.session_state.dsp_host, "dependency").format(**{"ID": ",".join(obj for obj in objects_to_check_ids)})

    response = requests.get(url, headers=header)
    if response.status_code == 200:
        dependency = response.json()
        for object in dependency:
            if dependency and object['dependencies'] == []:
                unused_objects.append((object['qualifiedName'], object['id']))
        return pd.DataFrame(unused_objects, columns=['Technical Name', 'ID']), no_auth



def get_objects(skip, skip_times, object_url):
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    objects = []
    if skip == 'N':
        url_parameter = f'?top={number_of_entries}'
    elif skip == 'Y':
        url_parameter = f'?skip={number_of_entries * skip_times}'
    url = utils.get_url(st.session_state.dsp_host, object_url).format(**{"spaceID": st.session_state.dsp_space}) + url_parameter
    response = requests.get(url, headers=header)
    if response.status_code == 200:
        if response.json() != []:
            objects = objects + response.json()
            skip_times = skip_times + 1
            objects = objects + get_objects('Y', skip_times, object_url)

    return objects





