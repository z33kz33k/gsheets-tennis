"""

    rapidapi.tennis_live_data.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI Tennis Live Data API handling.

    @author: z33k

"""
from typing import List, Optional

from utils import get_apikey, UrlParamsEndpoint


class TennisLiveDataEndpoint(UrlParamsEndpoint):
    """Tennis Live Data API endpoint.
    """
    HOST = "tennis-live-data.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)


# endpoints without potential and those checked to be useless are filtered out
ENDPOINTS = [
    TennisLiveDataEndpoint("matches-results-by-player", "tourn_id", "player_id"),
    TennisLiveDataEndpoint("players", "tour"),
    TennisLiveDataEndpoint("matches-by-date", optparams=["date"]),  # today if no date supplied
    TennisLiveDataEndpoint("player", "player_id"),
    TennisLiveDataEndpoint("race", "tour_code", folder="rankings"),
    TennisLiveDataEndpoint("rankings", "tour_code"),
    # returns the same data that is already present in more elaborate 'matches-results' endpoint
    TennisLiveDataEndpoint("match", "match_id"),
    TennisLiveDataEndpoint("matches-results", "tournament_id", optparams=["date"]),
    TennisLiveDataEndpoint("matches", "tournament_id", optparams=["date"]),
    TennisLiveDataEndpoint("tournaments", "tour_code", "season_id"),  # season_id is really a year
    TennisLiveDataEndpoint("tours"),
]