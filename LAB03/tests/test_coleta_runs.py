from datetime import date

import pytest

from pipeline.coleta_runs import coletar_runs, meses_da_janela, repo_usa_actions, salvar_runs_csv


def test_meses_da_janela_cobre_tudo_sem_sobreposicao():
    fatias = meses_da_janela(date(2025, 9, 15), date(2026, 9, 14))
    assert fatias[0] == (date(2025, 9, 15), date(2025, 9, 30))
    assert fatias[-1] == (date(2026, 9, 1), date(2026, 9, 14))
    assert len(fatias) == 13
    for (_, fim), (ini, _) in zip(fatias, fatias[1:]):
        assert (ini - fim).days == 1


def test_meses_da_janela_rejeita_janela_invertida():
    with pytest.raises(ValueError):
        meses_da_janela(date(2026, 1, 2), date(2026, 1, 1))


class ClienteFalso:
    """Simula /actions/runs: ``por_dia`` diz quantos runs existem em cada dia."""

    def __init__(self, por_dia):
        self.por_dia = por_dia
        self.periodos = []

    def _runs(self, params):
        a, b = (date.fromisoformat(x) for x in params["created"].split(".."))
        self.periodos.append((a, b))
        runs = []
        for dia, n in self.por_dia.items():
            if a <= dia <= b:
                for i in range(n):
                    runs.append(
                        {
                            "id": hash((dia, i)),
                            "workflow_id": 1,
                            "event": "push",
                            "head_branch": "main",
                            "conclusion": "success",
                            "created_at": f"{dia}T10:00:00Z",
                            "run_started_at": f"{dia}T10:{i % 60:02d}:00Z",
                            "updated_at": f"{dia}T11:00:00Z",
                        }
                    )
        return runs

    def get(self, caminho, params=None):
        if caminho.endswith("/actions/workflows"):
            return {"total_count": self.por_dia.get("workflows", 0)}
        return {"total_count": len(self._runs(params))}

    def listar(self, caminho, params=None):
        return self._runs(params)[:1000]


def test_coleta_por_mes_e_ordena():
    gh = ClienteFalso({date(2026, 1, 5): 2, date(2026, 2, 5): 3})
    runs = coletar_runs(gh, "o", "r", "main", date(2026, 1, 1), date(2026, 2, 28))
    assert len(runs) == 5
    datas = [r["run_started_at"] for r in runs]
    assert datas == sorted(datas)


def test_mes_acima_do_teto_e_subdividido():
    gh = ClienteFalso({date(2026, 1, 3): 700, date(2026, 1, 20): 700})
    runs = coletar_runs(gh, "o", "r", "main", date(2026, 1, 1), date(2026, 1, 31))
    assert len(runs) == 1400  # nenhum run perdido pelo teto de 1.000
    assert any(a != date(2026, 1, 1) or b != date(2026, 1, 31) for a, b in gh.periodos)


def test_filtra_runs_de_outro_branch_ou_evento():
    class Misturado(ClienteFalso):
        def listar(self, caminho, params=None):
            base = super().listar(caminho, params)
            base[0] = {**base[0], "head_branch": "dev"}
            base[1] = {**base[1], "event": "schedule"}
            return base

    gh = Misturado({date(2026, 1, 5): 4})
    assert len(coletar_runs(gh, "o", "r", "main", date(2026, 1, 1), date(2026, 1, 31))) == 2


def test_repo_usa_actions():
    assert repo_usa_actions(ClienteFalso({"workflows": 3}), "o", "r")
    assert not repo_usa_actions(ClienteFalso({}), "o", "r")


def test_salvar_csv(tmp_path):
    gh = ClienteFalso({date(2026, 1, 5): 2})
    runs = coletar_runs(gh, "o", "r", "main", date(2026, 1, 1), date(2026, 1, 31))
    saida = tmp_path / "runs" / "o__r.csv"
    salvar_runs_csv(runs, saida, "o/r")
    linhas = saida.read_text().strip().splitlines()
    assert linhas[0].startswith("repo,id,workflow_id")
    assert len(linhas) == 3
