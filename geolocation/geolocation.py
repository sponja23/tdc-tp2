import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString


from geolocation.api import GeolocationAPIClient, WorldCoordinates, get_my_ip
from traceroute import (
    RouterResponse,
    TTLRoute,
)


def geolocate_route(
    route: TTLRoute, api_client: GeolocationAPIClient
) -> list[WorldCoordinates]:
    assert len(route) > 2, "La ruta es demasiado corta"

    assert route[0].is_localhost(), "La ruta no comienza en localhost"
    assert route[1].is_private(), "La ruta no comienza en una IP privada"

    route[1] = RouterResponse(get_my_ip(), route[1].get_segment_time())

    # TODO: Detectar las IPs privadas automáticamente
    return [
        api_client.get_ip_location(response.ip)
        for response in route[1:]  # El primero es localhost
        if isinstance(response, RouterResponse)  # TODO (capaz): Manejar NoResponse
    ]


def plot_route(route_coordinates: list[WorldCoordinates], ax: plt.Axes) -> None:
    route_line = LineString(
        [(point.longitude, point.latitude) for point in route_coordinates]
    )

    gpd.GeoSeries(route_line).plot(ax=ax, color="red")
