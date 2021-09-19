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
    def url(self) -> str:
        """This endpoint's URL."""
        if self.folder:
            return f"{self.PREFIX}{self.HOST}/{self.folder}/{self.endpoint}"
        return f"{self.PREFIX}{self.HOST}/{self.endpoint}"

    @abstractmethod
    def retrieve(self, *paramvalues: str,
                 dumpdest: Optional[Path] = None, **optparamvalues: str) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """

    def _validate_paramvalues(self, *paramvalues: str) -> None:
        if len(self.params) != len(paramvalues):
            raise ValueError(f"Invalid number of parameter values: {len(paramvalues)}.")

    def paramsmap(self, *paramvalues: str) -> Dict[str, str]:
        """Return params to values map.
        """
        self._validate_paramvalues(*paramvalues)
        return {k: v for k, v in zip(self.params, paramvalues)}

    def _validate_optparamvalues(self, **optparamvalues) -> None:
        err_keys = [k for k in optparamvalues if k not in self.optparams]
        if err_keys:
            raise ValueError(f"Invalid optional parameter values: {optparamvalues}.")

    def optparamsmap(self, **optparamvalues: str) -> Dict[str, str]:
        """Validate optparamvalues and return it.
        """
        self._validate_optparamvalues(**optparamvalues)
        return optparamvalues

    def _sample_dest(self, *paramvalues: str, **optparamvalues: str) -> Path:
        destdir = Path("data") / self.API_PROVIDER / self.APINAME / "samples"
        if not destdir.exists():
            destdir.mkdir(parents=True)
        filename = ""
        if self.folder:
            filename += self.folder.replace("/", "_") + "_"
        filename += self.endpoint.replace("-", "_")
        if paramvalues:
            filename += f"_{'_'.join(paramvalues)}"
        if optparamvalues:
            filename += f"_{'_'.join([*optparamvalues.values()])}"
        filename += ".json"

        return destdir / filename

    def dump_sample(self, *paramvalues: str, **optparamvalues: str) -> Union[Json, List[Json]]:
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


class UrlParamsEndpoint(ApiEndpoint, metaclass=ABCMeta):
    """API endpoint that sends parameters via 'url' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str, optparams: Optional[List[str]] = None,
                 folder: Optional[str] = None, optparams_in_url=True) -> None:
        if type(self) is UrlParamsEndpoint:
            raise TypeError(f"Abstract class {self.__class__.__name__} must not be instantiated")
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)
        self.optparams_in_url = optparams_in_url

    def retrieve(self, *paramvalues: str,   # override
                 dumpdest: Optional[Path] = None, **optparamvalues: str) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        # validation
        self._validate_paramvalues(*paramvalues)
        self._validate_optparamvalues(**optparamvalues)

        url = self.url
        if paramvalues:
            url += f"/{'/'.join(paramvalues)}"
        if optparamvalues and self.optparams_in_url:
            url += f"/{'/'.join([*optparamvalues.values()])}"

        print(f"Retrieving data from '{url}'...")
        with Timer() as t:
            if self.optparams_in_url:
                response = requests.request("GET", url, headers=self.HEADERS_MAP)
            else:
                response = requests.request("GET", url, headers=self.HEADERS_MAP,
                                            params=optparamvalues)

        print(f"Request completed in {t.elapsed} seconds.")
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


class RequestParamsEndpoint(ApiEndpoint, metaclass=ABCMeta):
    """API endpoint that sends parameters using 'params' arg of 'requests.request()' method.
    """
    def __init__(self, endpoint: str, *params: str,
                 optparams: Optional[List[str]] = None, folder: Optional[str] = None) -> None:
        if type(self) is RequestParamsEndpoint:
            raise TypeError(f"Abstract class {self.__class__.__name__} must not be instantiated")
        super().__init__(endpoint, *params, optparams=optparams, folder=folder)

    def retrieve(self, *paramvalues: str,  # override
                 dumpdest: Optional[Path] = None, **optparamvalues: str) -> Union[Json, List[Json]]:
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


class MainParamEndpoint(UrlParamsEndpoint):
    """URL-type API endpoint with main param betwixt 'folder' and 'endpoint' values.

    NOTE: methods of this class treat first parameter of 'paramvalues' vararg as main parameter
    and as such it's obligatory.
    """
    def __init__(self, endpoint: str, mainparam: str, *params: str,
                 optparams: Optional[List[str]] = None, folder: Optional[str] = None,
                 optparams_in_url=True) -> None:
        super().__init__(endpoint, *params, optparams=optparams, folder=folder,
                         optparams_in_url=optparams_in_url)
        self.mainparam = mainparam

    def _validate_paramvalues(self, *paramvalues: str) -> None:  # override
        if len([self.mainparam, *self.params]) != len(paramvalues):
            raise ValueError(f"Invalid number of parameter values: {len(paramvalues)}.")

    def _sample_dest(self, *paramvalues: str, **optparamvalues: str) -> Path:  # override
        destdir = Path("data") / self.API_PROVIDER / self.APINAME / "samples"
        if not destdir.exists():
            destdir.mkdir(parents=True)
        filename = ""
        if self.folder:
            filename += self.folder.replace("/", "_") + "_"
        mainparam, *paramvalues = paramvalues
        filename += mainparam + "_"
        filename += self.endpoint.replace("-", "_")
        if paramvalues:
            filename += f"_{'_'.join(paramvalues)}"
        if optparamvalues:
            filename += f"_{'_'.join([*optparamvalues.values()])}"
        filename += ".json"

        return destdir / filename

    def retrieve(self, *paramvalues: str,   # override
                 dumpdest: Optional[Path] = None, **optparamvalues: str) -> Union[Json, List[Json]]:
        """Retrieve data from this endpoint.

        Similar to this module's 'endpoint_retrieve()'.
        """
        # validation
        self._validate_paramvalues(*paramvalues)
        self._validate_optparamvalues(**optparamvalues)

        mainvalue, *paramvalues = paramvalues
        url = self.url[:-(len(self.endpoint) + 1)]
        url += f"/{mainvalue}/{self.endpoint}"
        if paramvalues:
            url += f"/{'/'.join(paramvalues)}"
        if optparamvalues and self.optparams_in_url:
            url += f"/{'/'.join([*optparamvalues.values()])}"

        print(f"Retrieving data from '{url}'...")
        with Timer() as t:
            if self.optparams_in_url:
                response = requests.request("GET", url, headers=self.HEADERS_MAP)
            else:
                response = requests.request("GET", url, headers=self.HEADERS_MAP,
                                            params=optparamvalues)

        print(f"Request completed in {t.elapsed} seconds.")
        data = json.loads(response.text)

        if dumpdest is not None:
            with dumpdest.open(mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        return data


def get_endpoint(endpoints: List[ApiEndpoint], name: str,
                 folder: Optional[str] = None,
                 paramscount: Optional[int] = None) -> Optional[ApiEndpoint]:
    if folder is not None and paramscount is not None:
        return next((e for e in endpoints if e.endpoint == name and e.folder == folder
                     and len(e.params) == paramscount), None)
    elif folder is not None and paramscount is None:
        return next((e for e in endpoints if e.endpoint == name and e.folder == folder), None)
    elif folder is None and paramscount is not None:
        return next((e for e in endpoints if e.endpoint == name
                     and len(e.params) == paramscount), None)
    return next((e for e in endpoints if e.endpoint == name), None)
