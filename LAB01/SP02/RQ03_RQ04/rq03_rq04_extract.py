"""
Extração RQ03 + RQ04 - Lab01S01 / Lab01S02
RQ03: total de releases (releases.totalCount)
RQ04: tempo até a última atualização (a partir de pushedAt)

Segue o mesmo padrão das demais partes do grupo (RQ01+RQ02, RQ05+RQ06):
- consulta GraphQL escrita e consumida por script próprio (só stdlib: urllib)
- mesmo critério de seleção: "stars:>1000 sort:stars-desc"
- saída em CSV com chave `repo` para permitir merge dos datasets

Uso:
    1. Crie um Personal Access Token (classic) em https://github.com/settings/tokens
       com escopo "public_repo" ou "repo" (leitura basta).
    2. Exporte a variável de ambiente:
         export GITHUB_TOKEN="seu_token_aqui"
    3. Rode:
         python rq03_rq04_extract.py --sample   # 8 repos p/ validação rápida
         python rq03_rq04_extract.py            # 100 repos (Lab01S01)
         python rq03_rq04_extract.py --full     # 1000 repos (Lab01S02)
"""

import os
import sys
import time
import csv
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($queryString: String!, $cursor: String, $perPage: Int!) {
  rateLimit {
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: $perPage, after: $cursor) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        pushedAt
        releases {
          totalCount
        }
      }
    }
  }
}
"""


def run_query(token, cursor=None, per_page=10, max_retries=5):
    variables = {
        "queryString": "stars:>1000 sort:stars-desc",
        "cursor": cursor,
        "perPage": per_page,
    }
    payload = json.dumps({"query": QUERY, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        GITHUB_GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < max_retries:
                wait = 2 * attempt
                print(f"[aviso] erro {e.code} (transitório), retry {attempt}/{max_retries} em {wait}s...")
                time.sleep(wait)
                continue
            raise Exception(f"Erro {e.code}: {e.read().decode()}")
    if "errors" in data:
        raise Exception(f"Erro GraphQL: {data['errors']}")
    return data["data"]


def calc_days_since_update(pushed_at_str):
    pushed = datetime.strptime(pushed_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    now = datetime.now(timezone.utc)
    delta = now - pushed
    return delta.days


def collect_repos(token, total_target=100, per_page=10):
    repos = []
    cursor = None

    while len(repos) < total_target:
        remaining = total_target - len(repos)
        page_size = min(per_page, remaining)

        data = run_query(token, cursor=cursor, per_page=page_size)

        rl = data["rateLimit"]
        print(f"[rate limit] restante: {rl['remaining']} | reset: {rl['resetAt']}")

        nodes = data["search"]["nodes"]
        for node in nodes:
            repos.append(
                {
                    "repo": node["nameWithOwner"],
                    "stars": node["stargazerCount"],
                    # RQ03
                    "total_releases": node["releases"]["totalCount"],
                    # RQ04
                    "pushed_at": node["pushedAt"],
                    "days_since_update": calc_days_since_update(node["pushedAt"]),
                }
            )

        page_info = data["search"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

        time.sleep(0.5)  # gentileza com a API

    return repos[:total_target]


def save_csv(repos, filename):
    fieldnames = ["repo", "stars", "total_releases", "pushed_at", "days_since_update"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repos)
    print(f"\nSalvo em: {filename}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Roda apenas uma amostra pequena (8 repos) para validação rápida",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Roda para 1000 repositórios (Lab01S02, com paginação completa)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERRO: defina a variável de ambiente GITHUB_TOKEN antes de rodar.")
        sys.exit(1)

    if args.sample:
        total, out_file = 8, "sample_rq03_rq04.csv"
    elif args.full:
        total, out_file = 1000, "rq03_rq04_1000.csv"
    else:
        total, out_file = 100, "rq03_rq04.csv"

    print(f"Coletando {total} repositórios...")
    repos = collect_repos(token, total_target=total)

    print("\n--- Prévia ---")
    for r in repos[:5]:
        print(r)

    save_csv(repos, out_file)


if __name__ == "__main__":
    main()
