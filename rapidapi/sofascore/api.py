"""

    rapidapi.sofascore.api.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI SofaScore API handling.

    @author: z33k

"""
from datetime import datetime
import json
from pathlib import Path
from typing import List
from unicodedata import normalize

import requests

from rapidapi.sofascore.data import Status
from utils import Json, get_apikey

HOSTMAP = {'x-rapidapi-host': "sofascore.p.rapidapi.com"}
KEYMAP = get_apikey("rapidapi", "sofascore")
HEADERS_MAP = HOSTMAP.update(KEYMAP)
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
    url = "https://sofascore.p.rapidapi.com/teams/get-last-matches"
    playername = next((k for k, v in TEAMID_MAP.items() if v == player_teamid), None)
    if not playername:
        raise ValueError(f"Invalid player team ID: {player_teamid}.")
    if page_index < 0:
        raise ValueError(f"Negative page index: {page_index}.")

    querystring = {"teamId": f"{player_teamid}", "pageIndex": str(page_index)}
    response = requests.request("GET", url, headers=HEADERS, params=querystring)

    return json.loads(response.text)


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

