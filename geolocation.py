from dataclasses import dataclass
from pprint import pprint

import requests
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from traceroute import (
    traceroute_parser,
    IPAddress,
    RouterResponse,
    TTLRoute,
    average_route,
    sample_routes,
)


def get_ip_location(ip: IPAddress) -> tuple[float, float]:
    response = requests.get(f"https://dazzlepod.com/ip/{ip}.json")
    response.raise_for_status()
    data = response.json()
    return (data["latitude"], data["longitude"])


def get_my_ip() -> IPAddress:
    response = requests.get("https://api.ipify.org")
    response.raise_for_status()
    return response.text


@dataclass
class WorldCoordinates:
    latitude: float
    longitude: float

    @classmethod
    def from_ip(cls, ip: IPAddress) -> "WorldCoordinates":
        return cls(*get_ip_location(ip))


def geolocate_route(route: TTLRoute) -> list[WorldCoordinates]:
    assert len(route) > 2, "La ruta es demasiado corta"

    assert route[0].is_localhost(), "La ruta no comienza en localhost"
    assert route[1].is_private(), "La ruta no comienza en una IP privada"

    route[1] = RouterResponse(get_my_ip(), route[1].get_segment_time())

    # TODO: Detectar las IPs privadas automáticamente
    return [
        WorldCoordinates.from_ip(response.ip)
        for response in route[1:]  # El primero es localhost, el segundo es el router
        if isinstance(response, RouterResponse)  # TODO (capaz): Manejar NoResponse
    ]


def plot_route(route: TTLRoute, ax: plt.Axes) -> None:
    route_path = geolocate_route(route)
    route_line = LineString([(point.longitude, point.latitude) for point in route_path])

    gpd.GeoSeries(route_line).plot(ax=ax, color="red")


if __name__ == "__main__":
    args = traceroute_parser.parse_args()

    samples = sample_routes(args.ip, samples_per_ttl=args.samples, max_ttl=args.max_ttl)
    route = average_route(samples)

    pprint(route)

    my_ip = get_my_ip()

    fig, ax = plt.subplots()
    plot_route(route, ax)

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world.plot(ax=ax, color="white", edgecolor="black")

    ax.set_title(f"Geolocalización de ruta desde {my_ip} hasta {args.ip}")

    plt.show()
