import sys
import logging
import requests
import urllib3
import base64
from google.cloud import storage


logger = logging.getLogger(__name__)


def _create_auth_headers(username, password):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    headers.update(urllib3.util.make_headers(basic_auth=f"{username}:{password}"))
    return headers


def _verify_boomi_licensing(username, password, account):
    _headers = _create_auth_headers(username, password)
    API_URL = f"https://api.boomi.com/api/rest/v1/{account}/Account/{account}"
    resp = requests.get(API_URL, headers=_headers)
    resp.raise_for_status()
    
def _generate_install_token(username, password, account_id, token_type, timeout):
    REQ_TOKEN_TYPES = ["ATOM"]
    if token_type.upper() not in REQ_TOKEN_TYPES:
        raise Exception(f"Parameter TokenType must be one of: {str(REQ_TOKEN_TYPES)}")

    _headers = _create_auth_headers(username, password)
    API_URL = f"https://api.boomi.com/api/rest/v1/{account_id}/InstallerToken/"
    payload = {"installType": token_type, "durationMinutes": int(timeout)}
    logger.info(payload)
    resp = requests.post(API_URL, headers=_headers, json=payload)
    resp.raise_for_status()
    rj = resp.json()

    return rj["token"]


def auth_and_licensing_logic(username, password, account_id, token_type, token_timeout):
    # Verify licensing    
    _verify_boomi_licensing(username, password, account_id)
    if username.startswith("BOOMI_TOKEN."):
        # Generate install token
        token = _generate_install_token(
            username, password, account_id, token_type, token_timeout
        )
        return token


def handler(request):
    STATUS = "SUCCESS"
    atom_token = None
    try:
        request_json = request.get_json()
        BoomiUsername = request_json['BoomiUsername']
        BoomiAuthenticationType= request_json['boomiAuthenticationType']
        BoomiPassword= request_json['BoomiPassword']
        BoomiAccountID=request_json['BoomiAccountID']
        TokenType= request_json['TokenType']
        TokenTimeout= request_json['TokenTimeout']
        bucketname= request_json['bucketname']
        BoomiAuthenticationType = BoomiAuthenticationType.strip()
        if BoomiAuthenticationType.upper() =="TOKEN":
         atom_token = auth_and_licensing_logic("BOOMI_TOKEN."+BoomiUsername, BoomiPassword, BoomiAccountID, TokenType.upper(), TokenTimeout)
         client = storage.Client()
         bucket = client.get_bucket(bucketname)
         blob = bucket.blob('token.txt')         
         blob.upload_from_string(base64.b64encode(atom_token.encode('utf-8')))
        else:
         atom_token = auth_and_licensing_logic(BoomiUsername, BoomiPassword, BoomiAccountID, TokenType.upper(), TokenTimeout)        
         client = storage.Client()
         bucket = client.get_bucket(bucketname)
         blob = bucket.blob('token.txt')
         blob.upload_from_string(base64.b64encode(BoomiPassword.encode('utf-8')))
    except requests.exceptions.RequestException as err:
        logging.error(err)
        STATUS = "FAILED"
    except Exception as err:
        logging.error(err)
        STATUS = "FAILED"
    finally:
        print("status:{},token:{}".format(STATUS,atom_token))
