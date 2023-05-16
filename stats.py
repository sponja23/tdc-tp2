from collections import Counter
from traceroute import NoResponse, RouteSamples, RouterResponse, TTLRoute


def filter_only_responses(route: TTLRoute) -> TTLRoute:
    """
    Retorna una ruta que descarta los NoResponse.
    """
    return [response for response in route if not isinstance(response, NoResponse)]


def number_no_responses(route: TTLRoute) -> int:
    """
    Retorna la cantidad de NoResponse en una ruta.
    """
    return len(route) - len(filter_only_responses(route))


def router_response_count(route: TTLRoute) -> int:
    """
    Retorna la longitud de una ruta sin contar los NoResponse.
    """
    return len(filter_only_responses(route))


def average_length(route_samples: RouteSamples) -> float:
    """
    Retorna el largo promedio de una lista de rutas (sin contar los NoResponse).
    """
    return sum(router_response_count(route) for route in route_samples) / len(
        route_samples
    )


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

        average_rtt_time = (
            sum(
                response.rtt_time
                for response in ttl_responses
                if isinstance(response, RouterResponse)
                and response.ip == most_common_ip
            )
            / num_pkts_with_ip
        )

        average_route.append(
            RouterResponse(most_common_ip, average_segment_time, average_rtt_time)
        )

    return average_route


def number_of_negative_ttls(route: TTLRoute) -> int:
    """
    Devuelve la cantidad de TTLs negativos en una ruta.
    """

    return sum(
        isinstance(response, RouterResponse) and response.segment_time == 0
        for response in route
    )


def get_valid_segment_times_for_ttl(
    route_samples: RouteSamples, ttl: int
) -> list[float]:
    """
    Devuelve una lista con los RTT de los paquetes que llegaron al TTL dado.
    """
    return [
        response.get_segment_time()
        for route in route_samples
        if (response := route[ttl - 1]).get_segment_time() > 0
    ]
