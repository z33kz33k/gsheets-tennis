"""

    rapidapi.sofascore.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI SofaScore API handling.

    @author: z33k

"""
from datetime import datetime
import json
from pathlib import Path
from typing import List, Optional
from unicodedata import normalize

from rapidapi.sofascore.data import Status
from utils import Json, get_apikey, RequestParamsEndpoint, get_endpoint


class SofaScoreEndpoint(RequestParamsEndpoint):
    """SofaScore-specific endpoint.
    """
    HOST = "sofascore.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0]
    KEYMAP = get_apikey(API_PROVIDER, APINAME)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)


# endpoints without tennis-related potential are filtered out
ENDPOINTS = [
    SofaScoreEndpoint("list", "sport", folder="categories"),
    SofaScoreEndpoint("auto-complete", "query"),
    SofaScoreEndpoint("search", "name", folder="teams"),
    SofaScoreEndpoint("detail", "teamId", folder="teams"),
    SofaScoreEndpoint("get-performance", "teamId", folder="teams"),
    SofaScoreEndpoint("get-transfers", "teamId", folder="teams"),
    SofaScoreEndpoint("get-squad", "teamId", folder="teams"),
    SofaScoreEndpoint("get-rankings", "teamId", folder="teams"),
    SofaScoreEndpoint("get-tournaments", "teamId", folder="teams"),
    SofaScoreEndpoint("get-near-events", "teamId", folder="teams"),
    SofaScoreEndpoint("get-statistics-seasons", "teamId", folder="teams"),
    SofaScoreEndpoint("get-statistics", "teamId", "tournamentId", optparams=["type"],
                      folder="teams"),
    SofaScoreEndpoint("get-player-statistics-seasons", "teamId", folder="teams"),
    SofaScoreEndpoint("get-player-statistics", optparams=["type"], folder="teams"),
    SofaScoreEndpoint("get-last-matches", "teamId", optparams=["pageIndex"], folder="teams"),
    SofaScoreEndpoint("get-next-matches", "teamId", optparams=["pageIndex"], folder="teams"),
    SofaScoreEndpoint("search", "name", folder="players"),
    SofaScoreEndpoint("detail", "playerId", folder="players"),
    SofaScoreEndpoint("get-characteristics", "playerId", folder="players"),
    SofaScoreEndpoint("get-last-ratings", "playerId", "tournamentId", "seasonId", folder="players"),
    SofaScoreEndpoint("get-attribute-overviews", "playerId", folder="players"),
    SofaScoreEndpoint("get-national-team-statistics", "playerId", folder="players"),
    SofaScoreEndpoint("get-transfer-history", "playerId", folder="players"),
    SofaScoreEndpoint("get-last-year-summary", "playerId", folder="players"),
    SofaScoreEndpoint("get-statistics-seasons", "playerId", folder="players"),
    SofaScoreEndpoint("get-statistics", "playerId", "tournamentId", optparams=["type"],
                      folder="players"),
    SofaScoreEndpoint("get-last-matches", "playerId", optparams=["pageIndex"], folder="players"),
    SofaScoreEndpoint("get-next-matches", "playerId", optparams=["pageIndex"], folder="players"),
    SofaScoreEndpoint("detail", "matchId", folder="matches"),
    SofaScoreEndpoint("get-lineups", "matchId", folder="matches"),
    SofaScoreEndpoint("get-last-ratings", "matchId", "tournamentId", "seasonId", folder="matches"),
    SofaScoreEndpoint("get-incidents", "matchId", folder="matches"),
    SofaScoreEndpoint("get-managers", "matchId", folder="matches"),
    SofaScoreEndpoint("get-head2head", "matchId", folder="matches"),
    SofaScoreEndpoint("get-votes", "matchId", folder="matches"),
    SofaScoreEndpoint("get-graph", "matchId", folder="matches"),
    SofaScoreEndpoint("get-statistics", "matchId", folder="matches"),
    SofaScoreEndpoint("get-best-players", "matchId", folder="matches"),
    SofaScoreEndpoint("get-media", "matchId", folder="matches"),
    SofaScoreEndpoint("get-tweets", "matchId", folder="matches"),
    SofaScoreEndpoint("get-player-statistics", "matchId", "playerId", folder="matches"),
    SofaScoreEndpoint("get-player-heatmap", "matchId", "playerId", folder="matches"),
]

