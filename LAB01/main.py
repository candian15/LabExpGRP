#!/usr/bin/env python3
"""
CLI única do LAB01 — roda extract/analyze/visualize/merge de cada RQ sem precisar
entrar em cada pasta e lembrar o script, a flag e o CSV certos.

Exemplos:
    python main.py --list                              # status: o que já foi gerado, o que falta
    python main.py --rq RQ01_RQ02 --stage extract --mode sample
    python main.py --rq all --stage extract --mode full
    python main.py --rq all --stage all --mode full     # pipeline completo
    python main.py --rq RQ07 --stage merge
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

LAB01_DIR = Path(__file__).resolve().parent
MODE_FLAGS = {"sample": ["--sample"], "100": [], "full": ["--full"]}
PAUSE_BETWEEN_EXTRACTS = 10  # segundos entre extrações de RQs diferentes, para não bater no rate limit do GitHub

# Cada RQ declara só os estágios que realmente tem: RQ03_RQ04 não tem "analyze",
# RQ07 não consulta a API (só "merge" dos CSVs das outras + "visualize").
RQS = {
    "RQ01_RQ02": {
        "dir": LAB01_DIR / "RQ01_RQ02",
        "extract": "rq01_rq02_extract.py",
        "extract_out": {"sample": "sample_rq01_rq02.csv", "100": "rq01_rq02.csv", "full": "rq01_rq02_1000.csv"},
        "analyze": "analyze_rq01_rq02.py",
        "visualize": "visualize_rq01_rq02.py",
    },
    "RQ03_RQ04": {
        "dir": LAB01_DIR / "RQ03_RQ04",
        "extract": "rq03_rq04_extract.py",
        "extract_out": {"sample": "sample_rq03_rq04.csv", "100": "rq03_rq04.csv", "full": "rq03_rq04_1000.csv"},
        "visualize": "visualize_rq03_rq04.py",
    },
    "RQ05_RQ06": {
        "dir": LAB01_DIR / "RQ05_RQ06",
        "extract": "rq05_rq06_extract.py",
        "extract_out": {"sample": "sample_rq05_rq06.csv", "100": "rq05_rq06.csv", "full": "rq05_rq06_1000.csv"},
        "analyze": "analyze_rq05_rq06.py",
        "visualize": "visualize_rq05_rq06.py",
    },
    "RQ07": {"dir": LAB01_DIR / "RQ07"},
}
RQ07_MERGE_OUT = "rq07_por_linguagem.csv"


def load_dotenv():
    """Lê LAB01/.env (KEY=VALUE por linha) sem sobrescrever variáveis já definidas no ambiente."""
    env_file = LAB01_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def stages_of(rq):
    if rq == "RQ07":
        return ["merge", "visualize"]
    return [s for s in ("extract", "analyze", "visualize") if RQS[rq].get(s)]


def full_csv(rq):
    return RQS[rq]["dir"] / RQS[rq]["extract_out"]["full"]


def print_status():
    print("=== Status dos arquivos gerados ===")
    for rq in ("RQ01_RQ02", "RQ03_RQ04", "RQ05_RQ06"):
        p = full_csv(rq)
        print(f"{rq:<12} [{'OK' if p.exists() else 'faltando'}] {p.name}")
    rq07_out = RQS["RQ07"]["dir"] / RQ07_MERGE_OUT
    print(f"{'RQ07':<12} [{'OK' if rq07_out.exists() else 'faltando'}] {RQ07_MERGE_OUT} "
          f"(precisa dos 3 CSVs _1000.csv acima)")


def run(cmd, cwd, env):
    print(f"$ {' '.join(cmd)}   (em {cwd})")
    return subprocess.run(cmd, cwd=cwd, env=env).returncode == 0


def run_rq07(stage, env):
    dir_ = RQS["RQ07"]["dir"]
    sources = {"rq02": "RQ01_RQ02", "rq0304": "RQ03_RQ04", "rq05": "RQ05_RQ06"}
    paths = {k: full_csv(rq) for k, rq in sources.items()}

    if stage == "merge":
        missing = [rq for k, rq in sources.items() if not paths[k].exists()]
        if missing:
            print(f"[erro] faltam os CSVs de 1000 repositórios de: {', '.join(missing)}. "
                  f"Rode 'extract --mode full' nessas RQs antes do merge da RQ07.")
            return False
        cmd = [sys.executable, "rq07_analysis.py",
               "--rq02", str(paths["rq02"]), "--rq0304", str(paths["rq0304"]), "--rq05", str(paths["rq05"])]
        return run(cmd, dir_, env)

    if stage == "visualize":
        if not (dir_ / RQ07_MERGE_OUT).exists():
            print(f"[erro] {RQ07_MERGE_OUT} não existe — rode o estágio 'merge' primeiro.")
            return False
        return run([sys.executable, "visualize_rq07.py", RQ07_MERGE_OUT], dir_, env)

    print(f"[erro] RQ07 não tem estágio '{stage}' (use merge ou visualize).")
    return False


def run_stage(rq, stage, mode, env):
    if rq == "RQ07":
        return run_rq07(stage, env)

    spec = RQS[rq]
    dir_ = spec["dir"]

    if stage == "extract":
        if not spec.get("extract"):
            print(f"[erro] {rq} não tem etapa de extração.")
            return False
        if not env.get("GITHUB_TOKEN"):
            print("[erro] defina GITHUB_TOKEN (variável de ambiente ou --token) antes de rodar extract.")
            return False
        return run([sys.executable, spec["extract"]] + MODE_FLAGS[mode], dir_, env)

    if stage in ("analyze", "visualize"):
        script = spec.get(stage)
        if not script:
            print(f"[erro] {rq} não tem etapa de {stage}.")
            return False
        csv_name = spec["extract_out"][mode]
        if not (dir_ / csv_name).exists():
            print(f"[erro] {csv_name} não encontrado — rode 'extract --mode {mode}' antes.")
            return False
        return run([sys.executable, script, csv_name], dir_, env)

    print(f"[erro] estágio desconhecido: {stage}")
    return False


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--rq", nargs="+", choices=list(RQS) + ["all"], default=["all"],
                         help="Quais RQs rodar (default: all)")
    parser.add_argument("--stage", nargs="+", choices=["extract", "analyze", "visualize", "merge", "all"],
                         default=["all"], help="Quais estágios rodar por RQ (default: all)")
    parser.add_argument("--mode", choices=["sample", "100", "full"], default="full",
                         help="Tamanho da extração: sample (8) / 100 / full (1000). Default: full")
    parser.add_argument("--token", default=None,
                         help="GITHUB_TOKEN a usar (senão usa a variável de ambiente GITHUB_TOKEN)")
    parser.add_argument("--list", action="store_true",
                         help="Só mostra o status dos arquivos já gerados, não roda nada")
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    if args.list:
        print_status()
        return

    env = os.environ.copy()
    if args.token:
        env["GITHUB_TOKEN"] = args.token

    rqs = list(RQS) if "all" in args.rq else args.rq
    failed = []
    ran_extract_before = False

    for rq in rqs:
        available = stages_of(rq)
        stages = available if "all" in args.stage else [s for s in args.stage if s in available]
        for stage in stages:
            if stage == "extract" and ran_extract_before:
                print(f"\n(pausa de {PAUSE_BETWEEN_EXTRACTS}s entre extrações — evita rate limit do GitHub)")
                time.sleep(PAUSE_BETWEEN_EXTRACTS)
            print(f"\n>>> {rq} / {stage} (mode={args.mode})")
            if not run_stage(rq, stage, args.mode, env):
                failed.append(f"{rq}/{stage}")
            if stage == "extract":
                ran_extract_before = True

    if failed:
        print(f"\nEtapas com problema: {', '.join(failed)}")
        sys.exit(1)
    print("\nConcluído.")


if __name__ == "__main__":
    main()
