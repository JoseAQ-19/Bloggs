import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

def notify_google(url):
    credentials_json = os.environ.get('GOOGLE_INDEXING_JSON')
    if not credentials_json:
        print("⚠️ GOOGLE_INDEXING_JSON no configurado. Saltando indexación rápida (Fast-Track).")
        return
        
    try:
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/indexing"]
        )
        
        # Get Auth token
        request = Request()
        credentials.refresh(request)
        access_token = credentials.token
        
        endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "url": url,
            "type": "URL_UPDATED"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"⚡ [Fast-Track SEO] Ping exitoso a Google para la URL: {url}")
        else:
            print(f"⚠️ [Fast-Track SEO] Error al notificar a Google. Status: {response.status_code}, Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"⚠️ [Fast-Track SEO] Excepción al invocar Google Indexing API: {str(e)}")
