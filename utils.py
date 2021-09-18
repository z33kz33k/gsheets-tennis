"""

    api.py
    ~~~~~~~~~
    Utility functions.

    @author: z33k

"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

Json = Dict[str, Any]
API_CREDS_FILE = Path("api_creds.json")


class InsufficientDataError(ValueError):
    """Raised when data pulled is insufficient (from a variety of reasons).
    """


def get_apikey(provider: str, api: str) -> Json:
    data = json.loads(API_CREDS_FILE.read_text())
    provider = data.get(provider)
    if not provider:
        raise ValueError(f"Invalid provider: {provider}.")
    apikey = provider.get(api)
    if not apikey:
        raise ValueError(f"Invalid API: {api}.")
    return apikey


def endpoint_retrieve(endpoint_url: str, headersmap: Dict[str, str], paramsmap: Dict[str, str],
                      dumpdest: Optional[Path] = None) -> Union[Json, List[Json]]:
    response = requests.request("GET", endpoint_url, headers=headersmap, params=paramsmap)
    data = json.loads(response.text)

    if dumpdest is not None:
        with dumpdest.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    return data




