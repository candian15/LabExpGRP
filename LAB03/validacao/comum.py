"""Definições compartilhadas da validação manual (seção 6 do enunciado)."""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

AVALIADORES = ("artur", "joao", "pedro")
SEMENTE = 42
PASTA = Path("validacao")

NIVEL_REPO = "repositorio"
NIVEL_RELEASE = "release"

COLUNAS_PLANILHA = ["nivel", "repo", "tag", "link", "link_commits",
                    "tipo_projeto", "entregas_reais", "corretiva", "observacao"]

# dimensão -> (nível em que é rotulada, valores aceitos)
DIMENSOES = {
    "tipo_projeto": (NIVEL_REPO, ("biblioteca", "aplicacao", "cli", "outro")),
    "entregas_reais": (NIVEL_REPO, ("sim", "nao", "incerto")),
    "corretiva": (NIVEL_RELEASE, ("sim", "nao")),
}


def normalizar(dimensao: str, valor: str | None) -> str | None:
    """Minúsculas e sem acento ("Não" vira "nao"). Vazio vira None."""
    v = "".join(c for c in unicodedata.normalize("NFKD", valor or "") if not unicodedata.combining(c))
    v = v.strip().lower()
    if not v:
        return None
    if v not in DIMENSOES[dimensao][1]:
        raise ValueError(f"{dimensao}: valor {valor!r} inválido (use: {', '.join(DIMENSOES[dimensao][1])})")
    return v


def ler_csv(caminho: str | Path) -> list[dict]:
    """Lê CSV separado por ``;`` (Excel em português) ou ``,``."""
    texto = Path(caminho).read_text(encoding="utf-8-sig")
    delim = ";" if texto.split("\n", 1)[0].count(";") else ","
    return list(csv.DictReader(texto.splitlines(), delimiter=delim))


def escrever_csv(linhas: list[dict], campos: list[str], caminho: str | Path, delim: str = ",") -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=delim, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def ler_rotulos(caminho: str | Path) -> dict[str, dict[tuple, str | None]]:
    """Planilha preenchida -> {dimensão: {item: rótulo}}.

    Item é ``(repo,)`` nas dimensões de repositório e ``(repo, tag)`` na de release.
    """
    rotulos = {d: {} for d in DIMENSOES}
    for linha in ler_csv(caminho):
        for dim, (nivel, _) in DIMENSOES.items():
            if linha["nivel"] == nivel:
                item = (linha["repo"],) if nivel == NIVEL_REPO else (linha["repo"], linha["tag"])
                rotulos[dim][item] = normalizar(dim, linha[dim])
    return rotulos


def ler_todos(pasta: str | Path = PASTA) -> dict[str, dict[str, dict[tuple, str | None]]]:
    """{avaliador: {dimensão: {item: rótulo}}} das três planilhas."""
    return {a: ler_rotulos(Path(pasta) / f"rotulos_{a}.csv") for a in AVALIADORES}
