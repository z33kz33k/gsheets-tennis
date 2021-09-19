"""

    rapidapi.sportscore.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI SportScore API handling.

    @author: z33k

"""
from typing import List, Optional

from utils import get_apikey, MainParamEndpoint, UrlParamsEndpoint


class SportScoreEndpoint(MainParamEndpoint):
    """SportScore API endpoint.
    """
    HOST = "sportscore1.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0][:-1]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, mainparam: str, *params: str,
                 optparams: Optional[List[str]] = None, folder: Optional[str] = None,
                 optparams_in_url=True) -> None:
        super().__init__(endpoint, mainparam, *params, optparams=optparams, folder=folder,
                         optparams_in_url=optparams_in_url)


class SimpleSportScoreEndpoint(UrlParamsEndpoint):
    """Simple SportScore API endpoint.
    """
    HOST = "sportscore1.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0][:-1]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None, optparams_in_url=True) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder,
                         optparams_in_url=optparams_in_url)


# endpoints without potential and those checked to be useless are filtered out
ENDPOINTS = [
    SimpleSportScoreEndpoint("sports"),
    SportScoreEndpoint("seasons", "id", optparams=["page"], folder="sports"),
    SportScoreEndpoint("leagues", "id", optparams=["page"], folder="sports"),
    SimpleSportScoreEndpoint("sports", "id"),
    # TODO (doesn't work as the url it need has the form of:
    #  url = "https://sportscore1.p.rapidapi.com/sports/1/events/date/2020-06-07"
    #  and not the coded:
    #  url = "https://sportscore1.p.rapidapi.com/sports/1/events/2020-06-07")
    SportScoreEndpoint("events", "id", "date", optparams=["page"], folder="sports"),
]
