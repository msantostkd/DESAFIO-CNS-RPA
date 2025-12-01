# 📝 DESAFIO TÉCNICO: INTEGRAÇÃO DE API BANCÁRIA (Python e UiPath)

### Visão Geral do Projeto

Este repositório contém a solução completa para o Desafio Técnico de Extração de Extratos via API, implementada em duas abordagens:

1.  **Python:** Solução via código puro, utilizando bibliotecas para chamadas API e manipulação de Excel.
2.  **UiPath:** Solução via automação RPA, utilizando a atividade **HTTP Request** e manipulação de `DataTable` e JSON.

Ambas as soluções realizam a autenticação **OAuth2 (Client Credentials)** e processam uma lista de contas de entrada para gerar uma planilha master consolidada.

---

## 🚀 1. Configuração e Execução da Solução UiPath

Esta seção atende aos requisitos de documentação do projeto UiPath.

### 1.1 Pré-requisitos e Bibliotecas Necessárias

* **Software:** UiPath Studio (Versão **2026.0.181 STS**).
* **Dependências (Bibliotecas):**
    * `UiPath.System.Activities` (Padrão).
    * `UiPath.WebAPI.Activities` (Essencial para as chamadas HTTP Request, autenticação OAuth2 e manipulação JSON).
    * `UiPath.Excel.Activities` (Para leitura de dados de contas e gravação do relatório final).

### 1.2 Estrutura de Entrada e Saída

* **Arquivo de Entrada:** `contas_input.xlsx`. Deve estar na raiz do projeto e conter as colunas **Agencia** e **Conta**.
* **Arquivo de Saída:** `extrato_consolidado.xlsx` (Será criado/atualizado durante a execução). A planilha final deve ser idêntica à gerada pelo código Python.

### 1.3 Instruções de Abertura e Execução

1.  **Abertura:** Abra a pasta do projeto (`DESAFIO-CNS-RPA`) diretamente no **UiPath Studio**.
2.  **Configuração de Credenciais:** Antes de rodar, verifique o bloco inicial de autenticação para garantir que as variáveis (Client ID, Secret, **GW-DEV-APP-KEY**) estejam configuradas corretamente no escopo `Main`.
3.  **Execução:** Utilize o botão **Run File** (ou **Debug File**) na aba Design do Studio para iniciar o robô.
4.  **Tratamento de Exceções:** O robô foi configurado para **continuar a execução** mesmo após falha na consulta de contas específicas. O resultado da execução será registrado na aba `Log_Execucao`.

---

## 🐍 2. Configuração e Execução da Solução Python

Esta seção atende aos requisitos de documentação do projeto Python.

### 2.1 Configuração do Ambiente Virtual e Dependências

É altamente recomendável utilizar um ambiente virtual para gerenciar as dependências do projeto.

1.  **Criação do Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```
2.  **Ativação do Ambiente:**
    * **Windows:** `venv\Scripts\activate`
    * **macOS/Linux:** `source venv/bin/activate`
3.  **Instalação de Dependências:** Instale as bibliotecas necessárias (`requests` para API e `pandas` para Excel):
    ```bash
    pip install requests pandas openpyxl
    ```

### 2.2 Configuração de Credenciais no Código

1.  Abra o arquivo principal do script Python (`main.py`).
2.  Localize a seção de configuração (`CONFIGURAÇÃO` ou similar) e **insira suas credenciais** (Client ID, Secret, GW-DEV-APP-KEY) nos placeholders definidos.

### 2.3 Instruções de Execução

1.  Certifique-se de que o ambiente virtual está **ativo**.
2.  Execute o script diretamente no terminal:
    ```bash
    python [NOME_DO_SEU_SCRIPT].py
    ```
3.  **Resultado:** O script irá gerar o arquivo `extrato_master_python.xlsx` com o extrato em abas por conta (formato `agencia-conta`) e o log de execução.

---

## 3. Entrega Adicional (Postman e Versionamento)

### 3.1 Chamada Manual via Postman

A Collection do Postman utilizada para testes manuais e validação das chamadas API (Autenticação e Extrato) está inclusa no repositório. O arquivo exportado é:

* `[NOME_DO_ARQUIVO_POSTMAN.json]`

### 3.2 Versionamento GitHub

O projeto (incluindo código Python, pasta UiPath e documentação) foi entregue em um repositório público.
