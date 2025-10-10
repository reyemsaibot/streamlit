import utils
import json
import requests
import streamlit  as st


def delete_object(ids):

    # Initialize OAuth session
    header = utils.initializePutOAuthSession(st.session_state.token, st.session_state.secret)
    url = utils.get_url(st.session_state.dsp_host, "delete_objects").format(**{"spaceID": st.session_state.dsp_space})
    delete_objects = { "object_id": ", ".join(id for id in ids)}
    response = requests.delete(url, data=json.dumps(delete_objects), headers=header)
    return response.status_code, response.text

