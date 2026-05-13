"""
=============================================================
  DASHBOARD DE VISUALIZAÇÕES — ELEIÇÕES BRASIL 2026
  Gera HTML interativo com Plotly
=============================================================
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

from dados_eleitorais  import (
  CANDIDATOS_2026, HISTORICO_PESQUISAS, HISTORICO_ELEICOES,
  PESQUISA_ATUAL, REJEICAO, SEGUNDO_TURNO
)
from modelo_previsao import gerar_relatorio_completo

# ─────────────────────────────────────────────
#  PALETA & CONSTANTES
# ─────────────────────────────────────────────

CORES = {
    "Lula":              "#CC2200",
    "Fernando Haddad":   "#AA1100",
    "Flávio Bolsonaro":  "#003380",
    "Jair Bolsonaro":    "#001F5B",
    "Romeu Zema":        "#FF8800",
    "Ronaldo Caiado":    "#1177DD",
    "Ciro Gomes":        "#DDB000",
    "Geraldo Alckmin":   "#EE6600",
    "Outros/Brancos":    "#AAAAAA",
}

BG       = "#0A0E1A"
BG_CARD  = "#111827"
ACCENT   = "#00D4FF"
TEXT     = "#E8ECF4"
GRID     = "#1E2535"


# ─────────────────────────────────────────────
#  LAYOUT BASE.
# ─────────────────────────────────────────────

def base_layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        font=dict(family="'Courier New', monospace", color=TEXT, size=12),
        margin=dict(l=40, r=40, t=60, b=40),
        **kwargs,
    )


# ─────────────────────────────────────────────
#  G1 — INTENÇÃO DE VOTO ATUAL (barras horizontais)
# ─────────────────────────────────────────────

def grafico_intencao_voto(cenario="com_lula") -> go.Figure:
    data   = PESQUISA_ATUAL[cenario]
    nomes  = list(data.keys())
    vals   = list(data.values())
    cores  = [CORES.get(n, "#888") for n in nomes]

    idx = np.argsort(vals)[::-1]
    nomes = [nomes[i] for i in idx]
    vals  = [vals[i]  for i in idx]
    cores = [cores[i] for i in idx]

    label = "Com Lula" if cenario == "com_lula" else "Sem Lula (Haddad)"

    fig = go.Figure(go.Bar(
        x=vals, y=nomes, orientation="h",
        marker_color=cores,
        text=[f"<b>{v}%</b>" for v in vals],
        textposition="outside",
        textfont=dict(size=13, color=TEXT),
        hovertemplate="<b>%{y}</b><br>Intenção: %{x}%<extra></extra>",
    ))

    fig.update_layout(
        **base_layout(
            title=dict(text=f"📊 Intenção de Voto — 1º Turno ({label})<br>"
                            f"<sub>AtlasIntel/Bloomberg · Abr/2026 · n=5.008 · Erro: ±1pp</sub>",
                       font=dict(size=16, color=ACCENT), x=0.5),
            xaxis=dict(title="% Intenção de voto", range=[0, 45],
                       gridcolor=GRID, showgrid=True),
            yaxis=dict(showgrid=False),
            showlegend=False,
            height=400,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G2 — EVOLUÇÃO HISTÓRICA (linha)
# ─────────────────────────────────────────────

def grafico_evolucao() -> go.Figure:
    fig = go.Figure()

    for cand in ["Lula", "Flávio Bolsonaro", "Romeu Zema", "Ronaldo Caiado", "Ciro Gomes"]:
        df = HISTORICO_PESQUISAS[["data", cand]].dropna()
        fig.add_trace(go.Scatter(
            x=df["data"], y=df[cand],
            name=cand,
            mode="lines+markers",
            line=dict(color=CORES.get(cand, "#888"), width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{cand}</b><br>Data: %{{x|%b %Y}}<br>%{{y}}%<extra></extra>",
        ))

    fig.update_layout(
        **base_layout(
            title=dict(text="📈 Evolução das Pesquisas (2025–2026)",
                       font=dict(size=16, color=ACCENT), x=0.5),
            xaxis=dict(title="Data", gridcolor=GRID, showgrid=True),
            yaxis=dict(title="% Intenção de voto", gridcolor=GRID, showgrid=True,
                       range=[0, 45]),
            legend=dict(bgcolor=BG, bordercolor=GRID, borderwidth=1),
            height=400,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G3 — PROBABILIDADES MONTE CARLO
# ─────────────────────────────────────────────

def grafico_monte_carlo(relatorio: dict) -> go.Figure:
    df   = relatorio["monte_carlo_com_lula"]
    df   = df[df["Candidato"] != "Outros/Brancos"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="P(1º lugar)", x=df["Candidato"], y=df["P(1º lugar) (%)"],
        marker_color=[CORES.get(c, "#888") for c in df["Candidato"]],
        text=[f"{v}%" for v in df["P(1º lugar) (%)"]],
        textposition="outside",
    ))

    def hex_rgba(h, a=0.45):
        h = h.lstrip('#')
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f"rgba({r},{g},{b},{a})"

    fig.add_trace(go.Bar(
        name="P(2º lugar)", x=df["Candidato"], y=df["P(2º lugar) (%)"],
        marker_color=[hex_rgba(CORES.get(c, "#888888")) for c in df["Candidato"]],
        text=[f"{v}%" for v in df["P(2º lugar) (%)"]],
        textposition="outside",
    ))

    fig.update_layout(
        **base_layout(
            title=dict(text=f"🎲 Simulação Monte Carlo — {relatorio['n_simulacoes']:,} simulações<br>"
                            f"<sub>Prob. de terminar em 1º ou 2º no 1º turno</sub>",
                       font=dict(size=16, color=ACCENT), x=0.5),
            barmode="group",
            xaxis=dict(gridcolor=GRID),
            yaxis=dict(title="%", gridcolor=GRID, range=[0, 110]),
            legend=dict(bgcolor=BG),
            height=420,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G4 — 2º TURNO (cenários)
# ─────────────────────────────────────────────

def grafico_segundo_turno(relatorio: dict) -> go.Figure:
    st = relatorio["segundo_turno"]

    labels  = [f"{d['Candidato 1']}<br>vs<br>{d['Candidato 2']}" for d in st]
    p_c1    = [d["P(vitória C1) %"] for d in st]
    p_c2    = [d["P(vitória C2) %"] for d in st]
    cores_c1 = [CORES.get(d["Candidato 1"], "#888") for d in st]
    cores_c2 = [CORES.get(d["Candidato 2"], "#888") for d in st]

    fig = go.Figure()

    for i, d in enumerate(st):
        fig.add_trace(go.Bar(
            name=d["Candidato 1"] if i == 0 else None,
            x=[labels[i]], y=[p_c1[i]],
            marker_color=cores_c1[i],
            text=f"<b>{p_c1[i]}%</b>",
            textposition="inside",
            showlegend=False,
        ))
        fig.add_trace(go.Bar(
            name=d["Candidato 2"] if i == 0 else None,
            x=[labels[i]], y=[p_c2[i]],
            marker_color=cores_c2[i],
            text=f"<b>{p_c2[i]}%</b>",
            textposition="inside",
            showlegend=False,
        ))

    fig.update_layout(
        **base_layout(
            title=dict(text="⚔️  Cenários de 2º Turno — Probabilidade de Vitória",
                       font=dict(size=16, color=ACCENT), x=0.5),
            barmode="stack",
            xaxis=dict(gridcolor=GRID, tickfont=dict(size=10)),
            yaxis=dict(title="%", gridcolor=GRID, range=[0, 105]),
            height=420,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G5 — REJEIÇÃO
# ─────────────────────────────────────────────

def grafico_rejeicao() -> go.Figure:
    cands = sorted(REJEICAO.items(), key=lambda x: x[1], reverse=True)
    nomes = [c[0] for c in cands]
    vals  = [c[1] for c in cands]
    cores = [CORES.get(n, "#888") for n in nomes]

    fig = go.Figure(go.Bar(
        x=vals, y=nomes, orientation="h",
        marker_color=cores,
        text=[f"{v}%" for v in vals],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Rejeição: %{x}%<extra></extra>",
    ))

    fig.update_layout(
        **base_layout(
            title=dict(text="🚫 Rejeição — 'Não votaria de jeito nenhum'<br>"
                            "<sub>AtlasIntel · Abr/2026</sub>",
                       font=dict(size=16, color=ACCENT), x=0.5),
            xaxis=dict(title="%", range=[0, 65], gridcolor=GRID),
            yaxis=dict(showgrid=False),
            height=380,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G6 — PROJEÇÃO OUTUBRO 2026
# ─────────────────────────────────────────────

def grafico_projecao(relatorio: dict) -> go.Figure:
    projs = relatorio["projecoes"]
    cands = list(projs.keys())
    vals  = [projs[c]["projecao"] for c in cands]
    inf   = [projs[c]["ic_inf"]   for c in cands]
    sup   = [projs[c]["ic_sup"]   for c in cands]
    cores = [CORES.get(c, "#888") for c in cands]

    err_minus = [max(0, v - i) for v, i in zip(vals, inf)]
    err_plus  = [max(0, s - v) for v, s in zip(vals, sup)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cands, y=vals,
        marker_color=cores,
        error_y=dict(type="data", symmetric=False,
                     array=err_plus, arrayminus=err_minus,
                     color="rgba(255,255,255,0.4)", thickness=2, width=6),
        text=[f"<b>{v}%</b>" for v in vals],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Projeção: %{y}%<extra></extra>",
    ))

    fig.update_layout(
        **base_layout(
            title=dict(text="🔮 Projeção para Outubro 2026 (Regressão + IC 95%)",
                       font=dict(size=16, color=ACCENT), x=0.5),
            xaxis=dict(gridcolor=GRID, tickangle=-20),
            yaxis=dict(title="%", gridcolor=GRID, range=[0, 50]),
            height=400,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  G7 — HISTÓRICO DE ELEIÇÕES
# ─────────────────────────────────────────────

def grafico_historico_eleicoes() -> go.Figure:
    df  = HISTORICO_ELEICOES
    fig = make_subplots(specs=[[{"secondary_y": False}]])

    fig.add_trace(go.Bar(
        x=df["ano"].astype(str), y=df["pct_1turno"],
        name="1º Turno",
        marker_color=["#CC2200" if "PT" in v or "Lula" in v or "Dilma" in v else "#003380"
                      for v in df["vencedor"]],
        text=[f"{v}%<br><sub>{n}</sub>" for v, n in
              zip(df["pct_1turno"], df["vencedor"])],
        textposition="outside",
        width=0.35,
    ))

    fig.add_trace(go.Scatter(
        x=df["ano"].astype(str), y=df["pct_2turno"],
        name="% 2º Turno (vencedor)",
        mode="lines+markers+text",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=10, color=ACCENT),
        text=[f"{v}%" for v in df["pct_2turno"]],
        textposition="top center",
        textfont=dict(color=ACCENT),
    ))

    fig.update_layout(
        **base_layout(
            title=dict(text="🗳️  Resultados Históricos — Eleições Presidenciais (2002–2022)",
                       font=dict(size=16, color=ACCENT), x=0.5),
            xaxis=dict(title="Ano", gridcolor=GRID),
            yaxis=dict(title="%", gridcolor=GRID, range=[0, 75]),
            legend=dict(bgcolor=BG),
            height=400,
        )
    )
    return fig


# ─────────────────────────────────────────────
#  MONTAGEM DO DASHBOARD HTML
# ─────────────────────────────────────────────

def gerar_dashboard(output_path: str = "dashboard_eleitoral.html"):
    print("⚙️  Executando simulação Monte Carlo (50.000 iterações)...")
    relatorio = gerar_relatorio_completo()
    print("✅  Simulação concluída.\n")


    figs = {
      "intencao":    grafico_intencao_voto("com_lula"),
      "intencao2":   grafico_intencao_voto("sem_lula"),
      "evolucao":    grafico_evolucao(),
      "mc":          grafico_monte_carlo(relatorio),
      "segundo":     grafico_segundo_turno(relatorio),
      "rejeicao":    grafico_rejeicao(),
      "projecao":    grafico_projecao(relatorio),
      "historico":   grafico_historico_eleicoes(),
    }

    # Carregar dados em tempo real se existirem
    manchetes = []
    pesquisas = []
    try:
      with open("dados_tempo_real.json", encoding="utf-8") as f:
        dados_rt = json.load(f)
        manchetes = dados_rt.get("cnnbrasil", {}).get("manchetes", [])
        pesquisas = dados_rt.get("pollingdata", {}).get("pesquisas", [])
    except Exception:
      pass

    # exporta cada fig como div HTML
    divs = {k: fig.to_html(full_html=False, include_plotlyjs=False)
            for k, fig in figs.items()}

    # Indicadores do resumo executivo
    mc     = relatorio["monte_carlo_com_lula"]
    lider  = mc.iloc[0]["Candidato"]
    prob1  = mc.iloc[0]["P(1º lugar) (%)"]

    comp   = relatorio["competitividade"]
    tendencias = relatorio["tendencias"]

    # badges de tendência
    def badge_tend(cand):
        t = tendencias.get(cand, {})
        return t.get("direcao", "")


    html = f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"UTF-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>
  <title>Sistema de Simulação Eleitoral — Brasil 2026</title>
  <script src=\"https://cdn.plot.ly/plotly-2.32.0.min.js\"></script>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\"/>
  <link href=\"https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap\" rel=\"stylesheet\"/>
  <style>
    :root {{
      --bg:       #0A0E1A;
      --card:     #111827;
      --accent:   #00D4FF;
      --accent2:  #FF6B35;
      --text:     #E8ECF4;
      --muted:    #7B8A9E;
      --green:    #00FF88;
      --red:      #FF3366;
      --border:   #1E2535;
      --font-ui:  'Rajdhani', sans-serif;
      --font-mono:'Share Tech Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-ui);
      min-height: 100vh;
    }}

    /* ── HEADER ── */
    header {{
      background: linear-gradient(135deg, #0A0E1A 0%, #0D2040 60%, #0A0E1A 100%);
      border-bottom: 1px solid var(--accent);
      padding: 40px 60px 30px;
      position: relative;
      overflow: hidden;
    }}
    header::before {{
      content: '';
      position: absolute; inset: 0;
      background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 59px,
        #ffffff04 60px
      );
    }}
    .header-grid {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 20px;
      align-items: center;
    }}
    .flag-bar {{
      display: flex; gap: 4px; margin-bottom: 12px;
    }}
    .flag-bar span {{
      height: 4px; border-radius: 2px;
      display: block;
    }}
    h1 {{
      font-size: 2.6rem; font-weight: 700;
      color: var(--accent);
      letter-spacing: 2px;
      text-transform: uppercase;
      font-family: var(--font-ui);
      line-height: 1.1;
    }}
    h1 em {{ color: var(--text); font-style: normal; }}
    .subtitle {{
      color: var(--muted); font-size: 1rem; margin-top: 8px;
      font-family: var(--font-mono);
    }}
    .badge-stack {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
    .badge {{
      background: var(--border); border: 1px solid var(--accent);
      padding: 4px 12px; border-radius: 20px;
      font-size: 0.78rem; font-family: var(--font-mono);
      color: var(--accent);
    }}

    /* ── INDICADORES TOPO ── */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      padding: 24px 60px;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-top: 3px solid var(--accent);
      padding: 18px 22px;
      border-radius: 4px;
    }}
    .kpi-label {{
      font-family: var(--font-mono); font-size: 0.72rem;
      color: var(--muted); text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .kpi-value {{
      font-size: 2.2rem; font-weight: 700;
      color: var(--accent); margin-top: 4px;
      font-family: var(--font-ui);
    }}
    .kpi-sub {{
      font-size: 0.82rem; color: var(--muted); margin-top: 2px;
    }}

    /* ── SEÇÕES ── */
    .section {{
      padding: 16px 60px;
    }}
    .section-title {{
      font-family: var(--font-mono);
      font-size: 0.8rem; color: var(--muted);
      text-transform: uppercase; letter-spacing: 2px;
      border-left: 3px solid var(--accent2);
      padding-left: 12px; margin-bottom: 16px;
    }}
    .grid-2 {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
    }}
    .chart-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 4px;
      overflow: hidden;
    }}
    .chart-card.full {{ grid-column: 1 / -1; }}

    /* ── CANDIDATOS CARDS ── */
    .candidates-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      padding: 16px 60px;
    }}
    .cand-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 14px;
      position: relative;
      overflow: hidden;
    }}
    .cand-card::before {{
      content: '';
      position: absolute; top: 0; left: 0; right: 0; height: 3px;
    }}
    .cand-name {{ font-size: 1rem; font-weight: 700; }}
    .cand-party {{ font-size: 0.78rem; color: var(--muted); }}
    .cand-meta {{ font-size: 0.75rem; color: var(--muted); margin-top: 6px; }}
    .cand-intencao {{
      font-size: 1.8rem; font-weight: 700;
      color: var(--accent); margin-top: 6px;
    }}
    .cand-tend {{ font-size: 0.82rem; margin-top: 4px; }}
    .inelegivel-tag {{
      display: inline-block;
      background: #FF336622; border: 1px solid var(--red);
      color: var(--red);
      padding: 2px 8px; border-radius: 3px;
      font-size: 0.7rem; font-family: var(--font-mono);
      margin-top: 4px;
    }}

    /* ── TABS ── */
    .tab-row {{ display: flex; gap: 0; margin-bottom: -1px; }}
    .tab-btn {{
      background: var(--card); border: 1px solid var(--border);
      border-bottom: none; color: var(--muted);
      padding: 10px 22px; cursor: pointer;
      font-family: var(--font-ui); font-size: 0.9rem;
      font-weight: 600; transition: all 0.2s;
    }}
    .tab-btn.active {{ background: var(--bg); color: var(--accent); border-top: 2px solid var(--accent); }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    /* ── FOOTER ── */
    footer {{
      border-top: 1px solid var(--border);
      padding: 24px 60px;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 0.75rem;
      line-height: 1.8;
    }}
    .footer-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
    }}

    @media (max-width: 900px) {{
      header, .kpi-row, .section, .candidates-grid, footer {{
        padding-left: 20px; padding-right: 20px;
      }}
      .kpi-row {{ grid-template-columns: 1fr 1fr; }}
      .candidates-grid {{ grid-template-columns: 1fr 1fr; }}
      .grid-2 {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 1.8rem; }}
    }}
  </style>
</head>
<body>

<!-- ══════════ DADOS EM TEMPO REAL ══════════ -->
<div class=\"section\">
  <div class=\"section-title\">/// DADOS EM TEMPO REAL</div>
  <div style=\"display:grid;grid-template-columns:1fr 1fr;gap:24px;\">
    <div style=\"background:var(--card);padding:18px 20px;border-radius:4px;border:1px solid var(--border);\">
      <div style=\"font-family:var(--font-mono);color:var(--accent);font-size:1.1rem;margin-bottom:8px;\">📰 Manchetes CNN Brasil</div>
      <ul>
        {''.join([f'<li style=\"margin-bottom:6px;\">{m}</li>' for m in manchetes]) if manchetes else '<li style=\"color:var(--muted);\">Nenhuma manchete encontrada.</li>'}
      </ul>
    </div>
    <div style=\"background:var(--card);padding:18px 20px;border-radius:4px;border:1px solid var(--border);\">
      <div style=\"font-family:var(--font-mono);color:var(--accent2);font-size:1.1rem;margin-bottom:8px;\">📊 Últimas Pesquisas PollingData</div>
      <ul>
        {''.join([f'<li style=\"margin-bottom:6px;\">{p}</li>' for p in pesquisas]) if pesquisas else '<li style=\"color:var(--muted);\">Nenhuma pesquisa encontrada.</li>'}
      </ul>
    </div>
  </div>
</div>

<!-- ══════════ HEADER ══════════ -->
<header>
  <div class="header-grid">
    <div>
      <div class="flag-bar">
        <span style="width:80px;background:#009C3B;"></span>
        <span style="width:60px;background:#FEDF00;"></span>
        <span style="width:40px;background:#009C3B;"></span>
      </div>
      <h1>🗳️ Brasil <em>2026</em></h1>
      <p style="font-size:1.4rem;color:var(--muted);font-weight:600;margin-top:4px;">
        Sistema de Simulação Eleitoral
      </p>
      <p class="subtitle">
        Monte Carlo · Regressão Linear · Dados Reais de Pesquisas
      </p>
      <div class="badge-stack">
        <span class="badge">📊 AtlasIntel Abr/2026</span>
        <span class="badge">🎲 50.000 Simulações</span>
        <span class="badge">🔬 Python · Plotly · Scikit-Learn</span>
        <span class="badge">📅 Atualizado: Mai/2026</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:5rem;">🇧🇷</div>
      <div style="font-family:var(--font-mono);color:var(--muted);font-size:0.8rem;">
        ELEIÇÕES GERAIS<br>OUTUBRO 2026
      </div>
    </div>
  </div>
</header>

<!-- ══════════ KPIs ══════════ -->
<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">🥇 Líder nas Pesquisas</div>
    <div class="kpi-value">Lula</div>
    <div class="kpi-sub">PT — 33% intenção de voto</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">🎲 P(1º lugar) — Monte Carlo</div>
    <div class="kpi-value">{prob1}%</div>
    <div class="kpi-sub">Lula lidera em {prob1}% das simulações</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">⚡ Índice de Competitividade</div>
    <div class="kpi-value" style="color:var(--accent2)">{comp}%</div>
    <div class="kpi-sub">100% = disputa definida</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">🔢 Eleitores Aptos (estimativa)</div>
    <div class="kpi-value">~160M</div>
    <div class="kpi-sub">TSE — projeção 2026</div>
  </div>
</div>

<!-- ══════════ CANDIDATOS ══════════ -->
<div class="section">
  <div class="section-title">/// CANDIDATOS PROVÁVEIS 2026</div>
</div>
<div class="candidates-grid">
"""

    candidatos_principais = [
        ("Lula", "com_lula"), ("Flávio Bolsonaro", "com_lula"),
        ("Romeu Zema", "com_lula"), ("Ronaldo Caiado", "com_lula"),
        ("Fernando Haddad", "sem_lula"), ("Ciro Gomes", "com_lula"),
    ]

    for nome, cenario in candidatos_principais:
        info   = CANDIDATOS_2026.get(nome, {})
        cor    = CORES.get(nome, "#888")
        intenc = PESQUISA_ATUAL[cenario].get(nome, 0)
        tend   = relatorio["tendencias"].get(nome, {})
        direcao = tend.get("direcao", "")

        inelegivel_html = ""
        if info.get("inelegivel"):
            inelegivel_html = '<span class="inelegivel-tag">⚠️ INELEGÍVEL ATÉ 2030</span>'

        html += f"""
  <div class="cand-card" style="border-left: 3px solid {cor}">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{cor};"></div>
    <div class="cand-name">{nome}</div>
    <div class="cand-party">{info.get('partido','')}</div>
    {inelegivel_html}
    <div class="cand-intencao">{intenc}%</div>
    <div class="cand-tend">{direcao}</div>
    <div class="cand-meta">
      {info.get('cargo_atual','')}<br/>
      {info.get('ideologia','')} · {info.get('estado','')} · {info.get('idade','')} anos
    </div>
  </div>"""

    html += """
</div>

<!-- ══════════ GRÁFICOS PRINCIPAIS ══════════ -->
<div class="section">
  <div class="section-title">/// ANÁLISE DE INTENÇÃO DE VOTO</div>
  <div class="tab-row">
    <button class="tab-btn active" onclick="showTab('tab-intencao')">Intenção 1º Turno</button>
    <button class="tab-btn" onclick="showTab('tab-evolucao')">Evolução Histórica</button>
    <button class="tab-btn" onclick="showTab('tab-rejeicao')">Rejeição</button>
    <button class="tab-btn" onclick="showTab('tab-historico')">Eleições Anteriores</button>
  </div>

  <div id="tab-intencao" class="tab-content active">
    <div class="grid-2">
      <div class="chart-card">""" + divs["intencao"] + """</div>
      <div class="chart-card">""" + divs["intencao2"] + """</div>
    </div>
  </div>

  <div id="tab-evolucao" class="tab-content">
    <div class="chart-card full">""" + divs["evolucao"] + """</div>
  </div>

  <div id="tab-rejeicao" class="tab-content">
    <div class="chart-card full">""" + divs["rejeicao"] + """</div>
  </div>

  <div id="tab-historico" class="tab-content">
    <div class="chart-card full">""" + divs["historico"] + """</div>
  </div>
</div>

<!-- ══════════ SIMULAÇÃO ══════════ -->
<div class="section">
  <div class="section-title">/// SIMULAÇÃO PROBABILÍSTICA</div>
  <div class="grid-2">
    <div class="chart-card">""" + divs["mc"] + """</div>
    <div class="chart-card">""" + divs["segundo"] + """</div>
  </div>
</div>

<!-- ══════════ PROJEÇÃO ══════════ -->
<div class="section">
  <div class="section-title">/// PROJEÇÃO PARA OUTUBRO 2026</div>
  <div class="chart-card full">""" + divs["projecao"] + """</div>
</div>

<!-- ══════════ FOOTER ══════════ -->
<footer>
  <div class="footer-grid">
    <div>
      <strong style="color:var(--accent)">📚 Fontes de Dados</strong><br/>
      • AtlasIntel/Bloomberg — Pesquisa Nacional Abr/2026 (n=5.008, ±1pp, 95% IC)<br/>
      • Datafolha — Série histórica 2025–2026<br/>
      • PoderData — Levantamentos trimestrais 2025<br/>
      • TSE — Resultados eleitorais 2002–2022<br/>
      • IBGE — Estimativas populacionais
    </div>
    <div>
      <strong style="color:var(--accent)">⚙️ Metodologia</strong><br/>
      • Monte Carlo: 50.000 simulações com ruído gaussiano (σ=2.5pp)<br/>
      • Regressão linear sobre série histórica de pesquisas<br/>
      • Projeção com intervalo de confiança 95%<br/>
      • Modelo de transferência de votos no 2º turno<br/>
      <br/>
      <strong style="color:var(--muted)">⚠️ Aviso:</strong> Simulações não são previsões determinísticas.<br/>
      Desenvolvido para fins acadêmicos e portfólio.
    </div>
  </div>
</footer>

<script>
  function showTab(id) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
  }
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅  Dashboard salvo em: {output_path}")
    return output_path


if __name__ == "__main__":
    gerar_dashboard("dashboard_eleitoral.html")
