import streamlit as st
import utils
import pandas as pd

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


    artifacts = utils.database_connection(query)

    where = ', '.join(f"'{a[0]}'" for a in artifacts)
    query = f'''
            SELECT *
            FROM "SYS"."OBJECT_DEPENDENCIES"
            WHERE BASE_OBJECT_NAME IN ({where});
        '''

    dependencies = utils.database_connection(query)
    query = f'''
                SELECT *
                FROM "SYS"."ASSOCIATIONS"
                WHERE TARGET_OBJECT_NAME IN({where});
            '''
    associations = utils.database_connection(query)

    for artifact in artifacts:

        dependencies_count = [row for row in dependencies if artifact[0] in row]
        associations_count = [row for row in associations if artifact[0] in row]

        result.append((st.session_state.dsp_space, artifact[0],len(dependencies_count), len(associations_count)))
    # DataFrame bauen
    df = pd.DataFrame(result, columns=['Space', 'Artifact', 'Dependencies', 'Associations'])
    # nur Objekte ohne Dependencies & Associations
    return df[(df["Dependencies"] == 0) & (df["Associations"] == 0)]