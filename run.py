"""

    run.py
    ~~~~~~
    Run the script for debugging and testing.

    @author: z33k

"""
from pprint import pprint

from rapidapi.sportscore.api import ENDPOINTS
from utils import get_endpoint

endpoint = get_endpoint(ENDPOINTS, "events", folder="sports")
endpoint.dump_sample("2", "2021-09-06")

# pprint(endpoint.retrieve("iga świątek ranking"))
# result = endpoint.read_sample("228272")
# print(len(result["events"]))

