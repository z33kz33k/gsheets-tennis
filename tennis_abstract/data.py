"""

    tennis_abstract.data.py
    ~~~~~~~~~~~~~~~~~~~~~~~
    Tennis Abstract enums and dataclasses.

    @author: z33k

"""
import csv
from dataclasses import dataclass
from dateutil import parser
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Generator, Optional


class Hand(Enum):
    """Hand played.
    """
    RIGHT = "R"
    LEFT = "L"
    UNKNOWN = "U"


@dataclass
class Player:
    """Player as defined in Tennis Abstract data.
    """
    id: int
    firstname: str
    lastname: str
    hand: Hand
    birthdate: Optional[datetime]
    country_code: str

    @property
    def fullname(self):
        return f"{self.firstname} {self.lastname}"

    @property
    def csv_row(self) -> str:
        return f"{self.id},{self.firstname},{self.lastname},{self.hand.value}," \
               f"{self.birthdate.strftime('%Y%m%d')},{self.country_code}"


def getplayers(csvsource: Path,
               filter_: Optional[Callable[[Player], bool]]) -> Generator[Player, None, None]:
    """Return players from csvsource. Optionally, use a filtering function.

    Example:
        >>> poles = [*(getplayers(source, filter_=lambda p: p.country_code == "POL"))]
    """
    with csvsource.open() as f:
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
            player = Player(int(id_), fn, ln, hand, bd, cc)
            if filter_ is not None and filter_(player):
                yield player
            elif filter_ is None:
                yield player


def atp_players(filter_: Optional[Callable[[Player], bool]]) -> Generator[Player, None, None]:
    """Return ATP players from default Tennis Abstract data destination. Optionally,
    use a filtering function.
    """
    source = Path("data/tennis_abstract/atp/atp_players.csv")
    return getplayers(source, filter_=filter_)


def wta_players(filter_: Optional[Callable[[Player], bool]]) -> Generator[Player, None, None]:
    """Return WTA players from default Tennis Abstract data destination. Optionally,
    use a filtering function.
    """
    source = Path("data/tennis_abstract/wta/wta_players.csv")
    return getplayers(source, filter_=filter_)


def atp_players_1978(filter_: Optional[Callable[[Player], bool]]) -> Generator[Player, None, None]:
    """Return all ATP players born since 1978 from default Tennis Abstract data destination.
    Optionally, use a filtering function.
    """
    source = Path("data/tennis_abstract/_reshaped/atp_players_1978.csv")
    return getplayers(source, filter_=filter_)


def wta_players_1978(filter_: Optional[Callable[[Player], bool]]) -> Generator[Player, None, None]:
    """Return all WTA players born since 1978 from default Tennis Abstract data destination.
    Optionally, use a filtering function.
    """
    source = Path("data/tennis_abstract/_reshaped/wta_players_1978.csv")
    return getplayers(source, filter_=filter_)
