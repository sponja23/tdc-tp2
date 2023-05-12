from dataclasses import dataclass
import sys

import requests
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from traceroute import IPAddress, RouterResponse, TTLRoute, traceroute


def get_ip_location(ip: IPAddress) -> tuple[float, float]:
    response = requests.get(f"https://dazzlepod.com/ip/{ip}.json")
    response.raise_for_status()
    data = response.json()
    return (data["latitude"], data["longitude"])


@dataclass
class WorldCoordinates:
    latitude: float
    longitude: float

    @classmethod
    def from_ip(cls, ip: IPAddress) -> "WorldCoordinates":
        return cls(*get_ip_location(ip))


def geolocate_route(route: TTLRoute) -> list[WorldCoordinates]:
    # TODO: Detectar las IPs privadas automáticamente
    return [
        WorldCoordinates.from_ip(response.ip)
        for response in route[2:]  # El primero es localhost, el segundo es el router
        if isinstance(response, RouterResponse)  # TODO (capaz): Manejar NoResponse
    ]


def plot_route(route: TTLRoute, ax: plt.Axes) -> None:
    route_path = geolocate_route(route)
    route_line = LineString([(point.longitude, point.latitude) for point in route_path])

    gpd.GeoSeries(route_line).plot(ax=ax, color="red")


if __name__ == "__main__":
    ip_addr = sys.argv[1]
    route = traceroute(ip_addr)

    fig, ax = plt.subplots()
    plot_route(route, ax)

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world.plot(ax=ax, color="white", edgecolor="black")

    ax.set_title(f"Geolocalización de ruta a {ip_addr}")

    plt.show()
