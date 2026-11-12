"""Aplica o t de Welch e o Mann-Whitney aos 60 PRs reais (seção 6 do dashboard).

Lê ``data/dados_reais.csv`` e compara o tempo até o merge (``horas_ate_merge``) do grupo
``com_bot`` com o do ``sem_bot``. A ordem é a mesma das simulações: o controle (``sem_bot``)
é o primeiro grupo, então efeito **positivo** (d de Cohen ou delta de Cliff) quer dizer que
os PRs sem bot demoram mais para ser mesclados.

Grava ``resultados/dados_reais.csv``, uma linha por teste, com estatística, p-valor,
tamanho do efeito, sua interpretação e a conclusão em palavras.

Uso (a partir de LAB04/):  python -m src.dados_reais
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacao import ler_cenario
from src.testes import ALFA, aplicar_testes

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data" / "dados_reais.csv"
SAIDA = RAIZ / "resultados" / "dados_reais.csv"

# Limites usuais para |efeito|: (Cohen, 1988) para o d; (Romano et al., 2006) para o delta.
LIMITES = {
    "d de Cohen": (0.2, 0.5, 0.8),
    "delta de Cliff": (0.147, 0.33, 0.474),
}
ROTULOS = ("desprezível", "pequeno", "médio", "grande")


def interpretar_efeito(nome_efeito: str, efeito: float) -> str:
    """Classifica |efeito| em desprezível, pequeno, médio ou grande."""
    a = abs(efeito)
    return ROTULOS[sum(a >= limite for limite in LIMITES[nome_efeito])]


def _p(p_valor: float) -> str:
    return "p < 0,001" if p_valor < 0.001 else f"p = {p_valor:.3f}".replace(".", ",")


def conclusao(r: dict, controle: str = "sem bot", tratamento: str = "com bot", alfa: float = ALFA) -> str:
    """Frase com a decisão do teste, o sentido da diferença e o tamanho do efeito."""
    forca = interpretar_efeito(r["nome_efeito"], r["efeito"])
    valor = f"{r['efeito']:+.2f}".replace(".", ",")
    if r["rejeita_h0"]:
        mais_lento = controle if r["efeito"] > 0 else tratamento
        return (f"Rejeita H₀ ({_p(r['p_valor'])}): o tempo até o merge difere entre os grupos, "
                f"e os PRs {mais_lento} demoram mais. Efeito {forca} ({r['nome_efeito']} = {valor}).")
    return (f"Não rejeita H₀ ({_p(r['p_valor'])}): sem evidência de diferença no tempo até o merge "
            f"a {alfa:.0%}. Efeito {forca} ({r['nome_efeito']} = {valor}).")


def testar_dados_reais(df: pd.DataFrame, controle="sem_bot", tratamento="com_bot",
                       col_valor="horas_ate_merge") -> pd.DataFrame:
    a = df.loc[df["grupo"] == controle, col_valor].to_numpy(dtype=float)
    b = df.loc[df["grupo"] == tratamento, col_valor].to_numpy(dtype=float)
    resultados = aplicar_testes(a, b)
    concordam = len({r["rejeita_h0"] for r in resultados}) == 1
    linhas = []
    for r in resultados:
        linhas.append({
            "teste": r["teste"],
            "n_sem_bot": len(a),
            "n_com_bot": len(b),
            "mediana_sem_bot_h": float(np.median(a)),
            "mediana_com_bot_h": float(np.median(b)),
            "estatistica": r["estatistica"],
            "p_valor": r["p_valor"],
            "nome_efeito": r["nome_efeito"],
            "efeito": r["efeito"],
            "interpretacao_efeito": interpretar_efeito(r["nome_efeito"], r["efeito"]),
            "rejeita_h0": r["rejeita_h0"],
            "testes_concordam": concordam,
            "conclusao": conclusao(r, controle.replace("_", " "), tratamento.replace("_", " ")),
        })
    return pd.DataFrame(linhas)


def main():
    cenario = ler_cenario()
    tabela = testar_dados_reais(pd.read_csv(DADOS), cenario["controle"], cenario["tratamento"])
    SAIDA.parent.mkdir(exist_ok=True)
    # 12 dígitos significativos: mais do que o suficiente para qualquer leitura daqui e
    # pouco o bastante para o arquivo não mudar por causa do último bit de um float. Sem
    # isso, o p-valor do Welch sai com o 17º dígito diferente de máquina para máquina e o
    # passo de reprodutibilidade do CI (`git diff --exit-code -- resultados`) acusa.
    tabela.to_csv(SAIDA, index=False, float_format="%.12g")
    for _, r in tabela.iterrows():
        print(f"{r['teste']}: estatística = {r['estatistica']:.3f}, p = {r['p_valor']:.4f}, "
              f"{r['nome_efeito']} = {r['efeito']:+.3f} ({r['interpretacao_efeito']})")
        print(f"  {r['conclusao']}")
    print("\nOs dois testes " + ("chegaram à mesma conclusão." if tabela["testes_concordam"].iloc[0]
                                  else "chegaram a conclusões diferentes."))


if __name__ == "__main__":
    main()
