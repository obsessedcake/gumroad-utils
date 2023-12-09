import logging
from configparser import RawConfigParser
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from requests import Session as _RequestsSession

if TYPE_CHECKING:
    from pathlib3x import Path

__all__ = ["GumroadSession", "GumroadRedirectError", "create_session", "detect_redirect"]


def _sanitize_cookie_value(value: str) -> str:
    return value.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")


class GumroadSession(_RequestsSession):
    def get_soup(self, url: str, *, short=False) -> BeautifulSoup:
        if short:
            url = "https://app.gumroad.com" + url

        response = self.get(url, allow_redirects=False)
        response.raise_for_status()

        return BeautifulSoup(response.content, "lxml")

    @property
    def logged(self) -> bool:
        return False


class GumroadRedirectError(RuntimeError):
    pass


class DefaultSession(GumroadSession):
    pass


class UserSession(GumroadSession):
    def __init__(self, app_session: str, guid: str, user_agent: str) -> None:
        super().__init__()

        self.cookies.set("_gumroad_app_session", _sanitize_cookie_value(app_session))
        self.cookies.set("_gumroad_guid", guid)
        self.headers["User-Agent"] = user_agent

    @property
    def logged(self) -> bool:
        return True


def _create_default_session() -> GumroadSession:
    logging.getLogger().warning("Failed to create a user session, fallback to a default one!")
    return DefaultSession()


def create_session(path: "Path" | None = None) -> GumroadSession:
    if path and path.exists():
        config = RawConfigParser()
        config.read(path)

        app_session = config["user"]["app_session"]
        guid = config["user"]["guid"]
        user_agent = config["user"]["user_agent"]

        for value in (app_session, guid, user_agent):
            if value == "ChangeMe":
                return _create_default_session()

        return UserSession(app_session=app_session, guid=guid, user_agent=user_agent)

    return _create_default_session()


def detect_redirect(soup: BeautifulSoup) -> None:
    text = soup.find(text=True, recursive=False)
    if text and ("You are being" in text):  # You are being redirected.
        raise GumroadRedirectError("You are being redirected to a login page!")
