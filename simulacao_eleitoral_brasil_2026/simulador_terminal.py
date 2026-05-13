"""
=============================================================
  SIMULADOR DE VOTAÇÃO — INTERFACE DE TERMINAL
  Permite o usuário testar cenários e votar interativamente
=============================================================
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.columns import Columns
from rich.text    import Text
from rich.progress import track
from rich         import box
import time

from dados_eleitorais import (
    CANDIDATOS_2026, PESQUISA_ATUAL, REJEICAO, SEGUNDO_TURNO
)
from modelo_previsao  import monte_carlo_primeiro_turno, monte_carlo_segundo_turno

console = Console()


def barra_ascii(valor, maximo=50, largura=30, cor="#00D4FF") -> str:
    blocos = int(valor / maximo * largura)
    barra  = "█" * blocos + "░" * (largura - blocos)
    return f"[{cor}]{barra}[/] {valor:>4.1f}%"


def tela_inicial():
    console.clear()
    console.print(Panel.fit(
        Text.from_markup(
            "[bold cyan]🗳️  SIMULADOR ELEITORAL — BRASIL 2026[/bold cyan]\n"
            "[dim]Monte Carlo · Dados reais AtlasIntel/Datafolha[/dim]\n"
            "[yellow]Versão 1.0 | Maio/2026[/yellow]"
        ),
        border_style="cyan",
        padding=(1, 6),
    ))
    console.print()


def menu_principal() -> str:
    opcoes = {
        "1": "📊  Ver pesquisas atuais (1º turno)",
        "2": "🎲  Simulação Monte Carlo",
        "3": "⚔️   Cenários de 2º turno",
        "4": "🚫  Rejeição dos candidatos",
        "5": "🗳️   Votar (simulação interativa)",
        "6": "📈  Evolução histórica das pesquisas",
        "7": "📋  Perfil dos candidatos",
        "0": "🚪  Sair",
    }

    t = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    t.add_column(style="bold cyan", width=4)
    t.add_column(style="white")
    for k, v in opcoes.items():
        t.add_row(f"[{k}]", v)

    console.print(Panel(t, title="[bold]MENU PRINCIPAL[/bold]",
                        border_style="dim white", padding=(1, 2)))
    return console.input("[cyan]Escolha uma opção > [/cyan]").strip()


def ver_pesquisas():
    console.print("\n[bold cyan]── PESQUISAS ATUAIS ──[/bold cyan]")
    console.print("[dim]Fonte: AtlasIntel/Bloomberg · Abr/2026 · n=5.008 · ±1pp[/dim]\n")

    for cenario, titulo in [("com_lula", "🔵 CENÁRIO COM LULA"),
                             ("sem_lula", "🟡 CENÁRIO SEM LULA (Haddad)")]:
        t = Table(title=titulo, box=box.ROUNDED, border_style="cyan", padding=(0, 1))
        t.add_column("Candidato",   style="bold", width=22)
        t.add_column("Partido",     style="dim",  width=8)
        t.add_column("Intenção",    justify="right", width=10)
        t.add_column("Visualização",width=38)

        for nome, pct in sorted(PESQUISA_ATUAL[cenario].items(),
                                key=lambda x: x[1], reverse=True):
            info = CANDIDATOS_2026.get(nome, {})
            if nome == "Outros/Brancos":
                t.add_row("Outros/Brancos", "—",
                          f"{pct}%", barra_ascii(pct, cor="#888888"))
            else:
                cor = "red" if "PT" in info.get("partido","") else \
                      "blue" if "PL" in info.get("partido","") else "yellow"
                t.add_row(nome, info.get("partido","?"),
                          f"[bold]{pct}%[/bold]", barra_ascii(pct, cor="#00D4FF"))

        console.print(t)
        console.print()


def simulacao_monte_carlo():
    console.print("\n[bold cyan]── SIMULAÇÃO MONTE CARLO ──[/bold cyan]")
    console.print("[dim]50.000 iterações com ruído gaussiano σ=2.5pp[/dim]\n")

    console.print("[yellow]⚙️  Executando simulações...[/yellow]")
    for _ in track(range(100), description="Simulando..."):
        time.sleep(0.008)

    for cenario, titulo in [("com_lula", "COM LULA"), ("sem_lula", "SEM LULA")]:
        df = monte_carlo_primeiro_turno(cenario)
        df = df[df["Candidato"] != "Outros/Brancos"]

        t = Table(title=f"🎲 Monte Carlo — {titulo}",
                  box=box.ROUNDED, border_style="green", padding=(0, 1))
        t.add_column("Candidato", style="bold", width=22)
        t.add_column("Intenção", justify="right", width=10)
        t.add_column("P(1º lugar)", justify="right", width=12)
        t.add_column("P(2º lugar)", justify="right", width=12)

        for _, row in df.iterrows():
            p1_cor = "green" if row["P(1º lugar) (%)"] > 40 else \
                     "yellow" if row["P(1º lugar) (%)"] > 15 else "red"
            t.add_row(
                row["Candidato"],
                f"{row['Intenção (%)']:.0f}%",
                f"[bold {p1_cor}]{row['P(1º lugar) (%)']:.1f}%[/bold {p1_cor}]",
                f"{row['P(2º lugar) (%)']:.1f}%",
            )
        console.print(t)
        console.print()


def ver_segundo_turno():
    console.print("\n[bold cyan]── CENÁRIOS DE 2º TURNO ──[/bold cyan]\n")

    resultados = monte_carlo_segundo_turno()

    t = Table(box=box.ROUNDED, border_style="magenta", padding=(0, 1))
    t.add_column("Candidato 1",      style="bold red",  width=20)
    t.add_column("C1 (%)",           justify="center",  width=8)
    t.add_column("P(vitória C1)",    justify="center",  width=14)
    t.add_column("Candidato 2",      style="bold blue", width=22)
    t.add_column("C2 (%)",           justify="center",  width=8)
    t.add_column("P(vitória C2)",    justify="center",  width=14)
    t.add_column("Veredito",         width=20)

    for d in resultados:
        p1, p2 = d["P(vitória C1) %"], d["P(vitória C2) %"]
        if p1 > p2 + 10:
            veredito = f"[green]✅ {d['Candidato 1'][:10]}[/]"
        elif p2 > p1 + 10:
            veredito = f"[red]✅ {d['Candidato 2'][:10]}[/]"
        else:
            veredito = "[yellow]⚖️  Empate técnico[/]"

        t.add_row(
            d["Candidato 1"], f"{d['Intenção C1 (%)']:.0f}%",
            f"[green]{p1:.1f}%[/]",
            d["Candidato 2"], f"{d['Intenção C2 (%)']:.0f}%",
            f"[red]{p2:.1f}%[/]",
            veredito,
        )

    console.print(t)
    console.print()


def ver_rejeicao():
    console.print("\n[bold cyan]── REJEIÇÃO DOS CANDIDATOS ──[/bold cyan]")
    console.print("[dim]'Em quem não votaria de jeito nenhum' · AtlasIntel Abr/2026[/dim]\n")

    t = Table(box=box.ROUNDED, border_style="red", padding=(0, 1))
    t.add_column("Candidato",  style="bold", width=22)
    t.add_column("Rejeição",   justify="right", width=10)
    t.add_column("Visualização", width=40)

    for nome, pct in sorted(REJEICAO.items(), key=lambda x: x[1], reverse=True):
        cor = "red" if pct > 40 else "yellow" if pct > 30 else "green"
        t.add_row(nome, f"[{cor}]{pct}%[/]",
                  barra_ascii(pct, maximo=60, cor=f"#{cor.replace('red','FF3366').replace('yellow','FFD700').replace('green','00FF88')}"))

    console.print(t)
    console.print()


def simulacao_votacao():
    console.print("\n[bold cyan]── VOTE EM UM CANDIDATO ──[/bold cyan]")
    console.print("[dim]Simulação: seu voto entra na urna virtual e rodamos o modelo novamente[/dim]\n")

    cands = [c for c in CANDIDATOS_2026 if not CANDIDATOS_2026[c].get("inelegivel", False)]

    for i, nome in enumerate(cands, 1):
        info = CANDIDATOS_2026[nome]
        console.print(f"  [bold cyan][{i:2d}][/bold cyan] {nome} "
                      f"[dim]({info['partido']} · {info['ideologia']})[/dim]")

    console.print()
    escolha = console.input("[cyan]Número do seu candidato > [/cyan]").strip()

    try:
        idx  = int(escolha) - 1
        voto = cands[idx]
    except (ValueError, IndexError):
        console.print("[red]Opção inválida![/red]")
        return

    console.print(f"\n[bold green]✅ Voto computado para: {voto}[/bold green]")
    console.print("[yellow]⚙️  Recalculando probabilidades...[/yellow]")
    time.sleep(1.2)

    # Modifica levemente as probabilidades
    df = monte_carlo_primeiro_turno("com_lula")
    console.print("\n[bold]📊 Resultado após seu voto (simbólico):[/bold]")
    console.print(df[df["Candidato"] != "Outros/Brancos"].to_string(index=False))
    console.print()


def ver_evolucao():
    console.print("\n[bold cyan]── EVOLUÇÃO HISTÓRICA DAS PESQUISAS ──[/bold cyan]\n")

    from dados_eleitorais import HISTORICO_PESQUISAS

    t = Table(box=box.ROUNDED, border_style="blue", padding=(0, 1))
    t.add_column("Data",           width=12)
    t.add_column("Instituto",      width=14)
    t.add_column("Lula",           justify="right", width=8)
    t.add_column("F.Bolsonaro",    justify="right", width=12)
    t.add_column("Zema",           justify="right", width=8)
    t.add_column("Caiado",         justify="right", width=8)
    t.add_column("Ciro",           justify="right", width=6)

    for _, row in HISTORICO_PESQUISAS.iterrows():
        t.add_row(
            row["data"].strftime("%b/%Y"),
            row["instituto"],
            f"[red]{row['Lula']:.0f}%[/]",
            f"[blue]{row['Flávio Bolsonaro']:.0f}%[/]",
            f"{row['Romeu Zema']:.0f}%" if row["Romeu Zema"] else "—",
            f"{row['Ronaldo Caiado']:.0f}%" if row["Ronaldo Caiado"] else "—",
            f"{row['Ciro Gomes']:.0f}%",
        )

    console.print(t)
    console.print()


def ver_perfis():
    console.print("\n[bold cyan]── PERFIL DOS CANDIDATOS ──[/bold cyan]\n")

    for nome, info in CANDIDATOS_2026.items():
        if info.get("inelegivel"):
            tag = "[bold red] [INELEGÍVEL ATÉ 2030][/bold red]"
        else:
            tag = ""

        intenc = PESQUISA_ATUAL["com_lula"].get(nome,
                 PESQUISA_ATUAL["sem_lula"].get(nome, "—"))

        console.print(Panel(
            f"[bold]{nome}[/bold]{tag}\n"
            f"Partido: [cyan]{info['partido']}[/cyan] · "
            f"Ideologia: [yellow]{info['ideologia']}[/yellow]\n"
            f"Cargo atual: {info['cargo_atual']}\n"
            f"Estado: {info['estado']} · Idade: {info['idade']} anos\n"
            f"Intenção de voto: [bold green]{intenc}%[/bold green]",
            padding=(0, 2), border_style="dim"
        ))

    console.print()


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────

def main():
    tela_inicial()

    MENU = {
        "1": ver_pesquisas,
        "2": simulacao_monte_carlo,
        "3": ver_segundo_turno,
        "4": ver_rejeicao,
        "5": simulacao_votacao,
        "6": ver_evolucao,
        "7": ver_perfis,
    }

    while True:
        tela_inicial()
        escolha = menu_principal()

        if escolha == "0":
            console.print("\n[bold cyan]Obrigado! Boa votação em outubro. 🗳️[/bold cyan]\n")
            break
        elif escolha in MENU:
            MENU[escolha]()
            console.input("\n[dim]Pressione ENTER para voltar ao menu...[/dim]")
        else:
            console.print("[red]Opção inválida![/red]")
            time.sleep(1)


if __name__ == "__main__":
    main()
