import streamlit as st
import streamlit_app as app
import utils
import requests
from datetime import datetime
import pandas as pd

def get_user_overview():

    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    today = datetime.now().date()
    url = utils.get_url(st.session_state.dsp_host, 'user_list')
    response = requests.get(url, headers=header)
    user_json = response.json()
    user_list = []
    for user in user_json:
        username = user['userName']
        for parameter in user['parameters']:
            if parameter['name'] == 'NUMBER_OF_DAYS_VISITED':
                days_visited = parameter['value']
            if parameter['name'] == 'LAST_LOGIN_DATE':
                value = parameter['value'][:10]
                last_login = datetime.fromtimestamp(int(value)).date()
                ago = today - last_login
            if parameter['name'] == 'FIRST_NAME':
                first_name = parameter['value']
            if parameter['name'] == 'LAST_NAME':
                last_name = parameter['value']
            if parameter['name'] == 'EMAIL':
                email = parameter['value']

        user_list.append((username,first_name,last_name,email,days_visited,last_login.strftime("%d.%m.%Y"), ago.days))
        days_visited = 0
        first_name = ''
        last_name = ''
        email = ''

    return pd.DataFrame(user_list, columns=['User Name', 'First Name', 'Last Name', 'E-Mail', 'Days Visited', 'Last Login', 'Days ago'])
  
