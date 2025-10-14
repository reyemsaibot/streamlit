import pandas as pd
import json
import utils

def get_objects(object):
    query = f'''
        SELECT *
        FROM "SYS"."OBJECT_DEPENDENCIES"
        WHERE BASE_OBJECT_NAME = '{object}'
        AND DEPENDENT_OBJECT_NAME not like '§%';
    '''
    return utils.database_connection(query)

def get_description(space, list_of_objects):
    query = f'''
        SELECT A.ARTIFACT_NAME, A.CSN, A.ARTIFACT_VERSION
        FROM "{space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
        INNER JOIN (
          SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
          FROM "{space}$TEC"."$$DEPLOY_ARTIFACTS$$"
          WHERE SCHEMA_NAME = '{space}'  AND ARTIFACT_NAME in ({', '.join(f"'{w}'" for w in list_of_objects)})
          GROUP BY ARTIFACT_NAME

        ) B
        ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
        AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
    '''
    return utils.database_connection(query)


def get_object_dependencies(object):
    list_of_dependencies = []
    list_of_objects = get_objects(object)

    # unique list of spaces
    list_of_spaces =  list(dict.fromkeys([t[6] for t in list_of_objects]))

    list_of_objects = list(dict.fromkeys([t[7] for t in list_of_objects]))
    # remove _$TV from objects
    list_of_objects = [x.replace('_$TV', '') for x in list_of_objects]
    print(list_of_objects)

    for space in list_of_spaces:
        csn_files = get_description(space, list_of_objects)

        for csn in csn_files:
            csn = csn[1]
            csn_loaded = json.loads(csn)
            objectName = list(csn_loaded['definitions'].keys())[0]
            label = csn_loaded['definitions'][objectName]['@EndUserText.label']
            list_of_dependencies.append((space,objectName, label))

    df = pd.DataFrame(list_of_dependencies, columns=['Space', 'Dependency', 'Description'])
    return df