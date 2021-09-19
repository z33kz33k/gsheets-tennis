"""

    rapidapi.tennis_data.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI Tennis Data API handling.

    @author: z33k

"""
from typing import List, Optional

from utils import get_apikey, RequestParamsEndpoint, UrlParamsEndpoint


class TennisDataEndpoint(RequestParamsEndpoint):
    """Tennis Data API endpoint.
    """
    HOST = "tennis-data1.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0][:-1]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)


class TennisDataUrlEndpoint(UrlParamsEndpoint):
    """Tennis Data API URL-type endpoint.
    """
    HOST = "tennis-data1.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0][:-1]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)


# endpoints without potential and those checked to be useless are filtered out
ENDPOINTS = [
    TennisDataEndpoint("players", optparams=["page", "id"], folder="tennis"),
    TennisDataEndpoint("tournaments", optparams=["minPrize", "year", "page", "type"],
                       folder="tennis"),
    TennisDataUrlEndpoint("tournament", "id", folder="tennis"),
    TennisDataEndpoint("matches", optparams=["player_id", "tournament", "surface", "page"],
                       folder="tennis"),
]