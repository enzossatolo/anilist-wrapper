from __future__ import annotations

import json
import urllib.parse
from typing import Optional
import httpx

from .exceptions import AuthenticationError


class AniListAuth:
    """OAuth2 authentication helper for AniList."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: Optional[str] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def get_authorization_url(self) -> str:
        """Get the URL to redirect the user to for authorization."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
        }
        if self.redirect_uri:
            params["redirect_uri"] = self.redirect_uri

        return f"https://anilist.co/api/v2/oauth/authorize?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> str:
        """Exchange the authorization code for an access token."""
        url = "https://anilist.co/api/v2/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri

        try:
            response = httpx.post(url, json=data)
            response.raise_for_status()
            res_data = response.json()

            self.access_token = res_data.get("access_token")
            self.refresh_token = res_data.get("refresh_token")

            if not self.access_token:
                raise AuthenticationError("No access token found in response.")
            return self.access_token
        except Exception as e:
            raise AuthenticationError(f"Failed to exchange code: {e}") from e

    def load_token(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Manually load access and optional refresh tokens."""
        self.access_token = access_token
        self.refresh_token = refresh_token

    def save(self, filepath: str) -> None:
        """Save tokens to a JSON file."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, client_id: str, client_secret: str, filepath: str) -> AniListAuth:
        """Load tokens from a JSON file and return an AniListAuth instance."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        auth = cls(client_id=client_id, client_secret=client_secret)
        auth.load_token(
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token")
        )
        return auth
