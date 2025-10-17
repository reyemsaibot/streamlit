import argparse
import requests
from cron_descriptor import get_description, ExpressionDescriptor
import utils
import streamlit as st
from dateutil import parser as dateparser
import pandas as pd


def monitor(application, monitortype):

    object_list = []
    for space in get_list_of_spaces():
        for object in get_object_list(application, space):
            if application == 'LOCAL_TABLE_VARIANT':
                print(object)
            try:
                # cron job
                frequency = get_description(object['cron'])
            except KeyError:
                # other option
                frequency = format_frequency(object['frequency'])

            # Link
            link = utils.get_url(st.session_state.dsp_host, "link_monitor_object").format(**{"spaceID": space},
                                                                **{"monitortype": monitortype}, **{"objectName": object["objectId"]})
            object_list.append((object['spaceId'], object['description'],frequency,link))

    return pd.DataFrame(object_list, columns=['Space', 'Object', 'Frequency', 'Link'])



# List of all spaces in a tenant
def get_list_of_spaces():
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    url = utils.get_url(st.session_state.dsp_host, 'list_of_spaces')
    list_of_spaces = requests.get(url, headers=header).json()
    return list_of_spaces


def get_object_list(application, space):
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    url = utils.get_url(st.session_state.dsp_host, 'monitor_application').format(**{"spaceID": space},
                                                                **{"application": application})

    response = requests.get(url, headers=header)
    return response.json()


def format_frequency(freq):

    if freq['type'] == 'DAILY':
        daily = 'Daily'
    else:
        daily = freq['type']
    starttime = dateparser.parse(freq['startDate']).strftime("%H:%M:%S")
    if freq['interval'] != 1:
        interval = str(freq['interval'])
    else:
        interval = ''

    if interval != '' and freq['type'] == 'DAILY':
        text = "Every " + interval + " days at " + starttime
    else:
        text = interval + daily + " at " + starttime
    return text








