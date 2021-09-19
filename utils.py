"""

    api.py
    ~~~~~~~~~
    Utility functions.

    @author: z33k

"""
from abc import ABCMeta, abstractmethod
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from contexttimer import Timer
import requests

Json = Dict[str, Any]
API_CREDS_FILE = Path("api_creds.json")


class InsufficientDataError(ValueError):
    """Raised when data pulled is insufficient (from a variety of reasons).
    """


def get_apikey(provider: str) -> Json:
    data = json.loads(API_CREDS_FILE.read_text())
    keydata = data.get(provider)
    if not keydata:
        raise ValueError(f"Invalid provider: {provider}.")
    return keydata


def endpoint_retrieve(endpoint_url: str, headersmap: Dict[str, str], paramsmap: Dict[str, str],
                      dumpdest: Optional[Path] = None) -> Union[Json, List[Json]]:
    print(f"Retrieving data from '{endpoint_url}' with params '{paramsmap}'...")
    with Timer() as t:
        response = requests.request("GET", endpoint_url, headers=headersmap, params=paramsmap)
    print(f"Request completed in {t.elapsed} seconds.")
    data = json.loads(response.text)

    if dumpdest is not None:
        with dumpdest.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    return data


class ApiEndpoint(metaclass=ABCMeta):
    """API endpoint.
    """
    PREFIX = "https://"
    HEADERS_MAP: Dict[str, str] = {}
    HOST: str = ""  # eg. "tennis-live-data.p.rapidapi.com"
    API_PROVIDER: str = ""  # eg. "rapidapi"
    APINAME: str = ""  # eg. "sofascore"

    def __init__(self, endpoint: str, *params, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        if type(self) is ApiEndpoint:
            raise TypeError(f"Abstract class {self.__class__.__name__} must not be instantiated.")
        self.endpoint = endpoint
        self.params = params if params else ()
        self.optparams = optparams if optparams else ()
        self.folder = folder

    @property
    @abstractmethod
    def url(self) -> str:
        """This endpoint's URL.
        """

    @abstractmethod
    def retrieve(self, *paramvalues: str,
                 dumpdest: Optional[Path] = None, **optparamvalues) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """

    def _validate_paramvalues(self, *paramvalues) -> None:
        if len(self.params) != len(paramvalues):
            raise ValueError(f"Invalid number of values: {len(paramvalues)}.")

    def paramsmap(self, *values) -> Dict[str, str]:
        """Return params to values map.
        """
        self._validate_paramvalues(*values)
        return {k: v for k, v in zip(self.params, values)}

    def _validate_optparamvalues(self, **optparamvalues) -> None:
        err_keys = [k for k in optparamvalues if k not in self.optparams]
        if err_keys:
            raise ValueError(f"Invalid optional values: {optparamvalues}.")

    def optparamsmap(self, **optvalues) -> Dict[str, str]:
        """Validate optvalues and return it.
        """
        self._validate_optparamvalues(**optvalues)
        return optvalues

    def _sample_dest(self, *paramvalues, **optparamvalues) -> Path:
        destdir = Path("data") / self.API_PROVIDER / self.APINAME / "samples"
        if not destdir.exists():
            destdir.mkdir(parents=True)
        filename = ""
        if self.folder:
            filename += self.folder + "_"
        filename += self.endpoint.replace("-", "_")
        if paramvalues:
            filename += f"_{'_'.join(paramvalues)}"
        if optparamvalues:
            filename += f"_{'_'.join([*optparamvalues.values()])}"
        filename += ".json"

        return destdir / filename

    def dump_sample(self, *paramvalues: str, **optparamvalues) -> Union[Json, List[Json]]:
        """Retrieve sample data from this endpoint and dump it at default location.
        """
        self._validate_paramvalues(*paramvalues)
        self._validate_optparamvalues(**optparamvalues)
        dest = self._sample_dest(*paramvalues, **optparamvalues)
        return self.retrieve(*paramvalues, dumpdest=dest, **optparamvalues)

    def read_sample(self, *paramvalues: str, **optparamvalues) -> Union[Json, List[Json]]:
        self._validate_paramvalues(*paramvalues)
        self._validate_optparamvalues(**optparamvalues)
        dest = self._sample_dest(*paramvalues, **optparamvalues)
        return json.loads(dest.read_text())

    def __repr__(self) -> str:  # override
        return f"{self.__class__.__name__}(folder={self.folder}, endpoint={self.endpoint}, " \
               f"params={self.params}, optparams={self.optparams})"


class UrlParamsEndpoint(ApiEndpoint):
    """API endpoint that sends parameters via 'url' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)

    @property
    def url(self) -> str:  # override
        """This endpoint's URL."""
        if self.folder:
            return f"{self.PREFIX}{self.HOST}/{self.folder}/{self.endpoint}"
        return f"{self.PREFIX}{self.HOST}/{self.endpoint}"

    def retrieve(self, *paramvalues: str,   # override
                 dumpdest: Optional[Path] = None, **optparamvalues) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        # validation
        self._validate_paramvalues(*paramvalues)
        self._validate_optparamvalues(**optparamvalues)

        url = f"{self.url}"
        if paramvalues:
            url += f"/{'/'.join(paramvalues)}"
        if optparamvalues:
            url += f"/{'/'.join([*optparamvalues.values()])}"

        print(f"Retrieving data from '{url}'...")
        with Timer() as t:
            response = requests.request("GET", url, headers=self.HEADERS_MAP)
        print(f"Request completed in {t.elapsed} seconds.")
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


class RequestParamsEndpoint(ApiEndpoint):
    """API endpoint that sends parameters using 'params' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str,
                 optparams: Optional[List[str]] = None, folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)

    @property
    def url(self) -> str:  # override
        """This endpoint's URL."""
        if self.folder:
            return f"{self.PREFIX}{self.HOST}/{self.folder}/{self.endpoint}"
        return f"{self.PREFIX}{self.HOST}/{self.endpoint}"

    def retrieve(self, *paramvalues: str,  # override
                 dumpdest: Optional[Path] = None, **optparamvalues) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        paramsmap, optparamsmap = self.paramsmap(*paramvalues), self.optparamsmap(**optparamvalues)
        paramsmap.update(optparamsmap)
        print(f"Retrieving data from '{self.url}' with parameters: {paramsmap}...")
        with Timer() as t:
            response = requests.request("GET", self.url, headers=self.HEADERS_MAP, params=paramsmap)
        print(f"Request completed in {t.elapsed:.3f} seconds.")
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


def get_endpoint(endpoints: List[ApiEndpoint], name: str,
                 folder: Optional[str] = None) -> Optional[ApiEndpoint]:
    if folder:
        return next((e for e in endpoints if e.endpoint == name and e.folder == folder), None)
    return next((e for e in endpoints if e.endpoint == name), None)
