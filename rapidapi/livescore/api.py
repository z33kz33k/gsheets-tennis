"""

    rapidapi.livescore.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI LiveScore API handling.

    @author: z33k

"""
from typing import List, Optional

from utils import get_apikey, RequestParamsEndpoint


class LiveScoreEndpoint(RequestParamsEndpoint):
    """LiveScore API endpoint.
    """
    HOST = "livescore6.p.rapidapi.com"
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
    LiveScoreEndpoint("list", "Category", folder="leagues/v2"),
    LiveScoreEndpoint("list-live", "Category", folder="matches/v2"),
    LiveScoreEndpoint("list-by-date", "Category", "Date", folder="matches/v2"),
    # 'Ccd' - e.g. 'wimbledon', 'Scd' - e.g. 'group-b'
    LiveScoreEndpoint("list-by-league", "Category", "Ccd", optparams=["Scd"], folder="matches/v2"),
    # LiveTable - false/true
    LiveScoreEndpoint("detail", "Eid", "Category", optparams=["LiveTable"], folder="matches/v2"),
]
