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


def int_2_latex(n: int) -> str:
    return f"${n}$"


def float_2_latex(n: float) -> str:
    return f"${n:.2f}$"


def ratio_2_latex(r: float) -> str:
    return f"${r*100:.2f}\\%$"


def seconds_2_latex(s: float, in_ms: bool = False) -> str:
    if in_ms:
        return f"${s*1000:.2f}ms$"
    else:
        return f"${s:.2f}s$"


def ip_2_latex(ip: str) -> str:
    return f"\\texttt{{{ip}}}"


def destination_2_latex(destination: str) -> str:
    # Capitalize first letter
    return f"\\textbf{{{destination[0].upper() + destination[1:]}}}"


def latex_column_name(name: str) -> str:
    return f"\\textbf{{{name}}}"


def latex_table(data: Mapping[str, Iterable[Any]]) -> str:
    """
    Arma una tabla de LaTeX usando los datos de data

    Las claves de data son los nombres de las columnas, y los valores son las
    filas.
    """
    tabular = pd.DataFrame(
        data={
            latex_column_name(column_name): rows for column_name, rows in data.items()
        }
    ).to_latex(index=False)

    return "\\begin{table}[H]\n\\centering\n" + tabular + "\\end{table}\n"
