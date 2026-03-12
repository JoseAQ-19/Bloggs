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
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"⚡ [Fast-Track SEO] Ping exitoso a Google para la URL: {url}")
        else:
            print(f"⚠️ [Fast-Track SEO] Error al notificar a Google. Status: {response.status_code}, Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"⚠️ [Fast-Track SEO] Excepción al invocar Google Indexing API: {str(e)}")

    # Capa 1: Protocolo IndexNow (Bing/Yandex)
    notify_indexnow(url)

    # Capa 2: Ping Automático al Sitemap de Google
    ping_sitemap()


def notify_indexnow(url):
    """
    Notifica a Bing/Yandex (y otros buscadores que soportan IndexNow)
    sobre la publicación o actualización de una URL.
    """
    indexnow_key = os.environ.get('INDEXNOW_KEY')
    if not indexnow_key:
        print("⚠️ INDEXNOW_KEY no configurado. Saltando indexación IndexNow.")
        return

    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        endpoint = "https://api.indexnow.org/indexnow"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        payload = {
            "host": host,
            "key": indexnow_key,
            "keyLocation": f"https://{host}/{indexnow_key}.txt",
            "urlList": [url]
        }

        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)

        if response.status_code in [200, 202]:
            print(f"⚡ [IndexNow] Ping exitoso para la URL: {url} (Status: {response.status_code})")
        else:
            print(f"⚠️ [IndexNow] Error al notificar. Status: {response.status_code}, Response: {response.text[:200]}")

    except Exception as e:
        print(f"⚠️ [IndexNow] Excepción al invocar IndexNow API: {str(e)}")


def ping_sitemap():
    """
    Realiza un ping a Google para que vuelva a procesar el sitemap.xml.
    """
    try:
        sitemap_url = "https://novumworld.com/sitemap.xml"
        ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"

        response = requests.get(ping_url, timeout=10)

        if response.status_code == 200:
            print(f"⚡ [Sitemap Ping] Ping exitoso al Sitemap en Google: {sitemap_url}")
        else:
            print(f"⚠️ [Sitemap Ping] Error al hacer ping al Sitemap. Status: {response.status_code}, Response: {response.text[:200]}")

    except Exception as e:
        print(f"⚠️ [Sitemap Ping] Excepción al hacer ping al Sitemap: {str(e)}")
