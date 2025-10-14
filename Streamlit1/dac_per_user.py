import json
import requests
import dsp_token
import logging
from json.decoder import JSONDecodeError
from hdbcli import dbapi  # To connect to SAP HANA Database underneath SAP Datasphere to fetch metadata
import utils
import pandas as pd # To write the result into a dataframe
import datetime
with open('config_files/windhoff.json', 'r') as f:
    config = json.load(f)

secrets_file = config["SETTINGS"]["secrets_file"]
token_file = config["SETTINGS"]["token_file"]
dsp_host = config["DATASPHERE"]["dsp_host"]
dsp_space = config["DATASPHERE"]["dsp_space"]
hdb_address = config["HDB"]["hdb_address"]
hdb_port = config["HDB"]["hdb_port"]
hdb_user = config["HDB"]["hdb_user"]
hdb_password = config["HDB"]["hdb_password"]
excel_file = 'authoriazions.xlsx'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("session")


def initializeOAuthSession():
    token = ''
    # Get token if available
    f = open(token_file)
    logger.info(f'Path of token file: {token_file}')

    try:
        token = json.load(f)
    except JSONDecodeError:
        pass

    if token == '':
        # Get Code
        token = dsp_token.get_initial_token(secrets_file, token_file)
    else:
        # Refresh existing token
        token = dsp_token.refresh_token(secrets_file, token_file)

    logger.info(f'Token: {token}')

    # For Post, content-type must be provided
    header = {'authorization': "Bearer " + token,
              "accept": "application/vnd.sap.datasphere.object.content+json"}

    logger.info(f'Header: {header}')
    return header


def get_db_connection():
    connection = dbapi.connect(
        address=hdb_address,
        port=int(hdb_port),
        user=hdb_user,
        password=hdb_password
    )
    return connection


def get_authorization_objects(table, userIdentifier, authorization_column):
    connection = get_db_connection()
    cursor = connection.cursor()

    st = f'''
        SELECT *
        FROM "{dsp_space}"."{table}" 
        WHERE "{authorization_column}" = '{userIdentifier}';
    '''
    logger.info(f'SQL Statement: {st}')
    cursor.execute(st)
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_csn_definition(dac_source_table):
    connection = get_db_connection()
    cursor = connection.cursor()
    st = f'''
         SELECT A.CSN
         FROM "{dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$" A
         INNER JOIN (
           SELECT ARTIFACT_NAME, MAX(ARTIFACT_VERSION) AS MAX_ARTIFACT_VERSION
           FROM "{dsp_space}$TEC"."$$DEPLOY_ARTIFACTS$$"
           WHERE SCHEMA_NAME = '{dsp_space}' AND ARTIFACT_NAME = '{dac_source_table}'
           GROUP BY ARTIFACT_NAME

         ) B
         ON A.ARTIFACT_NAME = B.ARTIFACT_NAME
         AND A.ARTIFACT_VERSION = B.MAX_ARTIFACT_VERSION;
     '''
    logger.info(f'SQL Statement: {st}')
    cursor.execute(st)
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_dataAccessControls(spaceID, userIdentifier):

    list_of_columns = []
    dac_fields = []
    data = {}
    authorization_json = {"authorizations": []}

    # Initialize OAuth session
    header = utils.initializeGetOAuthSession(token_file, secrets_file)
    url = utils.get_url(dsp_host ,'list_of_dacs').format(**{"spaceID": spaceID})
    response = requests.get(url, headers=header)
    list_of_dacs = response.json()
    logger.info(f'List of Data Access Controls: {list_of_dacs}')
    for dac in list_of_dacs:

        technical_name = dac['technicalName']
        # Get technical URL and response from Data Access Control
        url = utils.get_url(dsp_host, 'dac_technical_name').format(**{"spaceID": spaceID}, **{"technicalName": technical_name})
        logger.info(f'Technical URL of DAC: {url}')
        response = requests.get(url, headers=header)
        dac_definitions = response.json()

        for dac_definition in dac_definitions['definitions']:

            # Check if Data Access Controls is Operator
            try:
                dac_operator = \
                dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                    'restrictionElements']
            except KeyError:
                dac_operator = None

            if dac_operator is not None:
                dac_fields.append(
                    dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                        'restrictionElements']['restriction']['='])
                dac_fields.append(
                    dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                        'restrictionElements']['name']['='])
                dac_fields.append(
                    dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                        'restrictionElements']['option']['='])
                dac_fields.append(dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                    'restrictionElements']['low']['='])
                dac_fields.append(dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                    'restrictionElements']['high']['='])
                data['type'] = 'OPERATOR'
            else:
                data['type'] = 'LIST'

            # Store technical name in JSON object
            data['technicalName'] = dac['technicalName']

            # Store description in JSON Object
            data['description'] = dac_definitions['definitions'][dac_definition]['@EndUserText.label']
            authorization_column = dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition'][
                'principalElement']

            # Store authorization column in JSON Object
            data['authorization'] = {authorization_column: []}
            data['columns'] = []

            # Get columns of Data Access Control

            # Data Access Control is from type Operator
            if dac_operator is not None:
                data['columns'] = {columns: [] for columns in dac_fields}
            elif dac_operator is None:
                data['columns'] = {columns: [] for columns in dac_definitions['definitions'][dac_definition]['elements']}

            # Get technical Name of DAC source table
            dac_source_table = dac_definitions['definitions'][dac_definition]['@DataWarehouse.dataAccessControl.definition']['sourceEntity']

            csn_definition = get_csn_definition(dac_source_table)
            csn_string = ''
            for csn in csn_definition:
                csn_string = csn[0]
            csn_json = json.loads(csn_string)
            elements = csn_json["definitions"][dac_source_table]["elements"]

            # get order of columns
            order = 0
            for element in elements:
                list_of_columns.append((element, order))
                order = order + 1

            # Get Data Access Control Entries
            dac_entries = get_authorization_objects(dac_source_table, userIdentifier, authorization_column)

            # DAC with OPERATOR
            if dac_operator != None:
                position_of_column = 0
                for columns in list_of_columns:

                    # Compare Column with entry in JSON under 'authorization'
                    for entry in dac_entries:

                        if position_of_column == len(data['columns']):
                            # Reset Position
                            position_of_column = 0

                        if columns[0] == list(data['authorization'].keys())[0]:
                            data['authorization'][columns[0]].append(entry[columns[1]])
                        elif columns[0] == list(data['columns'])[position_of_column]:
                            position_of_column += 1
                            if entry[columns[1]] is None:
                                data['columns'][columns[0]].append('')
                            else:
                                data['columns'][columns[0]].append(entry[columns[1]])

            else:
                # Logic to add all user identifier and authorization values
                for columns in list_of_columns:
                    # Compare Column with entry in JSON under 'authorization'
                    for entry in dac_entries:
                        if columns[0] == list(data['authorization'].keys())[0]:
                            # Build JSON
                            # Authorization Column = [ VALUE ]
                            # JSON['authorization']['Column_1'] = VALUE
                            data['authorization'][columns[0]].append(entry[columns[1]])
                        elif columns[0] == list(data['columns'])[0]:
                            data['columns'][columns[0]].append(entry[columns[1]])
            list_of_columns = []
        if data != {}:
            authorization_json["authorizations"].append(data)
        data = {}
    authorizations = json.dumps(authorization_json)
    return authorizations


