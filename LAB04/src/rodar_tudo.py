"""Roda o Lab04 inteiro com um comando: as simulações e as quatro figuras.

    python -m src.rodar_tudo

Grava tudo o que está em ``resultados/`` e as figuras G1 a G4 em ``docs/``. Todas as
etapas usam a semente registrada no ``config/cenario.yaml``, então rodar duas vezes
produz exatamente os mesmos arquivos — é essa a reprodutibilidade que o enunciado pede.

Cada etapa é de um integrante e vive no módulo dele. Uma etapa cujo módulo ainda não
está no repositório aparece como PENDENTE e as outras continuam: assim o comando já
roda enquanto a sprint está pela metade, e passa a gerar o arquivo que falta no dia em
que o módulo entrar, sem precisar mexer aqui.

Sai com código 1 se alguma etapa quebrar; etapa pendente não é falha.
"""
from __future__ import annotations

import importlib
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent

OK, PENDENTE, ERRO = "ok", "pendente", "erro"


@dataclass(frozen=True)
class Etapa:
    """Um passo do pipeline: ou chama o ``main()`` de um módulo, ou uma função daqui."""

    nome: str
    de_quem: str
    saidas: tuple[str, ...]
    modulo: str | None = None
    acao: Callable[[], None] | None = None

    def executar(self) -> None:
        if self.acao is not None:
            self.acao()
        else:
            importlib.import_module(self.modulo).main()

    def pronta(self) -> bool:
        """Verdadeiro quando os arquivos da etapa já estão no repositório."""
        return all((RAIZ / s).is_file() for s in self.saidas)


def salvar_figuras() -> None:
    """G1 a G4 em docs/. O G1 tem o main() dele; os outros três saem daqui."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src import resultados
    from src.graficos import fig_g2, fig_g3, fig_g4
    from src.graficos_g1 import main as salvar_g1
    from src.simulacao import gerar_grupos, ler_cenario

    salvar_g1()

    cenario = ler_cenario()
    grupos = gerar_grupos(cenario)
    figuras = {
        "docs/g2_estatistica_sob_h0.png":
            fig_g2(grupos[cenario["controle"]], grupos[cenario["tratamento"]]),
    }

    taxas = resultados.ler_taxas()
    figuras["docs/g3_erro_tipo_i.png"] = fig_g3(taxas)
    figuras["docs/g4_curvas_de_poder.png"] = fig_g4(taxas)

    for caminho, fig in figuras.items():
        fig.savefig(RAIZ / caminho, dpi=150)
        plt.close(fig)
        print(f"gravado {caminho}")

    faltam = [s for s in resultados.ORDEM if s not in resultados.situacoes(taxas)]
    if faltam:
        print(f"  (o G3 e o G4 saíram só com o cenário real; faltam {', '.join(faltam)})")


ETAPAS: tuple[Etapa, ...] = (
    Etapa(nome="Q1 e Q2 — erro tipo I e poder no cenário real",
          de_quem="Pedro",
          saidas=("resultados/q1.csv", "resultados/q2.csv"),
          modulo="src.monte_carlo"),
    Etapa(nome="Q3 — as situações que violam os pressupostos",
          de_quem="Arthur",
          saidas=("resultados/q3.csv",),
          modulo="src.q3"),
    Etapa(nome="Os dois testes nos 60 PRs reais",
          de_quem="Arthur",
          saidas=("resultados/dados_reais.csv",),
          modulo="src.dados_reais"),
    Etapa(nome="Figuras G1 a G4",
          de_quem="João",
          saidas=("docs/g1_dados_reais_vs_simulados.png", "docs/g2_estatistica_sob_h0.png",
                  "docs/g3_erro_tipo_i.png", "docs/g4_curvas_de_poder.png"),
          acao=salvar_figuras),
    Etapa(nome="Página do dashboard publicado (GitHub Pages)",
          de_quem="João",
          saidas=("../index.html",),
          modulo="src.gerar_pagina"),
)


def rodar(etapa: Etapa) -> str:
    """Executa a etapa e devolve ok, pendente ou erro (já imprimindo o que aconteceu)."""
    print(f"\n>> {etapa.nome}  [{etapa.de_quem}]")
    try:
        etapa.executar()
    except ModuleNotFoundError as e:
        if e.name != etapa.modulo:  # faltou uma dependência de dentro do módulo
            traceback.print_exc()
            return ERRO
        if etapa.pronta():
            print(f"   {etapa.modulo}.py ainda não está no repositório, mas "
                  f"{', '.join(etapa.saidas)} já está commitado — mantido como está.")
            return OK
        print(f"   PENDENTE: falta {etapa.modulo.replace('.', '/')}.py ({etapa.de_quem}).")
        return PENDENTE
    except Exception:  # noqa: BLE001 - uma etapa quebrada não derruba as outras
        traceback.print_exc()
        return ERRO

    sumiu = [s for s in etapa.saidas if not (RAIZ / s).is_file()]
    if sumiu:
        print(f"   ERRO: a etapa rodou mas não gravou {', '.join(sumiu)}")
        return ERRO
    return OK


def main() -> int:
    os.chdir(RAIZ)  # os módulos usam caminhos relativos a LAB04/
    (RAIZ / "resultados").mkdir(exist_ok=True)

    situacao = {etapa.nome: rodar(etapa) for etapa in ETAPAS}

    print("\n" + "=" * 70)
    for etapa in ETAPAS:
        print(f"{situacao[etapa.nome].upper():<9} {etapa.nome}  [{etapa.de_quem}]")
    print("=" * 70)

    pendentes = [n for n, s in situacao.items() if s == PENDENTE]
    if pendentes:
        print(f"{len(pendentes)} etapa(s) pendente(s): o dashboard avisa no lugar do "
              f"gráfico até o módulo entrar.")
    if ERRO in situacao.values():
        print("Alguma etapa quebrou — veja o traceback acima.")
        return 1
    print("Pronto. Dashboard: streamlit run dashboard/app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
