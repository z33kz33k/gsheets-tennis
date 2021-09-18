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

import requests

Json = Dict[str, Any]
API_CREDS_FILE = Path("api_creds.json")


class InsufficientDataError(ValueError):
    """Raised when data pulled is insufficient (from a variety of reasons).
    """


def get_apikey(provider: str, api: str) -> Json:
    data = json.loads(API_CREDS_FILE.read_text())
    provider = data.get(provider)
    if not provider:
        raise ValueError(f"Invalid provider: {provider}.")
    apikey = provider.get(api)
    if not apikey:
        raise ValueError(f"Invalid API: {api}.")
    return apikey


def endpoint_retrieve(endpoint_url: str, headersmap: Dict[str, str], paramsmap: Dict[str, str],
                      dumpdest: Optional[Path] = None) -> Union[Json, List[Json]]:
    response = requests.request("GET", endpoint_url, headers=headersmap, params=paramsmap)
    data = json.loads(response.text)

    if dumpdest is not None:
        with dumpdest.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    return data


class Endpoint(metaclass=ABCMeta):
    """API endpoint.
    """
    PREFIX = "http://"
    HEADERS_MAP: Dict[str, str] = {}
    HOST: str = ""  # eg. "tennis-live-data.p.rapidapi.com"

    def __init__(self, endpoint: str, *params, folder: Optional[str] = None) -> None:
        if type(self) is Endpoint:
            raise TypeError(f"Abstract class {self.__class__.__name__} must not be instantiated.")
        self.endpoint = endpoint
        self.params = params
        self.folder = folder

    @property
    @abstractmethod
    def url(self) -> str:
        """This endpoint's URL.
        """

    @abstractmethod
    def retrieve(self, *paramvalues: str,
                 dumpdest: Optional[Path] = None) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """


class UrlParamsEndpoint(Endpoint):
    """API endpoint that sends parameters via 'url' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str, folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, folder=folder)

    @property
    def url(self) -> str:
        """This endpoint's URL."""
        if self.folder:
            return f"{self.PREFIX}{self.HOST}/{self.folder}/{self.endpoint}"
        return f"{self.PREFIX}{self.HOST}/{self.endpoint}"

    def retrieve(self, *paramvalues: str,
                 dumpdest: Optional[Path] = None) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        if len(paramvalues) != len(self.params):
            raise ValueError(f"Invalid number of request's parameter values: "
                             f"{len(paramvalues)}.")
        url = f"{self.url}/{'/'.join(paramvalues)}"
        if not paramvalues:
            url = url[:-1]
        response = requests.request("GET", url, headers=self.HEADERS_MAP)
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


class RequestParamsEndpoint(Endpoint):
    """API endpoint that sends parameters using 'params' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str,
                 optparams: Optional[List[str]] = None, folder: Optional[str] = None) -> None:
        super().__init__(endpoint, *params, folder=folder)
        self.optparams = optparams if optparams else []

    @property
    def url(self) -> str:
        """This endpoint's URL."""
        if self.folder:
            return f"{self.PREFIX}{self.HOST}/{self.folder}/{self.endpoint}"
        return f"{self.PREFIX}{self.HOST}/{self.endpoint}"

    def paramsmap(self, *values, **optvalues) -> Dict[str, str]:
        if len(self.params) != len(values):
            raise ValueError(f"Invalid number of values: {len(values)}.")
        err_keys = [k for k in optvalues if k not in self.optparams]
        if err_keys:
            raise ValueError(f"Invalid optional values: {optvalues}.")
        paramsmap = {k: v for k, v in zip(self.params, values)}
        paramsmap.update(optvalues)
        return paramsmap

    def retrieve(self, *paramvalues: str,
                 dumpdest: Optional[Path] = None, **optparamvalues) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        paramsmap = self.paramsmap(*paramvalues, **optparamvalues)
        response = requests.request("GET", self.url, headers=self.HEADERS_MAP, params=paramsmap)
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


def get_endpoint(endpoints: List[Endpoint], name: str,
                 foldername: Optional[str] = None) -> Optional[Endpoint]:
    if foldername:
        return next((e for e in endpoints if e.endpoint == name and e.folder == foldername), None)
    return next((e for e in endpoints if e.endpoint == name), None)
