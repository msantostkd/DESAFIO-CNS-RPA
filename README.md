# Desafio Técnico: Integração com API Bancária (Python e UiPath)

Este projeto contém duas soluções (Python e UiPath) para o desafio técnico de integração com a API do Banco do Brasil (Sandbox), abrangendo autenticação OAuth2, consulta de extratos de múltiplas contas e geração de planilhas consolidadas e logs de execução.

---

## 1. Solução Python

O código em Python (`main.py`) é responsável por orquestrar todo o processo de API e manipulação de dados.

### 1.1 Estrutura do Projeto Python

A pasta raiz contém os seguintes arquivos principais da solução Python:

* `main.py`: O script principal que contém as classes e a lógica de processamento.
* `requirements.txt`: Lista de dependências Python.
* `contas_input.xlsx`: Planilha de entrada com as contas a serem processadas (gerada automaticamente se não existir).
* `extrato_consolidado.xlsx`: **Arquivo de saída principal** (com as abas de extrato e logs).
* `collection.postman.json`: Collection Postman para teste manual das requisições (Requisito 2.5).
* `execucao.log`: Log detalhado da execução do script.

### 1.2 Configuração e Execução

Para rodar a solução Python, siga os passos abaixo:

#### 1. Configurar o Ambiente Virtual (venv)

python -m venv venv
# Ative o ambiente
source venv/bin/activate  # Linux/macOS
# ou .\venv\Scripts\activate  # Windows (PowerShell)

