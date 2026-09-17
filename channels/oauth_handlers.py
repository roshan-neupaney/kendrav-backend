import requests
from django.conf import settings
from datetime import datetime, timedelta, timezone


def oauth_handler(slug_url):
    handlers = {"facebook": FacebookHandler}
    return handlers.get(slug_url)()


class FacebookHandler:
    redirect_uri = f"{settings.FRONTEND_BASE_URL}/channel/callback/facebook"

    def exchange_code_for_token(self, code):
        res = requests.get(
            "https://graph.facebook.com/v26.0/oauth/access_token",
            params={
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": self.redirect_uri,
                "code": code,
            },
        ).json()
        access_token = res.get("access_token", "")
        if access_token:
            return {"access_token": access_token, "status": True}

        error = res.get("error", "")
        if error:
            return {"message": error["message"], "status": False}

    def exchange_token(self, code):
        token_result = self.exchange_code_for_token(code=code)

        if not token_result.get("status"):
            return token_result

        token = token_result.get("access_token", "")
        res = requests.get(
            "https://graph.facebook.com/v26.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": self.redirect_uri,
                "fb_exchange_token": token,
            },
        ).json()
        error = res.get("error", "")
        if error:
            return {"message": error["message"], "status": False}

        user_data = requests.get(
            "https://graph.facebook.com/v26.0/me",
            params={
                "fields": "id,name,picture",
                "access_token": res.get("access_token"),
            },
        ).json()

        error = user_data.get("error", "")
        if error:
            return {"message": error["message"], "status": False}

        profile_picture = user_data.get("picture")["data"]["url"]

        expires_in = res.get("expires_in")
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        else:
            expires_at = None

        return {
            "access_token": res.get("access_token"),
            "expires_at": expires_at,
            "full_name": user_data.get("name", ""),
            "account_id": user_data.get("id", ""),
            "profile_picture": profile_picture,
            "status": True,
        }

    def invalidate_token(self, account_id, access_token):
        requests.delete(
            f"https://graph.facebook.com/v26.0/{account_id}/permissions",
            params={"access_token": access_token},
        )

    def test_user_data(self, access_token):
        user_data = requests.get(
            "https://graph.facebook.com/v26.0/me",
            params={
                "fields": "id,name",
                "access_token": access_token,
            },
        ).json()
        
        return bool(not user_data.get('error') and user_data.get('id'))
