from typing import Any, Iterable, Mapping
import pandas as pd
import seaborn as sns


def latex_figure_preamble() -> None:
    """Deja a matplotlib lista para generar figuras lindas en LaTeX."""
    sns.set(
        rc={
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": "Computer Modern",
        }
    )


def number_2_latex(n: float) -> str:
    return f"${n:.2f}$"


def ratio_2_latex(r: float) -> str:
    return f"${r*100:.2f}\\%$"


def destination_2_latex(destination: str) -> str:
    # Capitalize first letter
    return f"\\textbf{{{destination[0].upper() + destination[1:]}}}"


def latex_table(data: Mapping[str, Iterable[Any]]) -> str:
    """
    Arma una tabla de LaTeX usando los datos de data

    Las claves de data son los nombres de las columnas, y los valores son las
    filas.
    """
    tabular = pd.DataFrame(data=data).to_latex(index=False)

    return "\\begin{table}[H]\n\\centering\n" + tabular + "\\end{table}\n"
