"""Change failure rate, variante (b): proxy de entrega (RQ 03b).

Uma release R é considerada **falha** se for seguida, em até 7 dias, por uma
**release corretiva**. O CFR do repositório é

    CFR(b) = nº de releases que falharam / nº de releases avaliadas

Releases publicadas nos últimos 7 dias da janela não podem ser avaliadas (ainda
não se sabe se haverá correção): ficam fora do denominador e são contadas como
**censuradas**.

Release corretiva é aquela cujo objetivo principal é corrigir um defeito
recente. Como o GitHub não diz isso, o grupo usa uma heurística automática,
que precisa ser validada contra a amostra-ouro (seção 6 do enunciado). Cada
versão testada fica registrada em ``HEURISTICAS`` e em
``validacao/historico_heuristica.md``.

Decisões do grupo (vão para a Metodologia):

- a release R só é comparada com a **release seguinte** (a correção de R é a
  próxima release), e não com todas as que vierem nos 7 dias;
- a mensagem do commit é lida só no **assunto** (primeira linha), porque o
  corpo costuma citar "fixes #123" também em funcionalidades novas;
- a janela de 7 dias conta a partir de ``published_at`` de R, e a censura vale
  para releases publicadas depois de ``fim - 7 dias`` (``fim`` inclusivo);
- se o ``compare`` deu 404 (commits desconhecidos), só vale o critério de
  versão (patch SemVer);
- a primeira release da história do repositório nunca é corretiva.

Entrada: a lista ``comparacoes`` devolvida por ``pipeline.coleta_releases``
(cada item com ``tag_name``, ``published_at``, ``anterior``, ``status`` e
``commits`` com ``message``).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Callable

JANELA_DIAS = 7

_SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_CORRECAO = re.compile(r"\b(revert|hotfix|bugfix|fix(?:es|ed)?)\b", re.IGNORECASE)


# --------------------------------------------------------------- sinais simples
def versao_semver(tag: str | None) -> tuple[int, int, int] | None:
    """``v2.3.1`` -> (2, 3, 1); None se a tag não tem MAJOR.MINOR.PATCH."""
    if not tag:
        return None
    m = _SEMVER.search(tag)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def so_patch(anterior: str | None, atual: str | None) -> bool:
    """A versão muda apenas no número de *patch* (``2.3.0 -> 2.3.1``)."""
    a, b = versao_semver(anterior), versao_semver(atual)
    if a is None or b is None:
        return False
    return a[0] == b[0] and a[1] == b[1] and b[2] > a[2]


def assunto(mensagem: str | None) -> str:
    """Primeira linha da mensagem do commit."""
    return (mensagem or "").strip().split("\n", 1)[0]


def eh_correcao(mensagem: str | None) -> bool:
    """O assunto do commit tem ``fix``, ``fixes``, ``fixed``, ``bugfix``, ``hotfix`` ou ``revert``."""
    return bool(_CORRECAO.search(assunto(mensagem)))


def fracao_correcoes(commits: list[dict]) -> float:
    """Proporção de commits da release cujo assunto é uma correção (0 se não há commits)."""
    if not commits:
        return 0.0
    return sum(1 for c in commits if eh_correcao(c.get("message"))) / len(commits)


# --------------------------------------------------------- versões da heurística
# Assinatura: (tag anterior, tag da release, commits entre as duas) -> é corretiva?
Heuristica = Callable[[str | None, str, list[dict]], bool]


def _v1(anterior, atual, commits) -> bool:
    """v1 (exemplo do enunciado): só patch OU algum commit de correção."""
    return so_patch(anterior, atual) or any(eh_correcao(c.get("message")) for c in commits)


def _v2(anterior, atual, commits) -> bool:
    """v2: só patch OU pelo menos metade dos commits são correções."""
    return so_patch(anterior, atual) or fracao_correcoes(commits) >= 0.5


def _v3(anterior, atual, commits) -> bool:
    """v3: (só patch E algum commit de correção) OU pelo menos metade dos commits são correções."""
    algum = any(eh_correcao(c.get("message")) for c in commits)
    return (so_patch(anterior, atual) and algum) or fracao_correcoes(commits) >= 0.5


HEURISTICAS: dict[str, Heuristica] = {"v1": _v1, "v2": _v2, "v3": _v3}
VERSAO_PADRAO = "v1"  # trocar pela melhor versão depois da validação manual


def _heuristica(versao: str) -> Heuristica:
    try:
        return HEURISTICAS[versao]
    except KeyError:
        raise ValueError(f"heurística desconhecida: {versao!r} (opções: {sorted(HEURISTICAS)})") from None


# ---------------------------------------------------------------------- cálculo
def _data(valor) -> datetime:
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _ordenadas(comparacoes: list[dict]) -> list[dict]:
    return sorted(comparacoes, key=lambda c: _data(c["published_at"]))


def eh_corretiva(comparacao: dict, versao: str = VERSAO_PADRAO) -> bool:
    """Classifica uma release (um item de ``comparacoes``) com a heurística escolhida."""
    anterior = comparacao.get("anterior")
    if anterior is None:  # primeira release da história: não tem o que corrigir
        return False
    return _heuristica(versao)(anterior, comparacao["tag_name"], comparacao.get("commits") or [])


def classificar_releases(comparacoes: list[dict], versao: str = VERSAO_PADRAO) -> list[dict]:
    """Uma linha por release: ``tag_name``, ``published_at`` e ``corretiva`` (bool)."""
    return [
        {
            "tag_name": c["tag_name"],
            "published_at": c["published_at"],
            "corretiva": eh_corretiva(c, versao),
        }
        for c in _ordenadas(comparacoes)
    ]


def cfr_entrega(
    comparacoes: list[dict],
    fim: date,
    versao: str = VERSAO_PADRAO,
    janela_dias: int = JANELA_DIAS,
) -> dict:
    """CFR (b) de um repositório.

    Devolve ``cfr_entrega`` (fração 0-1, ou None se nenhuma release pôde ser
    avaliada), ``n_avaliadas``, ``n_falhas``, ``n_censuradas`` e
    ``n_corretivas`` (releases corretivas na janela, útil para a RQ 08).
    """
    itens = _ordenadas(comparacoes)
    corretivas = [eh_corretiva(c, versao) for c in itens]
    espera = timedelta(days=janela_dias)
    fim_da_janela = datetime(fim.year, fim.month, fim.day, tzinfo=timezone.utc) + timedelta(days=1)

    avaliadas = falhas = censuradas = 0
    for i, c in enumerate(itens):
        publicada = _data(c["published_at"])
        if publicada + espera > fim_da_janela:
            censuradas += 1
            continue
        avaliadas += 1
        if i + 1 < len(itens) and corretivas[i + 1]:
            if _data(itens[i + 1]["published_at"]) - publicada <= espera:
                falhas += 1

    return {
        "cfr_entrega": falhas / avaliadas if avaliadas else None,
        "n_avaliadas": avaliadas,
        "n_falhas": falhas,
        "n_censuradas": censuradas,
        "n_corretivas": sum(corretivas),
    }
