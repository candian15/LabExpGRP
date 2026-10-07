from datetime import datetime, timezone
from statistics import median


def _data(valor):
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor


def _horas(fim, inicio):
    return (_data(fim) - _data(inicio)).total_seconds() / 3600


def _validas(comparacoes):
    return [c for c in comparacoes if c.get("status", "ok") == "ok" and c.get("commits")]


def lead_time_release(published_at, datas_commits):
    if not datas_commits:
        return None
    mais_antigo = min(_data(d) for d in datas_commits)
    return _horas(published_at, mais_antigo)


def lead_times_commits(published_at, datas_commits):
    return [_horas(published_at, d) for d in datas_commits]


def lead_times_por_release(comparacoes):
    return [
        lead_time_release(c["published_at"], [k["data"] for k in c["commits"]])
        for c in _validas(comparacoes)
    ]


def lead_times_por_commit(comparacoes):
    valores = []
    for c in _validas(comparacoes):
        valores.extend(lead_times_commits(c["published_at"], [k["data"] for k in c["commits"]]))
    return valores


def lead_time_repo(comparacoes):
    por_release = lead_times_por_release(comparacoes)
    por_commit = lead_times_por_commit(comparacoes)
    status = [c.get("status", "ok") for c in comparacoes]
    return {
        "lead_time_a_horas": median(por_release) if por_release else None,
        "lead_time_b_horas": median(por_commit) if por_commit else None,
        "releases_avaliadas": len(por_release),
        "commits_avaliados": len(por_commit),
        "releases_primeira": status.count("primeira"),
        "releases_404": status.count("404"),
        "releases_sem_commits": sum(
            1 for c in comparacoes if c.get("status", "ok") == "ok" and not c.get("commits")
        ),
    }