# teams
MEN_TEAMID_MAP = {
    "Daniel Michalski": 257091,
    "Hubert Hurkacz": 158896,
    "Kacper Żuk": 205971,
    "Kamil Majchrzak": 108709,
    "Jan Zieliński": 112805,
    "Maciej Rajski": 111783,
    "Michał Dembek": 153698,
    "Pawel Ciaś": 56577,
    "Wojciech Marek": 257864,
    "Yann Wojcik": 179258,
}
WOMEN_TEAMID_MAP = {
    "Anna Hertel": 222299,
    "Iga Świątek": 228272,
    "Katarzyna Kawa": 42492,
    "Joanna Zawadzka": 161400,
    "Magda Linette": 42289,
    "Magdalena Fręch": 71250,
    "Maja Chwalińska": 211014,
    "Martyna Kubka": 294815,
    "Paula Kania": 45903,
    "Stefania Rogozińska-Dzik": 222185,
    "Urszula Radwańska": 19329,
    "Weronika Baszak": 321865,
    "Weronika Falkowska": 217160,
}
TEAMID_MAP = {**MEN_TEAMID_MAP, **WOMEN_TEAMID_MAP}
PLAYERNAMES_MAP = {v: k for k, v in TEAMID_MAP.items()}  # reversed, ex. {228272: "Iga Świątek"}


def to_slug(name: str) -> str:
    """Convert name to sofascore 'slug'.

    Example:
        >>> to_slug("Iga Świątek")
        >>> 'swiatek-iga'
    """
    return "-".join(normalize("NFKD", name).encode("ascii", "ignore").decode(
        "utf-8").lower().split())


def prune_canceled(matches_data: List[Json]) -> List[Json]:
    return [data for data in matches_data if data["status"]["description"]
            not in (Status.CANCELED.value, Status.COVERAGE_CANCELED.value, Status.WARNING.value)]


def pull_matches(player_teamid: int, page_index=0) -> Json:
    endpoint = get_endpoint(ENDPOINTS, "get-last-matches", "teams")
    playername = next((k for k, v in TEAMID_MAP.items() if v == player_teamid), None)
    if not playername:
        raise ValueError(f"Invalid player team ID: {player_teamid}.")

    data = endpoint.retrieve(str(player_teamid), pageIndex=page_index)
    return data["events"]


def pull_all_matches(player_teamid: int) -> List[Json]:
    playername = PLAYERNAMES_MAP.get(player_teamid)
    if not playername:
        raise ValueError(f"Invalid player team ID: {player_teamid}.")
    print(f"Pulling matches for player '{playername}'...")
    matches, page_index = [], 0
    while True:
        result = pull_matches(player_teamid, page_index)
        new_batch = result.get("events")
        if not new_batch:
            print("Pulling finished unexpectedly (no 'events' key in the result JSON). Exiting.")
            return matches
        matches += new_batch
        print(f"Pulled results page no. {page_index}. Total number of matches pulled: "
              f"'{len(matches)}'...")
        if not result["hasNextPage"]:
            break
        page_index += 1

    print("Finished pulling.")
    return matches


def dump_matches(data: List[Json], playername: str) -> None:
    dt = datetime.now()
    month = f"0{dt.month}" if len(str(dt.month)) == 1 else str(dt.month)
    day = f"0{dt.day}" if len(str(dt.day)) == 1 else str(dt.day)
    datedir = f"{dt.year}{month}{day}"
    filename = "_".join(item.lower() for item in playername.split()) + ".json"
    dest = Path("../../data") / datedir
    dest.mkdir(exist_ok=True, parents=True)
    dest /= filename
    with dest.open(mode="w", encoding="UTF-8") as f:
        json.dump(data, f, indent=4)
    print(f"Dumping of {len(data)} matches data finished successfully at: {dest}.")

