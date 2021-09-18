"""

    run.py
    ~~~~~~
    Run the script for debugging and testing.

    @author: z33k

"""

# TEAMID_MAP = {k: v for k, v in TEAMID_MAP.items()
#               if k not in ["Iga Świątek", "Daniel Michalski", "Hubert Hurkacz"]}
#
# ids = [v for v in TEAMID_MAP.values()]
#
# for id_ in ids:
#     pull_last_matches(id_)

# playername = "Kacper Żuk"
# teamid = TEAMID_MAP[playername]
# data = pull_full_matches(teamid)
# dump_matches(data, playername)

# import json
# from pathlib import Path
# from pprint import pprint
#
# from tennis import Match, Type
# from utils import prune_canceled
#
#
# source = Path("data/20210917")
# files = [*source.iterdir()]
# zuk_json = next((f for f in files if "żuk" in f.name), None)
# zuk_data = prune_canceled(json.loads(zuk_json.read_text()))
# matches = [Match(data) for data in zuk_data]
#
# singles = [m for m in matches if m.type is Type.SINGLES]
#
# zuk_instances = [c for m in singles for c in [*m.home_contenders, *m.away_contenders]
#                  if c and c.ss_slug == "zuk-kacper"]
#
# pprint(zuk_instances)
from pathlib import Path

from utils import endpoint_retrieve
from rapidapi.sofascore.api import HEADERS_MAP

url = "https://sofascore.p.rapidapi.com/teams/get-statistics"
paramsmap = {"teamId": "228272"}
dest = Path()

# endpoint_retrieve()


