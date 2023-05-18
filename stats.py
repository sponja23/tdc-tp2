from collections import Counter

import numpy as np
import scipy.stats as stats

from traceroute import NoResponse, RouterResponse, RouteSamples, TTLRoute


def filter_only_responses(route: TTLRoute) -> list[RouterResponse]:
    """
    Retorna una ruta que descarta los NoResponse.
    """
    return [response for response in route if isinstance(response, RouterResponse)]


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

    most_common_length, _ = Counter(
        len(route) for route in route_samples if not isinstance(route[-1], NoResponse)
    ).most_common(1)[0]

    # Nos quedamos solo con las rutas de la misma distancia
    route_samples = [
        route for route in route_samples if len(route) == most_common_length
    ]

    for ttl, ttl_responses in enumerate(zip(*route_samples)):
        if all(isinstance(response, NoResponse) for response in ttl_responses):
            average_route.append(NoResponse(ttl=ttl))
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
            RouterResponse(
                ttl=ttl,
                ip=most_common_ip,
                segment_time=average_segment_time,
                rtt_time=average_rtt_time,
            )
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
        if (response := route[ttl]).get_segment_time() > 0
    ]


def drop_localhost(samples: RouteSamples) -> RouteSamples:
    """
    Devuelve una lista de rutas sin la primera respuesta de cada ruta, que
    corresponde a la respuesta del localhost.
    """

    assert all(route[0].is_localhost() for route in samples)

    return [route[1:] for route in samples]


def modified_thompson_tau(n: int) -> float:
    """
    Devuelve el valor de tau de Thompson para un tamaño de muestra dado.
    """
    t_student_critical_value = stats.t.pdf(x=0.05 / 2, df=n - 2)

    tau = (t_student_critical_value * (n - 1)) / (
        np.sqrt(n) * np.sqrt((n - 2 + t_student_critical_value**2))
    )

    return tau
