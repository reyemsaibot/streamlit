import utils
import pandas as pd

def get_memory_usage(seconds):

    query = f'''SELECT 
    SUBSTRING("TIME", 12, 8) as TIME,
    ROUND(MEMORY_USED / MEMORY_ALLOCATION_LIMIT * 100,2) as Memory

    FROM M_LOAD_HISTORY_HOST
    WHERE TO_DATE(LEFT(TIME,10)) = LEFT(NOW(),10) AND 
    TIME > ADD_SECONDS(NOW(), -{seconds})
    ORDER BY TIME ASC
    ;'''

    columns = [  "Time", "Memory"]
    data = utils.database_connection(query)

    return pd.DataFrame(data, columns=columns)