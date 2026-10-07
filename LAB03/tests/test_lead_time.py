import pytest

from metricas.lead_time import (
    lead_time_release,
    lead_time_repo,
    lead_times_commits,
    lead_times_por_commit,
    lead_times_por_release,
)

DIA = 24


def comp(tag, publicada, datas, status="ok"):
    return {
        "tag_name": tag,
        "published_at": publicada,
        "status": status,
        "commits": [{"sha": f"{tag}-{i}", "data": d} for i, d in enumerate(datas)],
    }


@pytest.fixture
def v11():
    return comp(
        "v1.1",
        "2025-03-15T00:00:00Z",
        ["2025-03-02T00:00:00Z", "2025-03-10T00:00:00Z", "2025-03-14T00:00:00Z"],
    )


def test_exemplo_variante_a(v11):
    assert lead_times_por_release([v11]) == [13 * DIA]
    assert lead_time_repo([v11])["lead_time_a_horas"] == 13 * DIA


def test_exemplo_variante_b(v11):
    assert sorted(lead_times_por_commit([v11]), reverse=True) == [13 * DIA, 5 * DIA, 1 * DIA]
    assert lead_time_repo([v11])["lead_time_b_horas"] == 5 * DIA


def test_primeira_release_ignorada(v11):
    primeira = comp("v1.0", "2025-02-01T00:00:00Z", [], status="primeira")
    r = lead_time_repo([primeira, v11])
    assert r["releases_avaliadas"] == 1
    assert r["releases_primeira"] == 1
    assert r["lead_time_a_horas"] == 13 * DIA


def test_release_sem_commits_novos(v11):
    vazia = comp("v1.1.1", "2025-03-16T00:00:00Z", [])
    r = lead_time_repo([v11, vazia])
    assert r["releases_avaliadas"] == 1
    assert r["releases_sem_commits"] == 1
    assert r["commits_avaliados"] == 3
    assert lead_time_release("2025-03-16T00:00:00Z", []) is None


def test_repositorio_com_unica_release():
    unica = comp("v1.0", "2025-02-01T00:00:00Z", [], status="primeira")
    r = lead_time_repo([unica])
    assert r["lead_time_a_horas"] is None
    assert r["lead_time_b_horas"] is None
    assert r["releases_avaliadas"] == 0


def test_release_404_ignorada(v11):
    quebrada = comp("v1.2", "2025-04-01T00:00:00Z", [], status="404")
    r = lead_time_repo([v11, quebrada])
    assert r["releases_404"] == 1
    assert r["releases_avaliadas"] == 1


def test_mediana_entre_releases_e_commits(v11):
    v12 = comp("v1.2", "2025-04-01T00:00:00Z", ["2025-03-30T00:00:00Z"])
    v13 = comp("v1.3", "2025-05-01T12:00:00Z", ["2025-04-01T12:00:00Z", "2025-04-30T12:00:00Z"])
    r = lead_time_repo([v11, v12, v13])
    assert r["lead_time_a_horas"] == 13 * DIA
    assert r["lead_time_b_horas"] == pytest.approx(3.5 * DIA)


def test_fuso_e_data_sem_timezone():
    assert lead_times_commits("2025-03-15T00:00:00Z", ["2025-03-14T21:00:00-03:00"]) == [0]
    assert lead_time_release("2025-03-15T00:00:00", ["2025-03-14T00:00:00"]) == DIA
