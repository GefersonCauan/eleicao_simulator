"""
=============================================================
  MODELO DE PREVISÃO ELEITORAL — Monte Carlo + Regressão
=============================================================
Técnicas utilizadas:
  - Regressão linear (tendência histórica)
  - Simulação Monte Carlo (incerteza eleitoral)
  - Modelo de transferência de votos no 2º turno
  - Índice de competitividade eleitoral
=============================================================
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from dados_eleitorais import (
    HISTORICO_PESQUISAS, PESQUISA_ATUAL, REJEICAO, SEGUNDO_TURNO
)

np.random.seed(42)

N_SIMULACOES = 50_000   # Monte Carlo iterations
MARGEM_ERRO  = 2.5      # margem de erro média das pesquisas (%)


# ─────────────────────────────────────────────
#  1. TENDÊNCIA HISTÓRICA POR CANDIDATO
# ─────────────────────────────────────────────

def calcular_tendencia(candidato: str) -> dict:
    """Regressão linear sobre as pesquisas históricas."""
    df = HISTORICO_PESQUISAS[["data", candidato]].dropna()
    if len(df) < 2:
        return {"slope": 0, "intercept": None, "r2": None}

    X = (df["data"] - df["data"].min()).dt.days.values.reshape(-1, 1)
    y = df[candidato].values

    model = LinearRegression().fit(X, y)
    r2    = model.score(X, y)
    slope = model.coef_[0] * 30  # pontos por mês

    return {
        "slope":     round(slope, 2),
        "intercept": round(model.intercept_, 2),
        "r2":        round(r2, 3),
        "direcao":   "📈 Subindo" if slope > 0.3 else
                     "📉 Caindo"  if slope < -0.3 else
                     "➡️  Estável",
    }


# ─────────────────────────────────────────────
#  2. MONTE CARLO — 1º TURNO
# ─────────────────────────────────────────────

def monte_carlo_primeiro_turno(cenario: str = "com_lula") -> pd.DataFrame:
    """
    Simula N_SIMULACOES eleições com ruído gaussiano em torno
    das intenções de voto atuais. Retorna probabilidade de cada
    candidato terminar em 1º ou 2º lugar.
    """
    base  = PESQUISA_ATUAL[cenario]
    nomes = list(base.keys())
    votos = np.array(list(base.values()), dtype=float)

    resultados_1o = {n: 0 for n in nomes}
    resultados_2o = {n: 0 for n in nomes}

    for _ in range(N_SIMULACOES):
        # ruído gaussiano proporcional à margem de erro
        ruido    = np.random.normal(0, MARGEM_ERRO, len(votos))
        sim      = np.maximum(votos + ruido, 0)
        sim      = sim / sim.sum() * 100   # renormaliza para 100%

        ordem    = np.argsort(sim)[::-1]
        resultados_1o[nomes[ordem[0]]] += 1
        resultados_2o[nomes[ordem[1]]] += 1

    df = pd.DataFrame({
        "Candidato":        nomes,
        "Intenção (%)":    [base[n] for n in nomes],
        "P(1º lugar) (%)": [round(resultados_1o[n] / N_SIMULACOES * 100, 1) for n in nomes],
        "P(2º lugar) (%)": [round(resultados_2o[n] / N_SIMULACOES * 100, 1) for n in nomes],
    }).sort_values("Intenção (%)", ascending=False)

    return df


# ─────────────────────────────────────────────
#  3. MONTE CARLO — 2º TURNO
# ─────────────────────────────────────────────

def monte_carlo_segundo_turno() -> list[dict]:
    """
    Para cada par de 2º turno na base de dados, simula N vezes
    e calcula a probabilidade de vitória de cada candidato.
    """
    resultados = []

    for c1, c2, pct1, pct2 in SEGUNDO_TURNO:
        v1 = np.random.normal(pct1, MARGEM_ERRO, N_SIMULACOES)
        v2 = np.random.normal(pct2, MARGEM_ERRO, N_SIMULACOES)

        # indecisos (resto vai para brancos/nulos, não altera proporção)
        prob_c1 = np.mean(v1 > v2) * 100
        prob_c2 = np.mean(v2 > v1) * 100
        empate  = 100 - prob_c1 - prob_c2

        resultados.append({
            "Candidato 1":     c1,
            "Candidato 2":     c2,
            "Intenção C1 (%)": pct1,
            "Intenção C2 (%)": pct2,
            "P(vitória C1) %": round(prob_c1, 1),
            "P(vitória C2) %": round(prob_c2, 1),
            "P(empate técn) %": round(empate, 1),
        })

    return resultados


# ─────────────────────────────────────────────
#  4. ÍNDICE DE COMPETITIVIDADE
# ─────────────────────────────────────────────

def indice_competitividade(cenario: str = "com_lula") -> float:
    """
    0 = disputa definida | 100 = totalmente imprevisível.
    Baseado no coeficiente de variação dos percentuais.
    """
    vals = list(PESQUISA_ATUAL[cenario].values())
    vals = [v for v in vals if v is not None]
    cv   = np.std(vals) / np.mean(vals)
    # normaliza para 0-100 invertido
    indice = max(0, min(100, (1 / (1 + cv)) * 100))
    return round(indice, 1)


# ─────────────────────────────────────────────
#  5. PROJEÇÃO PARA OUTUBRO 2026
# ─────────────────────────────────────────────

def projetar_outubro(candidato: str) -> dict:
    """
    Usa tendência histórica para projetar % em out/2026,
    com intervalo de confiança de 95%.
    """
    df = HISTORICO_PESQUISAS[["data", candidato]].dropna()
    if len(df) < 3:
        atual = PESQUISA_ATUAL["com_lula"].get(candidato,
                PESQUISA_ATUAL["sem_lula"].get(candidato, 0))
        return {"projecao": atual, "ic_inf": atual - 4, "ic_sup": atual + 4}

    X = (df["data"] - df["data"].min()).dt.days.values
    y = df[candidato].values

    # dias até outubro 2026
    dias_outubro = (pd.Timestamp("2026-10-04") - df["data"].min()).days

    slope, intercept, r, p, se = stats.linregress(X, y)
    proj   = intercept + slope * dias_outubro
    # IC 95% simples
    ic_inf = proj - 1.96 * se * np.sqrt(dias_outubro)
    ic_sup = proj + 1.96 * se * np.sqrt(dias_outubro)

    return {
        "projecao": round(max(0, proj), 1),
        "ic_inf":   round(max(0, ic_inf), 1),
        "ic_sup":   round(min(60, ic_sup), 1),
    }


# ─────────────────────────────────────────────
#  6. RELATÓRIO CONSOLIDADO
# ─────────────────────────────────────────────

def gerar_relatorio_completo() -> dict:
    mc_com   = monte_carlo_primeiro_turno("com_lula")
    mc_sem   = monte_carlo_primeiro_turno("sem_lula")
    segundo  = monte_carlo_segundo_turno()

    tendencias = {}
    projecoes  = {}
    for cand in ["Lula", "Flávio Bolsonaro", "Romeu Zema",
                 "Ronaldo Caiado", "Ciro Gomes"]:
        tendencias[cand] = calcular_tendencia(cand)
        projecoes[cand]  = projetar_outubro(cand)

    return {
        "monte_carlo_com_lula":  mc_com,
        "monte_carlo_sem_lula":  mc_sem,
        "segundo_turno":         segundo,
        "tendencias":            tendencias,
        "projecoes":             projecoes,
        "competitividade":       indice_competitividade(),
        "n_simulacoes":          N_SIMULACOES,
    }


if __name__ == "__main__":
    r = gerar_relatorio_completo()
    print("\n=== MONTE CARLO — CENÁRIO COM LULA ===")
    print(r["monte_carlo_com_lula"].to_string(index=False))
    print("\n=== MONTE CARLO — CENÁRIO SEM LULA ===")
    print(r["monte_carlo_sem_lula"].to_string(index=False))
    print(f"\nÍndice de competitividade: {r['competitividade']}%")
