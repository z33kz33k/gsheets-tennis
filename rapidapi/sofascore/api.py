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
    """SofaScore API endpoint.
    """
    HOST = "sofascore.p.rapidapi.com"
    HOSTMAP = {'x-rapidapi-host': HOST}
    API_PROVIDER = HOST.split(".")[2]
    APINAME = HOST.split(".")[0]
    KEYMAP = get_apikey(API_PROVIDER)
    HEADERS_MAP = {**HOSTMAP, **KEYMAP}

    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)


# endpoints without tennis-related potential and those checked to be useless are filtered out
ENDPOINTS = [
    # teams
    # returns 'categories' list (see Category class in data.py)
    SofaScoreEndpoint("list", "sport", folder="categories"),
    # returns 'suggestions' list for query (eg. for 'iga świątek' it returns one: "Świątek, Iga")
    SofaScoreEndpoint("auto-complete", "query"),
    # returns 'teams' list with data for teams that match given name
    SofaScoreEndpoint("search", "name", folder="teams"),
    # returns 'team' dict with details for the given teamId
    SofaScoreEndpoint("detail", "teamId", folder="teams"),
    # return 'events' list (last 10 matches data) and 'points' dict with float for each listed match
    # this corresponds to FORM chart on: https://www.sofascore.com/team/tennis/swiatek-iga/228272
    SofaScoreEndpoint("get-performance", "teamId", folder="teams"),
    # see the sample for details, not very useful overall as it really gives only last ranking
    # data and some sparse info on earlier performance (best ranking, best ranking date,
    # previous ranking, number of tournaments played etc.)
    SofaScoreEndpoint("get-rankings", "teamId", folder="teams"),
    # returns 'previousEvent' dict (info on the last match played)
    SofaScoreEndpoint("get-near-events", "teamId", folder="teams"),
    # useful as it can return (when fed consecutive pageIndex values) whole history of a player's
    # matches (see 'pull_all_matches()' below), sadly returned data for a match's competitors is
    # flat (that means it's recent instead of being specific to the match's time)
    SofaScoreEndpoint("get-last-matches", "teamId", optparams=["pageIndex"], folder="teams"),
    # probably dependent on time of request but when tested returned no data
    SofaScoreEndpoint("get-next-matches", "teamId", optparams=["pageIndex"], folder="teams"),

    # matches
    # returns 'event' dict with match info (not very useful as this is mostly the same as what
    # 'get-last-matches' gives but only of one item
    SofaScoreEndpoint("detail", "matchId", folder="matches"),
    # returns 'tournaments' list of head2head matches, useful
    SofaScoreEndpoint("get-head2head", "matchId", folder="matches"),
    # returns votes for and against something, whatever it is - not useful
    SofaScoreEndpoint("get-votes", "matchId", folder="matches"),
    # returns data corresponding to MATCHES/STATISTICS chart
    # on: https://www.sofascore.com/team/tennis/swiatek-iga/228272
    SofaScoreEndpoint("get-statistics", "matchId", folder="matches"),
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

