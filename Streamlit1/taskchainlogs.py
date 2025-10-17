import datetime
import requests
import pandas as pd
import utils
import streamlit as st



def get_log_information(spaceID):

    list_of_taskchains = get_list_of_taskchains(spaceID)

    log_details = []

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    for task_chain in list_of_taskchains:
        url = utils.get_url(st.session_state.dsp_host, 'task_chain_logs').format(**{"spaceID": spaceID}, **{"taskChain": task_chain[0]})
        response = requests.get(url, headers=header)
        logs = response.json()

        for log in logs['logs']:
         
            logID = log['logId']
            object = log['objectId']
            spaceID = log['spaceId']
            startTime = datetime.datetime.fromisoformat(log['startTime'])
            # current running tasks have no endtime
            try:
                endTime = datetime.datetime.fromisoformat(log['endTime'])
                duration = str(endTime - startTime).split(".")[0]
            except KeyError:
                endTime = ''
                duration = ''
            
            status = log['status']

            link = utils.get_url(st.session_state.dsp_host, "link_monitor_object").format(**{"spaceID": spaceID},
                                                                **{"monitortype": 'taskChainMonitor'}, **{"objectName": object})

            log_details.append((spaceID, logID, object,task_chain[1], str(startTime).split(".")[0], str(endTime).split(".")[0], duration, status, link))

    return pd.DataFrame(log_details, columns=['Space', 'LogID', 'Object', 'Description', 'Start', 'End', 'Duration', 'Status', 'Link'])





def get_list_of_taskchains(spaceID):

    list_of_taskchains = []

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    url = utils.get_url(st.session_state.dsp_host,'task_chain_list').format(**{"spaceID": spaceID})
    # empty request
    try:

        response = requests.get(url, headers=header)
    except requests.exceptions.JSONDecodeError:
        return

    taskchains = response.json()

    for taskchain in taskchains:
        technical_name = taskchain['technicalName']

        # Get Task Chain Technical URL and replace SpaceID + Technical Name
        url = utils.get_url(st.session_state.dsp_host, 'task_chain_technical').format(**{"spaceID": spaceID}, **{"technicalName": technical_name})
        response = requests.get(url, headers=header)

        description = response.json()['taskchains'][technical_name]['@EndUserText.label']
        list_of_taskchains.append((technical_name, description))

    return list_of_taskchains






