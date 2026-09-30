import requests
from django.conf import settings
from django.core.cache import cache
import uuid


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
        uuid_key = str(uuid.uuid4())

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

        user_access_token = res.get("access_token")
        user_page_data = requests.get(
            "https://graph.facebook.com/v26.0/me/accounts",
            params={
                "fields": "id,name,page_token,picture,access_token",
                "access_token": user_access_token,
            },
        ).json()

        error = user_page_data.get("error", "")
        if error:
            return {"message": error["message"], "status": False}

        page_list = user_page_data.get("data")

        updated_page_list = []

        for page in page_list:
            temp_page = page.copy()
            temp_page["user_access_token"] = user_access_token
            updated_page_list.append(temp_page)

        cache.set(
            f"user_page_list:{uuid_key}",
            {"pages": updated_page_list, "channel": "facebook"},
            timeout=3000,
        )

        list_to_return = []

        for page in page_list:
            page.pop("access_token")
            list_to_return.append(page)

        has_pages = len(list_to_return) > 0

        return {
            "data": list_to_return if has_pages else None,
            "required_page_selection": has_pages,
            "uuid": uuid_key,
            "status": True,
        }

    def get_page_data(self, pages):
        result = []

        for page in pages:
            data = {
                "channel_config": {
                    "user_access_token": page.get("user_access_token"),
                    "page_access_token": page.get("access_token"),
                },
                "channel_data": {
                    "name": page.get("name"),
                    "account_id": page.get("id"),
                    "profile_picture": page.get("picture")["data"]["url"],
                },
            }
            result.append(data)

        return result

    def invalidate_token(self, account_id, config):
        return {}

    def test_page(self, account_id, config):
        access_token = config.get("page_access_token")
        page_data = requests.get(
            f"https://graph.facebook.com/v24.0/{account_id}/page_status/",
            params={
                "access_token": access_token,
            },
        ).json()

        return bool(
            not page_data.get("error")
            and page_data.get("id")
            and page_data.get("status") == "ok"
        )
