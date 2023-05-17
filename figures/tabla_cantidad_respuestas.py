import numpy as np
from figures.latex import (
    destination_2_latex,
    float_2_latex,
    int_2_latex,
    latex_table,
    ratio_2_latex,
)
from figures.destinations import DestinationSamples, get_destination_samples
from stats import drop_localhost, router_response_count


def tabla_cantidad_respuestas(destination_samples: DestinationSamples) -> str:
    destination_samples = {
        destination: drop_localhost(samples)
        for destination, samples in destination_samples.items()
    }

    return latex_table(
        {
            "Destino": map(destination_2_latex, destination_samples.keys()),
            "Proporción de Respuestas": map(
                ratio_2_latex,
                [
                    float(
                        np.mean(
                            [
                                router_response_count(route) / len(route)
                                for route in samples
                            ]
                        )
                    )
                    for samples in destination_samples.values()
                ],
            ),
            "Largo": map(
                int_2_latex,
                [len(samples[0]) for samples in destination_samples.values()],
            ),
            "Cantidad Promedio de Respuestas": map(
                float_2_latex,
                [
                    float(np.mean([router_response_count(route) for route in samples]))
                    for samples in destination_samples.values()
                ],
            ),
        }
    )


if __name__ == "__main__":
    print(tabla_cantidad_respuestas(get_destination_samples()))
