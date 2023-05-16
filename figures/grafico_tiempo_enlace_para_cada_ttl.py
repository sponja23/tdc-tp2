from matplotlib.axes import Axes
import numpy as np
from stats import get_valid_segment_times_for_ttl
from traceroute import RouteSamples


def grafico_tiempo_enlace_para_cada_ttl(
    destination: str, samples: RouteSamples, *, ax: Axes
) -> None:
    ttls = range(1, len(samples[0]))

    valid_segment_times = [
        get_valid_segment_times_for_ttl(samples, ttl) for ttl in ttls
    ]

    # Esto solo tiene sentido cuando las rutas son iguales (o muy parecidas) entre sí
    # Por ejemplo, si una ruta tiene 1 salto más que las demás, va a generar outliers
    # en todos los hops que estén después de ese.
    # Me parece que eso se ve en el de Stanford
    ax.errorbar(
        x=ttls,
        y=[np.mean(segment_times) for segment_times in valid_segment_times],
        yerr=[np.std(segment_times) for segment_times in valid_segment_times],
        fmt="o",
    )

    ax.set_title(f"RTT promedio para cada TTL ({destination})")