def create_excel(authorizations):
    print(f'Start create Excel: {datetime.datetime.now().time()}')
    authorization_temp = []
    authorization_temp_operator = []
    useridentifier = []
    authValues = []
    listOfValues = []
    auth_json = json.loads(authorizations)
    print(auth_json)
    type = ''
    for authorization in auth_json['authorizations']:
        type = authorization['type']
        technicalname = authorization['technicalName']
        description = authorization['description']

        for authColumn in authorization['authorization']:
            useridentifier = authorization['authorization'][authColumn]

        for valueColumn in authorization['columns']:
            if type == 'LIST':
                authValues = authorization['columns'][valueColumn]
            elif type == 'OPERATOR':
                listOfValues.append(authorization['columns'][valueColumn])

        if type == 'LIST':
            for user in useridentifier:
                for auth in authValues:
                    authorization_temp.append((technicalname, description, user, auth))

        elif type == 'OPERATOR':
            for user in useridentifier:
                authorization_temp_operator.append((technicalname,description,user, listOfValues[0][0],listOfValues[1][0],listOfValues[2][0], listOfValues[3][0], listOfValues[4][0]))

        listOfValues.clear()
        authValues.clear()

    authorization_excel = list(dict.fromkeys(authorization_temp))


    df1 = pd.DataFrame(authorization_excel,
                      columns=['Technical Name', 'Description', 'User Identifier', 'Authorization Values'])
    df2 = pd.DataFrame(authorization_temp_operator,
                       columns=['Technical Name', 'Description', 'User Identifier', 'Restriction', 'Operator', 'Low Value', 'High Value',
                                ''])

    with pd.ExcelWriter(excel_file) as writer:  # doctest: +SKIP
        df1.to_excel(writer, sheet_name='Authorizations', index=False)
        df2.to_excel(writer, sheet_name='Operator Authorizations', index=False)

    # Format Excel
    utils.format_excel(excel_file)
    print(f'End create Excel: {datetime.datetime.now().time()}')


authorizations = get_dataAccessControls('TM', 't.meyer@windhoff-group.de')
create_excel(authorizations)