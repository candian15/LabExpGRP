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

# Commits que não são trabalho de produto: manutenção, dependências e infraestrutura.
# Eles inflam o denominador da fração de correções e escondem releases que, no que
# interessa, só corrigem.
_RUIDO = re.compile(
    r"^\s*(chore|build|ci|docs?|test|style|refactor)\b"
    r"|\b(bump|update|upgrade)\b.*\b(dep|dependenc|version|lockfile)"
    r"|^\s*(merge|release|version)\b",
    re.IGNORECASE,
)

# Cabeçalhos de seção nas release notes. A maioria dos projetos gera as notas a partir
# dos commits e separa correções de novidades em seções próprias.
_SECAO_CORRECAO = re.compile(r"^#{1,4}\s*.*(bug ?fix|fixes|fixed|patch|corre\u00e7|hotfix)", re.IGNORECASE | re.MULTILINE)
_SECAO_NOVIDADE = re.compile(r"^#{1,4}\s*.*(feature|new|added|enhancement|novidade|what's new)", re.IGNORECASE | re.MULTILINE)


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


def commits_substantivos(commits: list[dict]) -> list[dict]:
    """Commits sem os de manutenção, dependências e infraestrutura (ver ``_RUIDO``)."""
    return [c for c in commits if not _RUIDO.search(assunto(c.get("message")))]


def tem_correcao_substantiva(commits: list[dict]) -> bool:
    """Algum commit de correção que não seja manutenção, dependência ou infraestrutura."""
    return any(eh_correcao(c.get("message")) for c in commits_substantivos(commits))


def so_secao_de_correcao(body: str | None) -> bool:
    """As release notes têm seção de correção e **nenhuma** seção de novidade."""
    texto = body or ""
    return bool(_SECAO_CORRECAO.search(texto)) and not _SECAO_NOVIDADE.search(texto)


# --------------------------------------------------------- versões da heurística
# Assinatura: a comparação inteira (um item de ``comparacoes``) -> é corretiva?
# Recebe o item todo, e não só as tags e os commits, porque a partir da v4 as release
# notes (``body``) também entram na decisão.
Heuristica = Callable[[dict], bool]


def _v1(c: dict) -> bool:
    """v1 (exemplo do enunciado): só patch OU algum commit de correção."""
    commits = c.get("commits") or []
    return so_patch(c.get("anterior"), c["tag_name"]) or any(eh_correcao(x.get("message")) for x in commits)


def _v2(c: dict) -> bool:
    """v2: só patch OU pelo menos metade dos commits são correções."""
    return so_patch(c.get("anterior"), c["tag_name"]) or fracao_correcoes(c.get("commits") or []) >= 0.5


def _v3(c: dict) -> bool:
    """v3: (só patch E algum commit de correção) OU pelo menos metade dos commits são correções."""
    commits = c.get("commits") or []
    algum = any(eh_correcao(x.get("message")) for x in commits)
    return (so_patch(c.get("anterior"), c["tag_name"]) and algum) or fracao_correcoes(commits) >= 0.5


def _v4(c: dict) -> bool:
    """v4: as release notes só falam de correção, OU é patch com alguma correção real.

    A v1 marcava qualquer mudança de *patch* como corretiva, o que gerava muitos falsos
    positivos: publicar *patch* é a prática recomendada no SemVer e não implica corrigir
    defeito. A v4 troca esse critério isolado por dois:

    1. as **release notes** trazem seção de correção e nenhuma de novidade -- o sinal
       mais forte da amostra-ouro, porque a maioria dos projetos gera as notas a partir
       dos commits e separa as seções;
    2. a versão é *patch* **e** há pelo menos um commit de correção entre os
       **substantivos** -- atualização de dependência e manutenção não contam, senão um
       *bump* automático sozinho bastaria para a release virar corretiva.
    """
    if so_secao_de_correcao(c.get("body")):
        return True
    return (so_patch(c.get("anterior"), c["tag_name"])
            and tem_correcao_substantiva(c.get("commits") or []))


HEURISTICAS: dict[str, Heuristica] = {"v1": _v1, "v2": _v2, "v3": _v3, "v4": _v4}
VERSAO_PADRAO = "v4"  # melhor F1 na amostra-ouro (0,65); ver validacao/historico_heuristica.md


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
    if comparacao.get("anterior") is None:  # primeira release da história: não tem o que corrigir
        return False
    return _heuristica(versao)(comparacao)


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
