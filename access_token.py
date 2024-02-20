import json
import requests
import os

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

tenant_id = os.environ["tenant_id"]
api_url = os.environ["api_url"]
client_id = os.environ["client_id"]
client_secret = os.environ["client_secret"]

async def get_access_token():
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"

    token_params = {
        'grant_type': 'client_credentials',
        'client_id':client_id,
        'client_secret': client_secret,
        'resource': api_url
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=token_params, headers=headers)
    response.raise_for_status()

    return response.json().get('access_token')

