# Simulação Eleitoral Brasil 2026

Este projeto realiza simulações eleitorais para o cenário brasileiro de 2026, permitindo prever resultados, analisar dados eleitorais e visualizar informações em dashboards interativos.

## Funcionalidades
- Simulação de cenários eleitorais
- Previsão de resultados baseada em modelos estatísticos
- Visualização de dados em dashboard HTML
- Interface de uso via terminal

## Estrutura do Projeto
- `dados_eleitorais.py`: Manipulação e análise dos dados eleitorais
- `modelo_previsao.py`: Modelos de previsão e simulação
- `simulador_terminal.py`: Interface de simulação via terminal
- `gerar_dashboard.py`: Geração do dashboard HTML
- `dashboard_eleitoral_brasil_2026.html`: Dashboard interativo

## Como usar
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o simulador pelo terminal:
   ```bash
   python simulador_terminal.py
   ```
3. Para gerar o dashboard:
   ```bash
   python gerar_dashboard.py
   ```
4. Abra o arquivo `dashboard_eleitoral_brasil_2026.html` no navegador para visualizar os resultados.

## Requisitos
- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

## Contribuição
Contribuições são bem-vindas! Abra uma issue ou envie um pull request.

## Licença
Este projeto está licenciado sob a licença MIT.
