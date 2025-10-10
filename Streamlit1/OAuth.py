import dsp_token

def initializeGetOAuthSession(token_file, secrets_file):
    token = ''
    expire = datetime(1970, 1, 1)
    # Get token if available
    f = open(token_file)
    logger.info(f'Path of token file: {token_file}')

    try:
        token = json.load(f)
        expire = datetime.strptime(token['expire'], "%Y-%m-%d %H:%M:%S")
    except JSONDecodeError:
        pass

    if token == '':
        # Get Code
        dsp_token.get_initial_token(secrets_file, token_file)

    else:

        if expire + timedelta(days=30) <= datetime.now():
            token = ''

        # If expire date time is lower than current time
        if expire <= datetime.now() and token == '':
            # Get Code
            dsp_token.get_initial_token(secrets_file, token_file)

        # Refresh existing token
        token = dsp_token.refresh_token(secrets_file, token_file)



    logger.info(f'Token: {token}')

    header = {'authorization': "Bearer " + token,
              "accept": "application/vnd.sap.datasphere.object.content+json"}
    logger.info(f'Header: {header}')
    return header