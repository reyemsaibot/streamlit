import datetime
import streamlit as st
import requests
import utils
import pandas as pd


def get_all_spaces():
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    url = utils.get_url(st.session_state.dsp_host, 'list_of_spaces')
    list_of_spaces = requests.get(url, headers=header).json()
    return list_of_spaces


def get_scheduled_views(space):
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)
    
    url = utils.get_url(st.session_state.dsp_host, 'monitor_application').format(**{"spaceID": space},
                                                                **{"application": 'VIEWS'})

    response = requests.get(url, headers=header)

    return response.json()

def get_persisted_views():
    view_list = []
    scheduled_view_list = []
    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(st.session_state.token, st.session_state.secret)

    for space in get_all_spaces():
        url = utils.get_url(st.session_state.dsp_host, "persisted_views").format(**{"spaceID": space})
        response = requests.get(url, headers=header)
        #print(space + '||' + str(response.status_code))

        # Nur wenn Status ist OK
        if response.status_code == 200:
            views = response.json()
            scheduled_views = get_scheduled_views(space)

            for scheduled_view in scheduled_views:
                scheduled_view_list.append(scheduled_view['objectId'])

            for view in views['tables']:
               
                # Reset Variable
                scheduled = ''

                number_of_partitions = ''
                partition_column = ''
                
                view_name = view['viewName']
                if view['replicationState'] == 'E':
                    replication_status = 'error'
                elif view['replicationState'] == 'A':
                    replication_status = 'available'
                    if view_name in scheduled_view_list:
                        scheduled = 'Y'
                    else:
                        scheduled = 'N'
                elif view['replicationState'] == 'D':

                    replication_status = 'virtual'

                if view['dataPersistency'] == 'Virtual':
                    data_persistend = 'N'
                else:
                    data_persistend = 'Y'

                if view['latestUpdate'] == '0000-00-00T00:00:00Z':
                    last_update = None
                else:
                    last_update = view['latestUpdate']


                memory_consumption = str(view['inMemorySizeReplicaTableMB']) + ' MB'
                disk_size = str(view['diskSizeReplicaTableInMB']) + ' MB'
                try:
                    business_name = view['viewBusinessName']
                except KeyError:
                    business_name = ''
                
                number_of_records = view['numberOfRecords']

                if view['partitioningExists']:
                    partition_exists = 'Y'
                    # Get Partitions
                    url = utils.get_url(st.session_state.dsp_host, 'partitioning').format(**{"spaceID": space}, **{"objectName": view_name})
                    response = requests.get(url, headers=header)

                    partition_list = response.json()
                    partition_column = partition_list['column']
                    number_of_partitions = len(partition_list['ranges'])
                else:
                    partition_exists = 'N'

                view_list.append((space, view_name,business_name,number_of_records,replication_status, scheduled, data_persistend,memory_consumption,disk_size,partition_exists, partition_column,number_of_partitions,last_update, datetime.datetime.now()))

    return pd.DataFrame(view_list, columns=['Space', 'View', 'Description', 'Number of Records', 'Status', 'Scheduled YN', 'Persistent YN', 'Memory Consumption', 'Disk Size', 'Partition YN', 'Partition Column', 'Number of Partitions', 'Last Update', 'Timestamp Created'])



