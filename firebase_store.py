import os
import time
from pathlib import Path
import json

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DB_URL = os.environ["FIREBASE_DB_URL"].strip().rstrip("/")
API_KEY = os.environ["FIREBASE_API_KEY"].strip()
EMAIL = os.environ["FIREBASE_EMAIL"].strip()
PASSWORD = os.environ["FIREBASE_PASSWORD"].strip()

_token = {"value": None, "expires": 0}


def _get_token():
    if time.time() < _token["expires"]:
        return _token["value"]

    r = requests.post(
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
        params={"key": API_KEY},
        json={
            "email": EMAIL,
            "password": PASSWORD,
            "returnSecureToken": True,
        },
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    _token["value"] = data["idToken"]
    _token["expires"] = time.time() + int(data["expiresIn"]) - 60
    return _token["value"]


def get(path):
    r = requests.get(
        f"{DB_URL}/{path}.json",
        params={"auth": _get_token()},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def put(path, data):
    r = requests.put(
        f"{DB_URL}/{path}.json",
        params={"auth": _get_token()},
        data=json.dumps(data),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()