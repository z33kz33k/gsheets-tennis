"""

    rapidapi.sofascore.data.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RapidAPI SofaScore enums and dataclasses.

    @author: z33k

"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Generator, List, Optional, Tuple

from utils import Json, InsufficientDataError


class Ground(Enum):
    CLAY = "Clay"
    GRASS = "Grass"
    HARDCOURT_OUTDOOR = "Hardcourt outdoor"
    HARDCOURT_INDOOR = "Hardcourt indoor"
    SYNTHETIC_GRASS = "Synthetic grass"


class Category(Enum):
    WTA = "wta"
    ATP = "atp"
    CHALLENGER = "challenger"
    EXHIBITION = "exhibition"
    ITF_MEN = "itf-men"
    ITF_WOMEN = "itf-women"
    DAVIS_CUP = "davis-cup"
    JUNIORS = "juniors"


class Gender(Enum):
    FEMALE = 0
    MALE = 1


class Side(Enum):
    HOME = 0
    AWAY = 1


class Type(Enum):
    MIXED_DOUBLES = 0
    SINGLES = 1
    DOUBLES = 2


class Status(Enum):
    RETIRED = "Retired"
    ENDED = "Ended"
    CANCELED = "Canceled"
    COVERAGE_CANCELED = "Coverage canceled"
    WALKOVER = "Walkover"


@dataclass(frozen=True)
class Tournament:
    name: str
    altname: str
    category: Category
    popularity: int  # 'userCont' in JSON, probably number of followers on SofaScore
    ssid: int


@dataclass(frozen=True)
class Contender:
    name: str
    popularity: int  # 'userCont' in JSON, probably number of followers on SofaScore
    ss_slug: str
    ssid: int
    is_winner: bool
    side: Side
    gender: Optional[Gender] = field(default=None)  # can be missing in sofascore data
    ranking: Optional[int] = field(default=None)  # can be missing in sofascore data

    # override
    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class SetScore:
    home_score: int
    away_score: int
    home_tiebreak: Optional[int] = field(default=None)
    away_tiebreak: Optional[int] = field(default=None)

    def __post_init__(self) -> None:
        if self.home_score is None or self.away_score is None:
            if self.home_tiebreak is not None or self.away_tiebreak is not None:
                raise ValueError("Invalid input data. Main scores 'None' while tiebreaks not.")
            return
        if (self.home_tiebreak is not None and self.home_score not in (6, 7)
                or self.away_tiebreak is not None and self.away_score not in (6, 7)):
            raise ValueError(f"Invalid init data: home tiebreak: {self.home_tiebreak}, "
                             f"home score: {self.home_score}, away tiebreak: "
                             f"{self.away_tiebreak}, away score: {self.away_score}.")

    # 'None' is possible for 'Retired' matches, also in those scenarios winner by the scores
    # can end up losing the match
    @property
    def winner(self) -> Optional[Side]:
        if self.home_score > self.away_score:
            return Side.HOME
        elif self.away_score > self.home_score:
            return Side.AWAY
        else:
            return None

    @property
    def loser(self) -> Optional[Side]:
        if self.winner is Side.AWAY:
            return Side.HOME
        elif self.winner is Side.HOME:
            return Side.AWAY
        else:
            return None


@dataclass(frozen=True)
class Score:
    set1: SetScore
    set2: Optional[SetScore] = field(default=None)  # optional only for 'Retired' matches
    set3: Optional[SetScore] = field(default=None)
    set4: Optional[SetScore] = field(default=None)
    set5: Optional[SetScore] = field(default=None)

    @property
    def scores(self) -> Generator[SetScore, None, None]:
        return (score for score in (self.set1, self.set2, self.set3, self.set4, self.set5)
                if score is not None)

    # 'None' is possible for 'Retired' matches, also in those scenarios winner by the scores
    # can end up losing the match
    @property
    def winner(self) -> Optional[Side]:
        home_wins = [score for score in self.scores if score.winner is Side.HOME]
        away_wins = [score for score in self.scores if score.winner is Side.AWAY]
        if len(home_wins) > len(away_wins):
            return Side.HOME
        elif len(away_wins) > len(home_wins):
            return Side.AWAY
        else:
            return None

    @property
    def loser(self) -> Optional[Side]:
        if self.winner is Side.AWAY:
            return Side.HOME
        elif self.winner is Side.HOME:
            return Side.AWAY
        else:
            return None


class Time:
    def __init__(self, timestamp: int, set1: Optional[int] = None, set2: Optional[int] = None,
                 set3: Optional[int] = None, set4: Optional[int] = None,
                 set5: Optional[int] = None) -> None:
        self._timestamp = datetime.utcfromtimestamp(timestamp)
        # set times can be entirely missing from sofascore data
        self._set1 = timedelta(seconds=set1) if set1 else None
        self._set2 = timedelta(seconds=set2) if set2 else None
        self._set3 = timedelta(seconds=set3) if set3 else None
        self._set4 = timedelta(seconds=set4) if set4 else None
        self._set5 = timedelta(seconds=set5) if set5 else None

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def set1(self) -> Optional[timedelta]:
        return self._set1

    @property
    def set2(self) -> Optional[timedelta]:
        return self._set2

    @property
    def set3(self) -> Optional[timedelta]:
        return self._set3

    @property
    def set4(self) -> Optional[timedelta]:
        return self._set4

    @property
    def set5(self) -> Optional[timedelta]:
        return self._set5

    @property
    def times(self) -> Generator[timedelta, None, None]:
        return (time for time in (self.set1, self.set2, self.set3, self.set4, self.set5)
                if time is not None)

    # override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timestamp={self.timestamp}, set1={self.set1}, " \
               f"set2={self.set2}, set3={self.set3}, set4={self.set4}, set5={self.set5})"


class Match:
    """Tennis match statistics as pulled from sofascore.com.

    NOTE: this class expects non-calceled match data on input.
    """
    def __init__(self, data: Json) -> None:
        self._data = data
        self.status: Status = self._get_status()
        self.ssid: str = data["customId"]
        self.tournament: Tournament = self._get_tournament()
        self.round: Optional[str] = data["roundInfo"]["name"] if data.get("roundInfo") else None
        self.first_to_serve: Optional[Side] = self._get_first_to_serve()
        self.score: Score = self._get_score()
        self.winner: Side = self._get_winner()
        self.home_contenders: Tuple[Contender, Optional[Contender]] = self._get_contenders()
        self.away_contenders: Tuple[Contender, Optional[Contender]] = self._get_contenders(
            home=False)
        self.time: Time = self._get_time()
        self.ground: Optional[Ground] = next((ground for ground in Ground if ground.value == data[
            "groundType"]), None) if data.get("groundType") else None

    def _get_status(self) -> Status:
        status = self._data["status"]["description"]
        if status == Status.ENDED.value:
            return Status.ENDED
        elif status == Status.RETIRED.value:
            return Status.RETIRED
        else:
            raise ValueError(f"Invalid input status data: {self._data}.")

    def _get_tournament(self) -> Tournament:
        name = self._data["tournament"]["name"]
        altname = self._data["tournament"]["uniqueTournament"]["name"]
        category = next((cat for cat in Category
                         if cat.value == self._data["tournament"]["category"]["slug"]), None)
        if not category:
            raise ValueError(f"Invalid input, can't parse for category: {self._data}")
        popularity = self._data["tournament"]["uniqueTournament"]["userCount"]
        id_ = self._data["tournament"]["category"]["id"]
        return Tournament(name, altname, category, popularity, id_)

    def _get_first_to_serve(self) -> Optional[Side]:
        data = self._data.get("firstToServe")
        if data == 1:
            return Side.HOME
        elif data == 2:
            return Side.AWAY
        return None

    def _get_score(self) -> Score:
        def getscores(data: Json, tiebreaks=False) -> List[Optional[int]]:
            template = "period{}"
            if tiebreaks:
                template += "TieBreak"
            return [data.get(template.format(i)) for i in range(1, 6)]

        home_scores = getscores(self._data["homeScore"])
        home_tiebreaks = getscores(self._data["homeScore"], tiebreaks=True)
        away_scores = getscores(self._data["awayScore"])
        away_tiebreaks = getscores(self._data["awayScore"], tiebreaks=True)

        set_scores = [SetScore(hs, as_, ht, at) for hs, as_, ht, at
                      in zip(home_scores, away_scores, home_tiebreaks, away_tiebreaks)]
        set_scores = [ss for ss in set_scores
                      if ss.home_score is not None and ss.away_score is not None]
        return Score(*set_scores)

    def _get_winner(self) -> Side:
        winner = self._data["winnerCode"]
        if winner == 1:
            return Side.HOME
        elif winner == 2:
            return Side.AWAY
        else:
            raise ValueError(f"Invalid winner input data: {self._data}.")

    def _get_contenders(self, home=True) -> Tuple[Contender, Optional[Contender]]:
        def getcontender(data_: Json) -> Contender:
            name = data_["name"]
            gdata = data_.get("gender")
            if not gdata:
                gender = None
            else:
                if gdata == "M":
                    gender = Gender.MALE
                elif gdata == "F":
                    gender = Gender.FEMALE
                else:
                    raise ValueError(f"Invalid gender data: {data_}.")
            popularity = data_["userCount"]
            ss_slug = data_["slug"]
            ssid = data_["id"]
            if home:
                is_winner = True if self.winner is Side.HOME else False
            else:
                is_winner = True if self.winner is Side.AWAY else False
            side = Side.HOME if home else Side.AWAY
            ranking = data_.get("ranking")
            return Contender(name, popularity, ss_slug, ssid, is_winner, side, gender, ranking)

        key = "homeTeam" if home else "awayTeam"
        data = self._data[key]
        if data["subTeams"]:
            if len(data["subTeams"]) != 2:
                raise ValueError(f"Invalid subteams data: {data}.")
            return getcontender(data["subTeams"][0]), getcontender(data["subTeams"][1])
        return getcontender(data), None

    def _get_time(self) -> Time:
        template = "period{}"
        times = [self._data["time"].get(template.format(i)) for i in range(1, 6)]
        times = [t for t in times if t]
        return Time(self._data["startTimestamp"], *times)

    @property
    def home_contender(self) -> Contender:
        return self.home_contenders[0]

    @property
    def away_contender(self) -> Contender:
        return self.away_contenders[0]

    # override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tournament={self.tournament}, " \
               f"round={self.round}, type={self.type}, " \
               f"home_contenders={self.home_contenders}, " \
               f"away_contenders={self.away_contenders}, score={self.score}, " \
               f"time={self.time}, ground={self.ground}, " \
               f"first_to_serve={self.first_to_serve}, ssid={self.ssid})"

    @property
    def type(self) -> Type:
        home2 = self.home_contenders[1]
        if home2 is not None:
            if (all(c.gender is not None for c in self.home_contenders)
                    and (self.home_contender.gender != home2.gender)):
                return Type.MIXED_DOUBLES
            return Type.DOUBLES
        return Type.SINGLES


