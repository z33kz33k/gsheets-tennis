"""

    run.py
    ~~~~~~
    Run the script for debugging and testing.

    @author: z33k

"""
from pprint import pprint

from rapidapi.tennis_live_data.api import ENDPOINTS
from utils import get_endpoint

endpoint = get_endpoint(ENDPOINTS, "matches-results-by-player")
endpoint.dump_sample("1088", "1369644")

# pprint(endpoint.retrieve("iga świątek ranking"))
# result = endpoint.read_sample("228272")
# print(len(result["events"]))

