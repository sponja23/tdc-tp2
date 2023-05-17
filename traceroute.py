import pickle
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
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


@dataclass(frozen=True)
class RouteResponse(ABC):
    ttl: int

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
    rtt_time: float

    def __repr__(self) -> str:
        # Lo comento porque me tira excepción
        # domain = getnameinfo((self.ip, 0), 0)[0]
        # domain_text = f" ({domain})" if domain != self.ip else ""
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
    route: TTLRoute = [RouterResponse(ttl=0, ip=IP().src, segment_time=0, rtt_time=0)]
    last_rtt = 0.0

    for ttl in tqdm(range(1, max_ttl + 1), desc="Midiendo TTLs"):
        res, rtt = echo_request(dst_ip, ttl, timeout=timeout)

        if res is None:
            route.append(NoResponse(ttl=ttl))
            continue

        rtt_diff = rtt - last_rtt

        # Consigna:
        # > Tener en cuenta que esta resta puede dar un número negativo,
        # > en este caso se puede obviar el cálculo de RTT entre saltos y
        # > calcularlo con el próximo salto que de positivo.

        if rtt_diff > 0:
            last_rtt = rtt

        route.append(
            RouterResponse(ttl=ttl, ip=res.src, segment_time=rtt_diff, rtt_time=rtt)
        )

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


traceroute_parser = ArgumentParser()
traceroute_parser.add_argument("ip", help="IP destino")
traceroute_parser.add_argument(
    "--samples", type=int, default=SAMPLES_PER_TTL, help="Cantidad de muestras"
)
traceroute_parser.add_argument(
    "--max-ttl", type=int, default=MAX_TTL, help="TTL máximo para traceroute"
)
traceroute_parser.add_argument(
    "--timeout", type=float, default=1, help="Timeout para cada paquete"
)


def sample_route_from_args(args: Namespace) -> RouteSamples:
    return sample_routes(
        args.ip,
        samples_per_ttl=args.samples,
        max_ttl=args.max_ttl,
        timeout=args.timeout,
    )


def load_samples(path: str) -> RouteSamples:
    with open(path, "rb") as pkl:
        return pickle.load(pkl)


if __name__ == "__main__":
    traceroute_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path a donde guardar los samples",
    )

    args = traceroute_parser.parse_args()
    samples = sample_route_from_args(args)

    if args.output is not None:
        with open(args.output, "wb") as pkl:
            pickle.dump(samples, pkl, pickle.HIGHEST_PROTOCOL)

    pprint(samples)
