from matplotlib.axes import Axes
import numpy as np
from stats import modified_thompson_tau
from traceroute import RouterResponse, TTLRoute


def grafico_deteccion_outliers(
    destination: str,
    route: TTLRoute,
    *,
    ax: Axes,
    manual_threshold: float | None = None,
) -> None:
    valid_responses = [
        response for response in route[1:] if isinstance(response, RouterResponse)
    ]

    ttls = np.array([response.ttl for response in valid_responses])

    segment_times = np.array(
        [
            response.segment_time * 1000
            for response in valid_responses
            if response.segment_time > 0
        ]
    )

    tau_threshold = modified_thompson_tau(len(segment_times)) * np.std(
        segment_times
    ) + np.mean(segment_times)

    # Agrego los segment_times negativos como 0
    segment_times = np.array(
        [max(0, response.segment_time) * 1000 for response in valid_responses]
    )

    def get_color(segment_time: float) -> str:
        if manual_threshold is not None and segment_time > manual_threshold:
            return "red"
        elif segment_time > tau_threshold:
            return "orange"
        elif segment_time > 0:
            return "blue"
        else:
            return "black"

    ax.scatter(
        ttls,
        segment_times,
        color=[get_color(segment_time) for segment_time in segment_times],
    )

    ax.axhline(
        tau_threshold,
        color="orange",
        linestyle="--",
        label="Umbral de outliers (Thompson)",
    )

    if manual_threshold is not None:
        ax.axhline(
            manual_threshold,
            color="red",
            linestyle="--",
            label="Umbral de outliers (manual)",
        )

    ax.set_xticks(ttls)
    ax.set_xlabel("TTL")

    ax.set_ylabel("Tiempo de respuesta ($ms$)")

    ax.set_title(f"Detección de outliers en ruta a {destination}")
