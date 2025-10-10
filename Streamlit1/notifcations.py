import streamlit as st
import requests
import utils
import pandas as pd


def get_notifications():
    list_of_notifications = []
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    url = utils.get_url(st.session_state.dsp_host, 'notification')
    response = requests.get(url, headers=header)
    notifications = response.json()
    for notification in notifications:
        type = notification['type']
        # Error or other impact (8 = successful)
        if type == 0:
            day = notification['timestamp'][0:10] # Position 0 - 10
            deploy_time = notification['timestamp'][11:19] # Position 11 - 19
            list_of_notifications.append((notification['title'], day, deploy_time))


    return pd.DataFrame(list_of_notifications, columns=['Notification', 'Date', 'Time'])    