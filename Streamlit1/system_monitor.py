import utils
import pandas as pd

def get_system_monitor():

    query = f''' SELECT 
            "ACTIVE"."CONNECTION_ID",
            CONN.CLIENT_APPLICATION,
            CONN.CLIENT_TYPE,
            CONN.CREATED_BY,
            CONN.USER_NAME,
            MDX."APPLICATION_USER_NAME" AS USER,
            "ACTIVE"."STATEMENT_STRING",
            ("ACTIVE"."ALLOCATED_MEMORY_SIZE"/1048576) as Allocated_Memory,
            "ACTIVE"."LAST_EXECUTED_TIME",
            "ACTIVE"."LAST_ACTION_TIME"
        FROM "M_ACTIVE_STATEMENTS" AS ACTIVE
            LEFT JOIN "M_CONNECTIONS" CONN ON ACTIVE."CONNECTION_ID" = CONN."CONNECTION_ID"
            LEFT JOIN 
            (SELECT DISTINCT "STATEMENT_ID", "APPLICATION_USER_NAME" FROM "M_SERVICE_THREADS") AS MDX ON MDX."STATEMENT_ID" = ACTIVE."STATEMENT_ID"
        WHERE ACTIVE."STATEMENT_STATUS" = 'ACTIVE'
        ORDER BY MDX."APPLICATION_USER_NAME", ACTIVE."CONNECTION_ID", ACTIVE."ALLOCATED_MEMORY_SIZE" DESC;'''

    data = utils.database_connection(query)   

    return pd.DataFrame(data, columns=['Connection ID', 'Client Application', 'Client Type', 'Created By', 'User Name', 'User', 'Statement', 'Allocated Memory (MB)', 'Last Executed Time', 'Last Action Time'])
