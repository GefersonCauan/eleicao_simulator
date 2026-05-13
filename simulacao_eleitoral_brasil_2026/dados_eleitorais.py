"""
=============================================================
  SISTEMA DE SIMULAÇÃO ELEITORAL - BRASIL 2026/2028
  Dados reais: AtlasIntel (abril/2026), Datafolha, PoderData
=============================================================
"""

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
#  DADOS REAIS DE PESQUISAS (AtlasIntel abr/2026
#  + histórico Datafolha/PoderData)
# ─────────────────────────────────────────────

CANDIDATOS_2026 = {
    "Lula": {
        "partido": "PT",
        "cor": "#CC0000",
        "icone": "🔴",
        "ideologia": "Centro-Esquerda",
        "cargo_atual": "Presidente (2023–2026)",
        "estado": "SP",
        "idade": 80,
        "inelegivel": False,
    },
    "Flávio Bolsonaro": {
        "partido": "PL",
        "cor": "#002776",
        "icone": "🔵",
        "ideologia": "Direita",
        "cargo_atual": "Senador (RJ)",
        "estado": "RJ",
        "idade": 44,
        "inelegivel": False,
    },
    "Fernando Haddad": {
        "partido": "PT",
        "cor": "#C00000",
        "icone": "🔴",
        "ideologia": "Centro-Esquerda",
        "cargo_atual": "Ministro da Fazenda",
        "estado": "SP",
        "idade": 62,
        "inelegivel": False,
    },
    "Geraldo Alckmin": {
        "partido": "PSB",
        "cor": "#FF6600",
        "icone": "🟠",
        "ideologia": "Centro",
        "cargo_atual": "Vice-Presidente",
        "estado": "SP",
        "idade": 72,
        "inelegivel": False,
    },
    "Romeu Zema": {
        "partido": "Novo",
        "cor": "#FF8C00",
        "icone": "🟡",
        "ideologia": "Direita-Liberal",
        "cargo_atual": "Governador (MG)",
        "estado": "MG",
        "idade": 57,
        "inelegivel": False,
    },
    "Ronaldo Caiado": {
        "partido": "PSD",
        "cor": "#1E90FF",
        "icone": "🔵",
        "ideologia": "Direita",
        "cargo_atual": "Governador (GO)",
        "estado": "GO",
        "idade": 72,
        "inelegivel": False,
    },
    "Ciro Gomes": {
        "partido": "PDT",
        "cor": "#FFD700",
        "icone": "🟡",
        "ideologia": "Centro-Esquerda",
        "cargo_atual": "Ex-ministro / político",
        "estado": "CE",
        "idade": 67,
        "inelegivel": False,
    },
    "Jair Bolsonaro": {
        "partido": "PL",
        "cor": "#001F5B",
        "icone": "⚫",
        "ideologia": "Direita",
        "cargo_atual": "Ex-Presidente",
        "estado": "RJ",
        "idade": 70,
        "inelegivel": True,  # inelegível até 2030 (TSE)
    },
}

# ─────────────────────────────────────────────
#  SÉRIE HISTÓRICA DE PESQUISAS (1º turno)
#  Fonte: AtlasIntel, Datafolha, PoderData
# ─────────────────────────────────────────────

HISTORICO_PESQUISAS = pd.DataFrame([
    # data,          Instituto,    Lula,  Flávio, Haddad, Zema, Caiado, Ciro, Outros
    ("2025-03-01", "Datafolha",   38,    18,     None,   8,    7,      5,    24),
    ("2025-06-01", "PoderData",   37,    19,     None,   9,    6,      4,    25),
    ("2025-09-01", "Datafolha",   36,    21,     None,   10,   7,      4,    22),
    ("2025-12-01", "AtlasIntel",  35,    22,     None,   11,   8,      4,    20),
    ("2026-02-01", "Datafolha",   34,    23,     None,   10,   8,      3,    22),
    ("2026-04-27", "AtlasIntel",  33,    27,     None,   11,   7,      3,    19),
], columns=["data", "instituto", "Lula", "Flávio Bolsonaro",
            "Fernando Haddad", "Romeu Zema", "Ronaldo Caiado", "Ciro Gomes", "Outros/Brancos"])

HISTORICO_PESQUISAS["data"] = pd.to_datetime(HISTORICO_PESQUISAS["data"])

# ─────────────────────────────────────────────
#  PESQUISA MAIS RECENTE (AtlasIntel abr/2026)
#  Cenário com Lula | Cenário sem Lula
# ─────────────────────────────────────────────

PESQUISA_ATUAL = {
    "com_lula": {
        "Lula": 33,
        "Flávio Bolsonaro": 27,
        "Romeu Zema": 11,
        "Ronaldo Caiado": 7,
        "Ciro Gomes": 3,
        "Outros/Brancos": 19,
    },
    "sem_lula": {
        "Fernando Haddad": 25,
        "Flávio Bolsonaro": 26,
        "Romeu Zema": 12,
        "Ronaldo Caiado": 8,
        "Ciro Gomes": 4,
        "Outros/Brancos": 25,
    }
}

# ─────────────────────────────────────────────
#  RESULTADOS ELEITORAIS HISTÓRICOS
# ─────────────────────────────────────────────

HISTORICO_ELEICOES = pd.DataFrame([
    (2002, "Lula (PT)",        46.44, 61.27),
    (2006, "Lula (PT)",        48.61, 60.83),
    (2010, "Dilma (PT)",       46.91, 56.05),
    (2014, "Dilma (PT)",       41.59, 51.64),
    (2018, "Bolsonaro (PSL)",  46.03, 55.13),
    (2022, "Lula (PT)",        48.43, 50.90),
], columns=["ano", "vencedor", "pct_1turno", "pct_2turno"])

# ─────────────────────────────────────────────
#  REJEIÇÃO DOS CANDIDATOS (AtlasIntel abr/2026)
# ─────────────────────────────────────────────

REJEICAO = {
    "Lula": 44,
    "Flávio Bolsonaro": 41,
    "Jair Bolsonaro": 50,
    "Fernando Haddad": 38,
    "Romeu Zema": 22,
    "Ronaldo Caiado": 20,
    "Ciro Gomes": 28,
}

# ─────────────────────────────────────────────
#  SIMULAÇÃO 2º TURNO (AtlasIntel abr/2026)
# ─────────────────────────────────────────────

SEGUNDO_TURNO = [
    ("Lula",            "Flávio Bolsonaro", 48, 48),   # empate técnico
    ("Lula",            "Romeu Zema",       49, 44),
    ("Lula",            "Ronaldo Caiado",   50, 42),
    ("Fernando Haddad", "Flávio Bolsonaro", 43, 49),
    ("Geraldo Alckmin", "Flávio Bolsonaro", 45, 46),   # empate técnico
]
