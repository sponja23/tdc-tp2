import numpy as np
from figures.latex import (
    destination_2_latex,
    number_2_latex,
    latex_table,
    ratio_2_latex,
)
from figures.destinations import DestinationSamples, get_destination_samples
from stats import router_response_count


def tabla_cantidad_respuestas(destination_samples: DestinationSamples) -> str:
    return latex_table(
        {
            r"\textbf{Destino}": map(destination_2_latex, destination_samples.keys()),
            r"\textbf{Proporción de Respuestas}": map(
                ratio_2_latex,
                [
                    np.mean(
                        [router_response_count(route) / len(route) for route in samples]
                    )
                    for samples in destination_samples.values()
                ],
            ),
            r"\textbf{Cantidad Promedio de Respuestas}": map(
                number_2_latex,
                [
                    np.mean([router_response_count(route) for route in samples])
                    for samples in destination_samples.values()
                ],
            ),
        }
    )


if __name__ == "__main__":
    print(tabla_cantidad_respuestas(get_destination_samples()))
