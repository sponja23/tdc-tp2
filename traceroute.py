from abc import ABC
import sys
from scapy.all import *
from time import time
from typing import List

SAMPLES_PER_TTL = 1#2**5
MAX_TTL = 2**5

def timeit(f):
    start_time = time()
    ret = f()
    end_time = time()
    return (ret, end_time - start_time)

class RouteResponse(ABC):
    segment_time: float
    pass

class NoResponse(RouteResponse):
    segment_time = 0

    def __repr__(self) -> str:
        return 'sin respuesta'

class RouterResponse(RouteResponse):
    ip: string

    def __init__(self, ip: string, segment_time: float) -> None:
        self.ip = ip
        self.segment_time = segment_time

    def __repr__(self) -> str:
        return f'({self.ip}, {self.segment_time})'
    
    @staticmethod
    def from_route(ip: string, total_time: float, route: List[Route]) -> Route:
        return RouterResponse(ip, total_time - sum(map(lambda x: x.segment_time, route)))

def gather_samples(dst_ip):
    route = [RouterResponse(IP().src, 0)]

    for ttl in range(1, MAX_TTL):
        probe = IP(dst=dst_ip, ttl=ttl) / ICMP() # echo-request por defecto
        (res, rtt) = timeit(lambda: sr1(probe, verbose=False, timeout=0.1))
        
        if res is None: 
            route.append(NoResponse())
            continue

        route.append(RouterResponse.from_route(res.src, rtt, route))

        # llegamos al destino
        if res.src == dst_ip: break

    return route

# Retorna una lista de presuntas rutas por la cual viajo el paquete de ping.
# Cada ruta tiene un objecto RouteResponse por valor de TTL: 
# - NoResponse si se corto por timeout 
# - RouterResponse si respondieron con TTLTimeExceeded
def traceroute(dst_ip):
    routes = []

    for _ in range(SAMPLES_PER_TTL):
        routes.append(gather_samples(dst_ip))

    return routes

if __name__ == '__main__':
    routers = traceroute(sys.argv[1])
    print(routers)
    #print(f'total rtt: {sum(map(lambda x: x.segment_time, routers[0]))}')