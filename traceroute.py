from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from collections import Counter
from dataclasses import dataclass
from pprint import pprint
from time import time
from typing import Any, Callable, TypeVar

from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import sr1
from tqdm import tqdm

SAMPLES_PER_TTL = 2**5
MAX_TTL = 2**6

IPAddress = str


T = TypeVar("T")


def timeit(f: Callable[[], T]) -> tuple[T, float]:
    start_time = time()
    ret = f()
    end_time = time()
    return (ret, end_time - start_time)


class RouteResponse(ABC):
    @abstractmethod
    def get_segment_time(self) -> float:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def is_localhost(self) -> bool:
        pass

    @abstractmethod
    def is_private(self) -> bool:
        pass


class NoResponse(RouteResponse):
    def get_segment_time(self) -> float:
        return 0

    def __repr__(self) -> str:
        return "sin respuesta"

    def is_localhost(self) -> bool:
        return False

    def is_private(self) -> bool:
        return False


@dataclass(frozen=True)
class RouterResponse(RouteResponse):
    ip: str
    segment_time: float

    def __repr__(self) -> str:
        return f"({self.ip}, {self.segment_time})"

    def get_segment_time(self) -> float:
        return self.segment_time

    def is_localhost(self) -> bool:
        return self.ip.startswith("127")

    def is_private(self) -> bool:
        return self.ip.startswith("192.168")


TTLRoute = list[RouteResponse]


def echo_request(dst_ip: IPAddress, ttl: int, timeout: float) -> tuple[Any, float]:
    """Envía un Echo-Request y mide el RTT en ms"""
    probe = IP(dst=dst_ip, ttl=ttl) / ICMP()
    return timeit(lambda: sr1(probe, verbose=False, timeout=1))


def traceroute(
    dst_ip: IPAddress, max_ttl: int = MAX_TTL, timeout: float = 1
) -> TTLRoute:
    """Retorna una lista de RouteResponse con los TTLs de la ruta al destino"""
    route: TTLRoute = [RouterResponse(IP().src, 0)]

    for ttl in tqdm(range(1, max_ttl + 1), desc="Midiendo TTLs"):
        res, rtt = echo_request(dst_ip, ttl, timeout=timeout)

        if res is None:
            route.append(NoResponse())
            continue

        rtt_diff = rtt - sum(response.get_segment_time() for response in route)

        route.append(RouterResponse(ip=res.src, segment_time=rtt_diff))

        # llegamos al destino
        if res.src == dst_ip:
            return route

    raise Exception("No se llegó al destino")


RouteSamples = list[TTLRoute]


def sample_routes(
    dst_ip: IPAddress,
    *,
    samples_per_ttl: int = SAMPLES_PER_TTL,
    max_ttl: int = MAX_TTL,
    timeout: float = 1,
) -> RouteSamples:
    """
    Retorna una lista de presuntas rutas por la cual viajó el paquete de ping.

    Cada ruta tiene un objecto RouteResponse por valor de TTL:
    - NoResponse si se cortó por timeout
    - RouterResponse si respondieron con TTLTimeExceeded
    """
    routes = []

    for _ in tqdm(range(samples_per_ttl), desc="Midiendo rutas"):
        routes.append(traceroute(dst_ip, max_ttl=max_ttl, timeout=timeout))

    return routes


def average_route(route_samples: RouteSamples) -> TTLRoute:
    """
    Retorna la ruta promedio de una lista de rutas.

    La ruta promedio es una lista de RouterResponse, donde cada RouterResponse
    tiene como ip la ip más frecuente de las respuestas para ese TTL, y como
    segment_time el promedio de los segment_time de las respuestas para esa IP.
    """
    average_route: TTLRoute = []

    most_common_distance, _ = Counter(
        len(route) for route in route_samples if not isinstance(route[-1], NoResponse)
    ).most_common(1)[0]

    # Nos quedamos solo con las rutas de la misma distancia
    route_samples = [
        route for route in route_samples if len(route) == most_common_distance
    ]

    for ttl_responses in zip(*route_samples):
        if all(isinstance(response, NoResponse) for response in ttl_responses):
            average_route.append(NoResponse())
            continue

        most_common_ip, num_pkts_with_ip = Counter(
            response.ip
            for response in ttl_responses
            if isinstance(response, RouterResponse)
        ).most_common(1)[0]

        average_segment_time = (
            sum(
                response.get_segment_time()
                for response in ttl_responses
                if isinstance(response, RouterResponse)
                and response.ip == most_common_ip
            )
            / num_pkts_with_ip
        )

        average_route.append(RouterResponse(most_common_ip, average_segment_time))

    return average_route


traceroute_parser = ArgumentParser()
traceroute_parser.add_argument("ip", help="IP a geolocalizar")
traceroute_parser.add_argument(
    "--samples", type=int, default=SAMPLES_PER_TTL, help="Cantidad de muestras"
)
traceroute_parser.add_argument(
    "--max-ttl", type=int, default=MAX_TTL, help="TTL máximo para traceroute"
)
traceroute_parser.add_argument(
    "--timeout", type=float, default=1, help="Timeout para cada paquete"
)


def average_route_from_args(args: Namespace) -> TTLRoute:
    routes = sample_routes(
        args.ip,
        samples_per_ttl=args.samples,
        max_ttl=args.max_ttl,
        timeout=args.timeout,
    )

    return average_route(routes)


if __name__ == "__main__":
    args = traceroute_parser.parse_args()
    pprint(average_route_from_args(args))
