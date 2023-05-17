#!/usr/bin/env python3
"""
Separé esto de lo demás porque python es un idiota con los imports
"""

from pprint import pprint
from socket import inet_aton

import geopandas as gpd
import seaborn as sns
from matplotlib import pyplot as plt

from geolocation.api import GeolocationAPIClient, get_my_ip
from geolocation.geolocation import geolocate_route, plot_route, plot_route_clusters
from stats import average_route
from traceroute import (  # noqa: F401
    NoResponse,  # noqa: F401
    RouteResponse,  # noqa: F401
    RouterResponse,  # noqa: F401
    load_samples,
    sample_route_from_args,
    traceroute_parser,
)

sns.set(
    rc={"text.usetex": True, "font.family": "serif", "font.serif": "Computer Modern"}
)


def is_valid_ip(ip: str) -> bool:
    try:
        inet_aton(ip)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    traceroute_parser.add_argument(
        "--api",
        default="dazzlepod",
        help="Cliente de geolocalización a usar",
        choices=GeolocationAPIClient.clients.keys(),
    )

    traceroute_parser.add_argument(
        "--output",
        "-o",
        help="Archivo donde guardar el mapa generado",
        type=str,
        default=None,
    )

    traceroute_parser.add_argument(
        "--dont-show",
        help="No mostrar el mapa generado",
        action="store_true",
        default=False,
    )

    args = traceroute_parser.parse_args()

    if is_valid_ip(args.ip):
        samples = sample_route_from_args(args)
    else:  # Se asume que es un path
        samples = load_samples(f"samples/{args.ip}.samples")

    route = average_route(samples)

    pprint(route)

    fig, ax = plt.subplots()

    api_client = GeolocationAPIClient.get_client(args.api)
    route_coordinates = geolocate_route(route, api_client)

    plot_route(route_coordinates, ax)

    plot_route_clusters(
        route_coordinates,
        [
            response.ttl
            for response in route[1:]
            if isinstance(response, RouterResponse)
        ],
        ax,
    )

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world.plot(ax=ax, color="white", edgecolor="black")

    ax.set_title(f"Geolocalización de ruta desde {get_my_ip()} hasta {args.ip}")

    if not args.dont_show:
        plt.show()

    if args.output:
        fig.savefig(args.output, format="pdf", bbox_inches='tight')
