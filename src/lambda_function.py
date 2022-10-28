#######################################################################################
# LAMBDA Adpater API b2b
# DESCRIPCION : Esta lambda entrega informacion obtenida desde el b2b de clientes y descuentos. 
# AUTOR : lpavez@koandina.com - Icalderon@koandina.com - jcastellanos@koandina.com
# CAMBIOS :version 1.1
# VER. FECHA AUTOR COMENTARIOS
# -------------------------------------------------------------------------------------
# 1.0 2022/02/06 Leonardo Pavez Version Inicial
# 1.1 2022/03/06 Isaias Caldero y Jesus castellano segunda Version 
# -------------------------------------------------------------------------------------
#######################################################################################
import uuid
import logging
import json
import requests
import random
import os
import boto3
import base64
from botocore.exceptions import ClientError



# api-endpoint
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Definicion de constante globales para Token
URL_TOKEN = os.getenv('URL_TOKEN')
URL_SERVICE = os.getenv('URL_SERVICE')
URL_SERVICE_CLIENT = os.getenv('URL_SERVICE_CLIENT')


def getSecret():
    try:
        client = boto3.client('secretsmanager', region_name="us-east-1")
        response = client.get_secret_value(
            SecretId='adpaterB2b'
        )
        return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(e)
        raise e

# Function GetToken Client
def get_token_client():
    client = boto3.client("cognito-idp", region_name="us-east-1")
    m = getSecret()
    response = client.initiate_auth(
        ClientId=m['clientId'],
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": m['username'], "PASSWORD": m['password']},
        ClientMetadata={'UserPoolId': m['poolId']}
    )
    print('response. ', response)

    # From the JSON response you are accessing the AccessToken
    print('token api client', response['AuthenticationResult']['IdToken'])

    responseToken = response['AuthenticationResult']['IdToken']

    return responseToken


# Function GetToken
def get_token():
    try:
        m = getSecret()
        AUTH = m['Authorization']
        urlToken = URL_TOKEN
        payload = {}
        headersToken = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': AUTH,
            'Cookie': 'XSRF-TOKEN=' + str(uuid.uuid4())
        }
        r = requests.request(
            "POST", urlToken, headers=headersToken, data=payload)
        print('token', r.json()['access_token'])
        return r.json()['access_token']
    except ClientError as e:
        logging.error(e)
        raise e

# Funtion Get Client api public B2b
def lambda_handler_get_id_client(datos):
    tokenService = get_token_client()

    params = {
        "cpgId": (datos['cpgId']),
        "countryId": (datos['countryId']),
        "erpClientId": (datos['erpClientId']),
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + tokenService,
        "X-B2B-Transaction-Id": str(uuid.uuid4()),
        "X-B2B-Organization-Id": (datos['X-B2B-Organization-Id'])
    }

    url_client = URL_SERVICE_CLIENT + 'cpg/' + \
        datos['cpgId']+'/country/'+datos['countryId']+'/clients'

    response = requests.request(
        "GET", url_client, params=params, headers=headers)

    print('***Respuestaaaaa client****', response.json()['data']['clientId'])
    return response.json()['data']['clientId']

# Funtion Principal
def lambda_handler(event, context):
    x = get_token_client()
    clientId = str(lambda_handler_get_id_client(event))
    lambdaname = (event['lambdaname'])
    logger.info('*************** Funcion **********')

    if lambdaname == "getdiscounts":
        logger.info('getdiscounts')
        return lambda_handler_get_discounts(event, clientId,  context)
    elif lambdaname == "updatediscounts":
        logger.info('updatediscounts')
        return lambda_handler_update_discounts(event, clientId,  context)
    else:
        return("Debe ingresar nombre Lambda valido")

# Function Get discount
def lambda_handler_get_discounts(event, clientId, context):
    params = {
        "cpgId": event['cpgId'],
        "countryId": event['countryId'],
        "erpClientId": event['erpClientId'],
        "clientId": clientId,
        "X-B2B-Transaction-Id":  uuid.uuid4(),
        "X-B2B-Organization-Id": event['X-B2B-Organization-Id'],
    }
    logger.info(event['X-B2B-Organization-Id'])
    logger.info('****************Token search **********')
    tokenService = get_token()
    logger.info('******************End search **********')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + tokenService + "'"
    }
    print('URL_SERVICE------------>', URL_SERVICE)
    print('evento------------>', event)
    urlService = URL_SERVICE + "cpg/" + event['cpgId'] + "/country/"+event['countryId']+"/clients/" +  clientId + "/discounts/discretionary" 
    response = requests.request(
        "GET", urlService, params=params, headers=headers)
    data = {}
    try:
        logger.info(response.text)
        data = response.json()
    except json.decoder.JSONDecodeError as e:
        if not e.args[0].startswith("Expecting ',' delimiter:"):
            data = {"httpStatus": response.code,
                    "ok": "false",
                    "code": "50",
                    "errorType": "JSON invalid",
                    "message": "JSON reply Error",
                    "data": ""
                    }
            raise
    logger.info(data)
    return data

# Function Update discount
def lambda_handler_update_discounts(event, clientId, context):
    disc = json.dumps({'clientDiscounts': event['clientDiscounts']})
    print('clientDiscount------------------->', disc)
    payload = disc
    params = {
        "cpgId": event['cpgId'],
        "countryId": event['countryId'],
        "erpClientId": event['erpClientId'],
        "clientId": clientId,
        "X-B2B-Transaction-Id":  uuid.uuid4(),
        "X-B2B-Organization-Id": event['X-B2B-Organization-Id'],
    }
    tokenService = get_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + tokenService + "'"
    }
    urlService = URL_SERVICE + "cpg/" + event['cpgId'] + "/country/"+event['countryId']+"/clients/" + clientId + "/updateClientDiscount"
    response = requests.request("POST", urlService, headers=headers, data=payload, params=params)
    data = {}
    try:
        logger.info(response.text)
        data = response.json()
    except json.decoder.JSONDecodeError as e:
        if not e.args[0].startswith("Expecting ',' delimiter:"):
            data = {"httpStatus": response.code,
                    "ok": "false",
                    "code": "50",
                    "errorType": "JSON invalid",
                    "message": "JSON reply Error",
                    "data": ""
                    }
            raise
  
    return data
