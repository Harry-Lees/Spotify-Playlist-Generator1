import json
import requests
from urllib.parse import quote


class SpotifyClient:
    # Spotify API URLS
    API_VERSION = "v1"
    SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_BASE_URL = "https://api.spotify.com"
    SPOTIFY_API_URL = f"{SPOTIFY_API_BASE_URL}/{API_VERSION}"

    # Server-side Parameters
    SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private user-read-recently-played"
    STATE = ""
    SHOW_DIALOG_bool = True
    SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

    def __init__(self, client_id, client_secret, client_side_url='http://127.0.0.1', port=None):
        self.port = port
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_side_url = client_side_url
        self.redirect_uri = f"{self.client_side_url}/callback/q" if port is None else f"{self.client_side_url}:{self.port}/callback/q"
        self._access_token = ''
        self._authorization_header = ''

    def get_auth_url(self):
        auth_query_parameters = {
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.SCOPE,
            # "state": STATE,
            # "show_dialog": SHOW_DIALOG_str,
            "client_id": self.client_id
        }
        url_args = "&".join([f"{key}={quote(val)}" for key, val in auth_query_parameters.items()])
        return f"{self.SPOTIFY_AUTH_URL}/?{url_args}"

    def get_authorization(self, auth_token):
        """
        returning authorization data and setting the authorization_header
        :param auth_token:
        :return: dict
        """
        data = {
            "grant_type": "authorization_code",
            "code": str(auth_token),
            "redirect_uri": self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        post_request = requests.post(self.SPOTIFY_TOKEN_URL, data=data)
        response_data = json.loads(post_request.text)
        self._access_token = response_data["access_token"]
        self._authorization_header = {"Authorization": f"Bearer {self._access_token}"}

        return dict(
            access_token=response_data["access_token"],
            refresh_token=response_data["refresh_token"],
            token_type=response_data["token_type"],
            expires_in=response_data["expires_in"],
        )

    @staticmethod
    def get_data(endpint_url, authorization_header):
        """
        returning data from an endpoint with a get request
        """
        return json.loads(requests.get(endpint_url, headers=authorization_header).text)
