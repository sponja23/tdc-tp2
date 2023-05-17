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
    assert route[1].is_private(), "La ruta no comienza en una IP privada"

    if route[0].is_localhost():
        route = route[1:]

    route[0] = RouterResponse(
        ttl=1,
        ip=get_my_ip(),
        segment_time=route[0].get_segment_time(),
        rtt_time=route[0].rtt_time if isinstance(route[0], RouterResponse) else 0,
    )

    return [
        api_client.get_ip_location(response.ip)
        for response in tqdm(route, desc="Geolocalizando ruta")
        if isinstance(response, RouterResponse)  # TODO (capaz): Manejar NoResponse
    ]


class Cluster:
    def __init__(self) -> None:
        self.points: list[WorldCoordinates] = []
        self.indices: list[int] = []

    def add_point(self, point: WorldCoordinates, index: int) -> None:
        self.points.append(point)
        self.indices.append(index)

    def should_add_point(self, point: WorldCoordinates, tol: float) -> bool:
        return all(
            point.distance_from(other_point) < tol for other_point in self.points
        )

    @property
    def center(self) -> WorldCoordinates:
        """
        Asumo que las coordenadas están cerca, así que trato
        a la tierra como si fuera plana.
        """

        return WorldCoordinates(
            latitude=sum(point.latitude for point in self.points) / len(self.points),
            longitude=sum(point.longitude for point in self.points) / len(self.points),
        )


def get_point_clusters(
    route_coordinates: list[WorldCoordinates], tol: float = 100.0
) -> list[Cluster]:
    """
    Devuelve los índices de los puntos que forman clusters de radio tol.
    """

    # Estrategia greedy: se toma el primer punto y se van agregando los que están a
    # distancia tol de él. No es correcta pero nuestros clusters están muy marcados.
    clusters: list[Cluster] = []
    for i, point in enumerate(route_coordinates):
        for cluster in clusters:
            if cluster.should_add_point(point, tol):
                cluster.add_point(point, i)
                break
        else:
            cluster = Cluster()
            cluster.add_point(point, i)
            clusters.append(cluster)

    return clusters


def plot_route(route_coordinates: list[WorldCoordinates], ax: plt.Axes) -> None:
    route_line = LineString(
        [(point.longitude, point.latitude) for point in route_coordinates]
    )

    gpd.GeoSeries(route_line).plot(ax=ax, color="red")


def plot_route_clusters(
    route_coordinates: list[WorldCoordinates], index_to_ttl: list[int], ax: plt.Axes
) -> None:
    clusters = get_point_clusters(route_coordinates)

    for cluster in clusters:
        ax.annotate(
            ",".join(f"\\textbf{{{index_to_ttl[index]}}}" for index in cluster.indices),
            xy=(cluster.center.longitude, cluster.center.latitude),
            ha="left",
            va="bottom",
            color="red",
            size=8,
        )
