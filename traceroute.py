from dataclasses import dataclass
import sys
from abc import ABC, abstractmethod
from time import time
from typing import Callable, TypeVar


from scapy.layers.inet import ICMP, IP
from scapy.route import Route
from scapy.sendrecv import sr1

SAMPLES_PER_TTL = 2**5
MAX_TTL = 2**5

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


class NoResponse(RouteResponse):
    def get_segment_time(self) -> float:
        return 0

    def __repr__(self) -> str:
        return "sin respuesta"


@dataclass
class RouterResponse(RouteResponse):
    ip: str
    segment_time: float

    def __repr__(self) -> str:
        return f"({self.ip}, {self.segment_time})"

    def get_segment_time(self) -> float:
        return self.segment_time

    @classmethod
    def from_route(cls, ip: IPAddress, total_time: float, route: "TTLRoute") -> Route:
        return cls(
            ip, total_time - sum(response.get_segment_time() for response in route)
        )


TTLRoute = list[RouteResponse]


def traceroute(dst_ip: IPAddress, max_ttl: int = MAX_TTL) -> TTLRoute:
    route: TTLRoute = [RouterResponse(IP().src, 0)]

    for ttl in range(1, max_ttl):
        probe = IP(dst=dst_ip, ttl=ttl) / ICMP()  # echo-request por defecto
        res, rtt = timeit(lambda: sr1(probe, verbose=False, timeout=0.1))

        if res is None:
            route.append(NoResponse())
            continue

        route.append(RouterResponse.from_route(res.src, rtt, route))

        # llegamos al destino
        if res.src == dst_ip:
            break

    return route


def sample_routes(
    dst_ip: IPAddress, *, samples_per_ttl: int = SAMPLES_PER_TTL
) -> list[TTLRoute]:
    """
    Retorna una lista de presuntas rutas por la cual viajó el paquete de ping.

    Cada ruta tiene un objecto RouteResponse por valor de TTL:
    - NoResponse si se cortó por timeout
    - RouterResponse si respondieron con TTLTimeExceeded
    """
    routes = []

    for _ in range(samples_per_ttl):
        routes.append(traceroute(dst_ip))

    return routes


if __name__ == "__main__":
    routers = sample_routes(sys.argv[1])
    print(routers)
    # print(f'total rtt: {sum(map(lambda x: x.segment_time, routers[0]))}')
