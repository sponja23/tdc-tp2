import os

import dotenv
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from tqdm import tqdm

from geolocation.api import GeolocationAPIClient, WorldCoordinates, get_my_ip
from traceroute import (
    RouterResponse,
    TTLRoute,
)

dotenv.load_dotenv()


def geolocate_route(
    route: TTLRoute, api_client: GeolocationAPIClient
) -> list[WorldCoordinates]:
    assert len(route) > 2, "La ruta es demasiado corta"

    assert route[0].is_localhost(), "La ruta no comienza en localhost"
    assert route[1].is_private(), "La ruta no comienza en una IP privada"

    route[1] = RouterResponse(
        os.environ.get("MY_IP") or get_my_ip(), route[1].get_segment_time()
    )

    return [
        api_client.get_ip_location(response.ip)
        for response in tqdm(route[1:], desc="Geolocalizando ruta")
        if isinstance(response, RouterResponse)  # TODO (capaz): Manejar NoResponse
    ]


def plot_route(
    route: TTLRoute, route_coordinates: list[WorldCoordinates], ax: plt.Axes
) -> None:
    route_line = LineString(
        [(point.longitude, point.latitude) for point in route_coordinates]
    )

    # TODO: Evitar que se superpongan los labels
    for response, x, y in zip(route[1:], *route_line.xy):
        if isinstance(response, RouterResponse):
            ax.annotate(
                response.ip,
                xy=(x, y),
                ha="center",
                va="center",
                size=8,
            )

    gpd.GeoSeries(route_line).plot(ax=ax, color="red")
