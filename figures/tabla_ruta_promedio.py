from figures.latex import (
    int_2_latex,
    ip_2_latex,
    latex_table,
    seconds_2_latex,
)
from stats import average_route, filter_only_responses
from traceroute import RouteSamples


def tabla_ruta_promedio(
    samples: RouteSamples,
) -> str:
    route = average_route(samples)

    filtered_route = filter_only_responses(route)

    filtered_route = filtered_route[1:]  # Drop localhost

    return latex_table(
        {
            "TTL": [int_2_latex(response.ttl) for response in filtered_route],
            "IP": [ip_2_latex(response.ip) for response in filtered_route],
            "Tiempo de enlace": [
                seconds_2_latex(response.segment_time, in_ms=True)
                for response in filtered_route
            ],
            "Tiempo de RTT": [
                seconds_2_latex(response.rtt_time, in_ms=True)
                for response in filtered_route
            ],
        }
    )
