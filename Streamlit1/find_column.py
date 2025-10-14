import streamlit_app as app

import utils
import pandas as pd

def find_objects(column):
    query = f'''SELECT
                    SCHEMA_NAME, TABLE_NAME
                    FROM "SYS"."M_CS_COLUMNS"
                    WHERE "COLUMN_NAME"= '{column}'
                    and SCHEMA_NAME not in ('_SYS_TABLE_REPLICA_DATA')
                ;'''
    
    list_of_objects = utils.database_connection(query)

    # Remove some wrong information at the end
    list_of_objects = [(a, b.replace('_$PT1', '').replace('_$PT2', '')) for a, b in list_of_objects]
    list_of_objects = sorted(list_of_objects, key=lambda x: x[0])

    return pd.DataFrame(data=list_of_objects, columns=['Space', 'Object'])

