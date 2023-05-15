import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import getcwd
from os.path import dirname, realpath
from pathlib import Path
from typing import Any, Mapping, Type

import requests
from dotenv import load_dotenv

from traceroute import IPAddress


# Cargo las API keys
load_dotenv()


__location__ = realpath(Path(getcwd()) / dirname(__file__))

CACHE_DIRECTORY = Path(__location__) / ".cache"
if not CACHE_DIRECTORY.exists():
    CACHE_DIRECTORY.mkdir()


def get_my_ip() -> IPAddress:
    response = requests.get("https://api.ipify.org")
    response.raise_for_status()
    return response.text


@dataclass(frozen=True)
class WorldCoordinates:
    latitude: float
    longitude: float


class GeolocationAPIClient(ABC):
    clients: dict[str, Type["GeolocationAPIClient"]] = {}

    def __init_subclass__(cls) -> None:
        if hasattr(cls, "name"):  # Sólo las subclases concretas tienen nombre
            cls.clients[cls.name] = cls

    @staticmethod
    def get_client(name: str, *args: Any, **kwargs: Any) -> "GeolocationAPIClient":
        """El mismísimo canHandle"""
        return GeolocationAPIClient.clients[name](*args, **kwargs)

    @abstractmethod
    def get_ip_location(self, ip: IPAddress) -> WorldCoordinates:
        ...


class JSONGeolocationAPIClient(GeolocationAPIClient):
    @abstractmethod
    def get_url(self, ip: IPAddress) -> str:
        ...

    def get_location_from_json_response(
        self, response: Mapping[str, Any]
    ) -> WorldCoordinates:
        return WorldCoordinates(response["latitude"], response["longitude"])

    def get_location_from_request(self, ip: IPAddress) -> WorldCoordinates:
        response = requests.get(self.get_url(ip))
        response.raise_for_status()
        data = response.json()
        return self.get_location_from_json_response(data)


class DazzlePodClient(JSONGeolocationAPIClient):
    name = "dazzlepod"

    def get_url(self, ip: IPAddress) -> str:
        return f"https://dazzlepod.com/ip/{ip}.json"

    def get_ip_location(self, ip: IPAddress) -> WorldCoordinates:
        return self.get_location_from_request(ip)


class CachedGeolocationAPIClient(GeolocationAPIClient):
    def __init__(self) -> None:
        if not self.get_cache_path().exists():
            self.cache = {}
            self.save_cache()
        else:
            with open(self.get_cache_path(), "r") as cache_file:
                self.cache = json.load(cache_file)

    @classmethod
    def get_cache_path(cls) -> Path:
        assert hasattr(cls, "name")
        return CACHE_DIRECTORY / f"{cls.name}.json"

    def save_cache(self) -> None:
        with open(self.get_cache_path(), "w") as cache_file:
            json.dump(self.cache, cache_file)

    def get_ip_location(self, ip: IPAddress) -> WorldCoordinates:
        if ip not in self.cache:
            coordinates = self.get_uncached_ip_location(ip)
            self.cache[ip] = [coordinates.latitude, coordinates.longitude]
            self.save_cache()
        latitude, longitude = self.cache[ip]
        return WorldCoordinates(latitude, longitude)

    @abstractmethod
    def get_uncached_ip_location(self, ip: IPAddress) -> WorldCoordinates:
        ...


# Cuidado con la multiple inheritance!!!
class IPGeolocationIOClient(CachedGeolocationAPIClient, JSONGeolocationAPIClient):
    """
    Estoy limitado a 30k requests por mes y 1k por día.

    https://ipgeolocation.io/documentation/ip-geolocation-api.html#introduction
    """

    name = "ipgeolocationio"

    def __init__(self, api_key: str = os.environ["IPGEOLOCATIONIO_KEY"]) -> None:
        super().__init__()
        self.api_key = api_key

    def get_url(self, ip: IPAddress) -> str:
        return f"https://api.ipgeolocation.io/ipgeo?apiKey={self.api_key}&ip={ip}"

    def get_uncached_ip_location(self, ip: IPAddress) -> WorldCoordinates:
        return self.get_location_from_request(ip)
