import jwt
import requests
from rownd_django.auth import jwks_client
from rownd_django.settings import rownd_settings
from rownd_django.auth.cache import RowndCache

rownd_cache = RowndCache()

class RowndAppConfig():
    def __init__(self):
        pass

    @property
    def config(self):
        return rownd_cache.fetch('rownd:app_config', self.fetch_app_config, 900) # 15 minutes

    def fetch_app_config(self):
        r = requests.get(f"{rownd_settings.API_URL}/hub/app-config", headers={
            'x-rownd-app-key': rownd_settings.APP_KEY,
        })

        if r.status_code != 200:
            raise Exception(f"Failed to fetch app config: {r.json()}")

        return r.json()

__app_config = RowndAppConfig()

def validate_jwt(token: str, audience: list[str]=[]):
    if __app_config.config is None:
        raise Exception("Rownd app config not loaded")

    jwks_client = fetch_jwks()
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    default_audience = f'app:{__app_config.config["app"]["id"]}'
    audience.append(default_audience)

    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            audience=audience
        )
    except jwt.exceptions.InvalidAudienceError:
        raise jwt.exceptions.InvalidAudienceError(f"Invalid audience. Expected {audience}")

    except Exception as e:
        raise e

def fetch_jwks() -> jwks_client.PyJWKClient:
    url = f"{rownd_settings.API_URL}/hub/auth/keys"
    return jwks_client.PyJWKClient(url)

def fetch_user(user_id: str):
    r = requests.get(f'{rownd_settings.API_URL}/applications/{__app_config.config["app"]["id"]}/users/{user_id}/data', headers={
        "x-rownd-app-key": rownd_settings.APP_KEY,
        "x-rownd-app-secret": rownd_settings.APP_SECRET,
    })

    if r.status_code != 200:
        raise Exception(f"Failed to fetch user: {r.json()}")

    return r.json()

if __name__ == "__main__":
    rownd_settings.APP_KEY = "<key>"
    rownd_settings.APP_SECRET = "<secret>"
    token = "<token>"
    token_info = validate_jwt(token)
    print(token_info)
    user_info = fetch_user(token_info["https://auth.rownd.io/app_user_id"])
    print(user_info)
    print("Success!")
