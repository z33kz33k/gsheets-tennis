"""

    rapidapi.sofascore.data.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI SofaScore enums and dataclasses.

    @author: z33k

"""
import csv
from dataclasses import dataclass
from dateutil import parser
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Generator, Optional


class Hand(Enum):
    RIGHT = "R"
    LEFT = "L"
    UNKNOWN = "U"


@dataclass
class Player:
    id: int
    firstname: str
    lastname: str
    hand: Hand
    birthdate: Optional[datetime]
    country_code: str

    @property
    def fullname(self):
        return f"{self.firstname} {self.lastname}"


def _getplayers(source: Path) -> Generator[Player, None, None]:
    with source.open() as f:
        reader = csv.reader(f)
        for row in reader:
            id_, fn, ln, hand, bd, cc = row
            hand = next((h for h in Hand if h.value == hand), None)
            if not hand:
                hand = Hand.UNKNOWN
            try:
                bd = parser.parse(bd)
            except parser.ParserError:
                if len(bd) == 8:
                    bd = datetime.strptime(bd[:-4], "%Y")
                elif len(bd) == 6:
                    bd = datetime.strptime(bd, "%Y%m")
                else:
                    bd = None
            yield Player(int(id_), fn, ln, hand, bd, cc)


def atp_players() -> Generator[Player, None, None]:
    source = Path("data/tennis_abstract/atp/atp_players.csv")
    return _getplayers(source)


def wta_players() -> Generator[Player, None, None]:
    source = Path("data/tennis_abstract/wta/wta_players.csv")
    return _getplayers(source)





