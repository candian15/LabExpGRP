"""Gera os dados simulados a partir do config/cenario.yaml."""
from pathlib import Path

import numpy as np
import yaml

CAMINHO_CENARIO = Path(__file__).resolve().parent.parent / "config" / "cenario.yaml"


def ler_cenario(caminho=CAMINHO_CENARIO):
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def gerar_grupos(cenario, rng=None, n=None):
    """Gera um conjunto simulado: um array por grupo (lognormal com mu e sigma do cenário)."""
    if rng is None:
        rng = np.random.default_rng(cenario["semente"])
    if n is None:
        n = cenario["n_por_grupo"]
    grupos = {}
    for nome, p in cenario["grupos"].items():
        grupos[nome] = rng.lognormal(mean=p["mu"], sigma=p["sigma"], size=n)
    return grupos


if __name__ == "__main__":
    cenario = ler_cenario()
    for nome, dados in gerar_grupos(cenario).items():
        print(f"{nome}: n={len(dados)}, mediana={np.median(dados):.1f} h, media={dados.mean():.1f} h")
