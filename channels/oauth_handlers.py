import requests
from django.conf import settings

def oauth_handler(slug_url):
    handlers = {
        'facebook': FacebookHandler
    }
    return handlers.get(slug_url)()

class FacebookHandler:
    def exchange_code_for_token(self, code, redirect_uri):
        res = requests.get(
           "https://graph.facebook.com/v26.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        ).json()
        access_token = res.get('access_token')
        return access_token

    def exchange_token(self, code, redirect_uri):
        token = self.exchange_code_for_token(code=code, redirect_uri=redirect_uri)
        res = requests.get(
            "https://graph.facebook.com/v26.0/oauth/access_token",
            params={
                'grant_type': 'fb_exchange_token',
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": redirect_uri,
                "fb_exchange_token": token,
            },
        )
    
        return res.json()


