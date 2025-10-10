import streamlit as st
import requests
import utils

def start_taskchain(spaceID, taskChain):

    # Initialize OAuth session
    header = utils.initializePutOAuthSession(st.session_state.token, st.session_state.secret)

    url = utils.get_url(st.session_state.dsp_host, 'run_task_chain').format(**{"spaceID": spaceID, **{"taskChain": taskChain}})
    response = requests.post(url, headers=header)

    print(f"Log ID lautet: {response.json()['logId']}")


