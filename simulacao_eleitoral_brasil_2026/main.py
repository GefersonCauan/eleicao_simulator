import subprocess
import sys
import os

def atualizar_dados_em_tempo_real():
    """
    Exemplo de função para buscar dados em tempo real.
    Faz scraping básico das páginas da CNN Brasil e PollingData.
    """
    import requests
    from bs4 import BeautifulSoup
    import json
    from datetime import datetime

    dados = {}

    print("[INFO] Buscando dados em tempo real da CNN Brasil...")
    manchetes = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        url_cnn = "https://www.cnnbrasil.com.br/politica/"
        resp_cnn = requests.get(url_cnn, timeout=10, headers=headers)
        soup_cnn = BeautifulSoup(resp_cnn.text, 'html.parser')
        
        # Procurar por elementos de notícia mais específicos
        artigos = soup_cnn.find_all('h3', class_=lambda x: x and 'headline' in x.lower() if x else False)
        if not artigos:
            artigos = soup_cnn.find_all('h2', limit=10)
        
        manchetes = [art.get_text(strip=True) for art in artigos if art.get_text(strip=True)][:5]
        
        if not manchetes:
            manchetes = ["📰 Dados eleitorais da CNN Brasil", "🗳️ Cobertura política atualizada"]
        
        print("Principais manchetes CNN Brasil:")
        for m in manchetes:
            print("-", m)
    except Exception as e:
        print(f"[AVISO] Usando dados padrão da CNN Brasil: {e}")
        manchetes = ["📰 Cobertura de eleições 2026", "🗳️ Pesquisas atualizadas"]
    
    dados['cnnbrasil'] = {
        'data_coleta': datetime.now().isoformat(),
        'manchetes': manchetes
    }

    print("[INFO] Buscando dados em tempo real do PollingData...")
    pesquisas = []
    try:
        url_polling = "https://www.pollingdata.com.br/"
        resp_polling = requests.get(url_polling, timeout=10, headers=headers)
        soup_polling = BeautifulSoup(resp_polling.text, 'html.parser')
        
        # Procurar por pesquisas em divs ou tables específicas
        pesquisa_items = soup_polling.find_all(['tr', 'div'], class_=lambda x: x and any(
            w in x.lower() for w in ['pesquisa', 'poll', 'resultado', 'survey']
        ) if x else False)
        
        if not pesquisa_items:
            pesquisa_items = soup_polling.find_all('article', limit=5)
        
        pesquisas = [p.get_text(strip=True)[:100] for p in pesquisa_items if p.get_text(strip=True)][:5]
        
        if not pesquisas:
            pesquisas = ["📊 Pesquisa eleitoral 2026", "🎯 Intenção de voto atualizada"]
        
        print("Últimas pesquisas PollingData:")
        for p in pesquisas:
            print("-", p[:80])
    except Exception as e:
        print(f"[AVISO] Usando dados padrão do PollingData: {e}")
        pesquisas = ["📊 Pesquisas eleitorais recentes", "🎯 Tendências de voto"]
    dados['pollingdata'] = {
        'data_coleta': datetime.now().isoformat(),
        'pesquisas': pesquisas
    }

    # Salvar em JSON
    try:
        with open('dados_tempo_real.json', 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print("[INFO] Dados salvos em dados_tempo_real.json")
    except Exception as e:
        print(f"[ERRO] Não foi possível salvar o arquivo JSON: {e}")

def rodar_simulacao_terminal():
    print("[INFO] Rodando simulador de terminal...")
    subprocess.run([sys.executable, "simulador_terminal.py"])

def gerar_dashboard():
    print("[INFO] Gerando dashboard HTML...")
    subprocess.run([sys.executable, "gerar_dashboard.py"])
    print("[INFO] Dashboard gerado!")
    dashboard_path = os.path.abspath("dashboard_eleitoral_brasil_2026.html")
    try:
        if sys.platform.startswith('win'):
            os.startfile(dashboard_path)
        elif sys.platform.startswith('darwin'):
            subprocess.run(['open', dashboard_path])
        else:
            subprocess.run(['xdg-open', dashboard_path])
    except Exception as e:
        print(f"[WARN] Não foi possível abrir o dashboard automaticamente: {e}")

def main():
    atualizar_dados_em_tempo_real()
    rodar_simulacao_terminal()
    gerar_dashboard()

if __name__ == "__main__":
    main()
