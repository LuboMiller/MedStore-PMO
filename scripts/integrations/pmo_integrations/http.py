"""Minimal HTTP helpers shared by clients."""

from __future__ import annotations

import sys
from typing import Any, Optional

import requests
from requests.auth import HTTPBasicAuth


class ApiError(RuntimeError):
    def __init__(self, service: str, status: int, body: str):
        super().__init__(f"{service} HTTP {status}: {body[:400]}")
        self.service = service
        self.status = status


def basic_session(username: str, api_token: str) -> requests.Session:
    s = requests.Session()
    s.auth = HTTPBasicAuth(username, api_token)
    s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    s.trust_env = False
    return s


def bearer_session(token: str, *, trust_env: bool = False) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
    )
    s.trust_env = trust_env
    return s


def raise_for_status(service: str, r: requests.Response) -> None:
    if r.ok:
        return
    raise ApiError(service, r.status_code, r.text)


def get_json(session: requests.Session, url: str, *, service: str, params: Optional[dict] = None) -> Any:
    r = session.get(url, params=params or {})
    raise_for_status(service, r)
    if not r.content:
        return {}
    return r.json()


def post_json(
    session: requests.Session,
    url: str,
    *,
    service: str,
    payload: Optional[dict] = None,
    params: Optional[dict] = None,
) -> Any:
    r = session.post(url, json=payload or {}, params=params or {})
    raise_for_status(service, r)
    if not r.content:
        return {}
    return r.json()


def put_json(
    session: requests.Session,
    url: str,
    *,
    service: str,
    payload: Optional[dict] = None,
    params: Optional[dict] = None,
) -> Any:
    r = session.put(url, json=payload or {}, params=params or {})
    raise_for_status(service, r)
    if not r.content:
        return {}
    return r.json()


def delete(session: requests.Session, url: str, *, service: str) -> None:
    r = session.delete(url)
    raise_for_status(service, r)


def die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    raise SystemExit(code)
