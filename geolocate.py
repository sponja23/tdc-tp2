#!/usr/bin/env python3
"""
Separé esto de lo demás porque python es un idiota con los imports
"""

from pprint import pprint
from matplotlib import pyplot as plt
from geolocation.api import GeolocationAPIClient, get_my_ip
from geolocation.geolocation import geolocate_route, plot_route
import geopandas as gpd
from traceroute import average_route_from_args, traceroute_parser


if __name__ == "__main__":
    traceroute_parser.add_argument(
        "--api-client",
        default="dazzlepod",
        help="Cliente de geolocalización a usar",
        choices=GeolocationAPIClient.clients.keys(),
    )

    args = traceroute_parser.parse_args()
    route = average_route_from_args(args)
    pprint(route)

    my_ip = get_my_ip()

    fig, ax = plt.subplots()

    api_client = GeolocationAPIClient.get_client(args.api_client)
    route_coordinates = geolocate_route(route, api_client)

    plot_route(route_coordinates, ax)

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world.plot(ax=ax, color="white", edgecolor="black")

    ax.set_title(f"Geolocalización de ruta desde {my_ip} hasta {args.ip}")

    plt.show()
