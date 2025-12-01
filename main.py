#!/usr/bin/env python3
# main.py — BankingAutomator (versão integrada com correções de autenticação e formato da API de extratos)

import os
import logging
import base64
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# --- CONFIGURAÇÕES DO PROJETO (sem credenciais sensíveis hardcoded) ---
CONFIG = {
    "APP_KEY": "2dc673fdaa5e4db68f1019d2d9027c01",
    "AUTH_URL": "https://oauth.hm.bb.com.br/oauth/token",
    "API_URL": "https://api.hm.bb.com.br/extratos/v1/conta-corrente/agencia/{agencia}/conta/{conta}",
    "INPUT_FILE": "contas_input.xlsx",
    "OUTPUT_FILE": "extrato_consolidado.xlsx",
    "MOCK_MODE": False
}

# --- LOG ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("execucao.log"),
        logging.StreamHandler()
    ]
)

print("=== Iniciando main.py — BankingAutomator ===")

class BankingAutomator:
    def __init__(self):
        self.token = None
        self.logs_execucao = []

    def _gerar_input_teste(self):
        """Gera arquivo de input se não existir (massa de teste)."""
        if not os.path.exists(CONFIG["INPUT_FILE"]):
            logging.info("Arquivo de input não encontrado. Gerando massa de teste...")
            df = pd.DataFrame({
                'MCITest': ['26968930', '178961031', '704950857'],
                'Agencia': ['551', '1505', '452'],
                'Conta': ['5087', '1348', '123873']
            })
            df.to_excel(CONFIG["INPUT_FILE"], index=False)

    def autenticar(self):
        """
        Autenticação OAuth2:
        - Tenta obter client_id/secret das variáveis de ambiente BB_CLIENT_ID / BB_CLIENT_SECRET (strip).
        - Se não definidas, usa fallback literal somente para teste local.
        - Faz POST para /oauth/token usando HTTPBasicAuth (sem scope primeiro, depois com scope).
        """
        logging.info("Iniciando autenticação OAuth2 (modo seguro)...")

        # ler variáveis de ambiente e strip
        env_client_id = os.getenv("BB_CLIENT_ID")
        env_client_secret = os.getenv("BB_CLIENT_SECRET")
        client_id = env_client_id.strip() if env_client_id is not None else None
        client_secret = env_client_secret.strip() if env_client_secret is not None else None

        # fallback literal (apenas para testes locais; prefira definir variáveis de ambiente)
        fallback_client_id = "eyJpZCI6ImU0NTYiLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6MTYzMDUwLCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6MX0"
        fallback_client_secret = "eyJpZCI6IjkzY2Q2NGQtNWE5Yy00ZTA5LTk4ZmEtYmI0ZDcyMDIyMyIsImNvZGlnb1B1YmxpY2Fkb3IiOjAsImNvZGlnb1NvZnR3YXJlIjoxNjMwNTAsInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoxLCJzZXF1ZW5jaWFsQ3JlZGVuY2lhbCI6MiwiYW1iaWVudGUiOiJob21vbG9nYWNhbyIsImlhdCI6MTc2NDA3NjYwMzQ5OX0"

        if client_id and client_secret:
            logging.info("Usando credenciais provenientes de variáveis de ambiente (após strip).")
        else:
            logging.info("Variáveis de ambiente não definidas ou incompletas — usando fallback literal para teste.")
            client_id = client_id or fallback_client_id
            client_secret = client_secret or fallback_client_secret

        if CONFIG["MOCK_MODE"]:
            self.token = "mock_token_123456"
            logging.info("Autenticação MOCK realizada com sucesso.")
            return True

        url = CONFIG["AUTH_URL"]
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # 1) tentar sem scope (corresponde ao seu teste isolado que funcionou)
        try:
            payload_simple = {"grant_type": "client_credentials"}
            logging.info("[T1] Tentativa de token (sem scope)...")
            r = requests.post(url, headers=headers, data=payload_simple,
                              auth=HTTPBasicAuth(client_id, client_secret), timeout=15)
            logging.info(f"[T1] status={r.status_code} resp (preview): {r.text[:300]}")
            if r.status_code == 200 and r.json().get("access_token"):
                self.token = r.json().get("access_token")
                logging.info("Autenticação sucedida (sem scope).")
                return True
        except Exception as e:
            logging.warning(f"Exceção na tentativa sem scope: {e}")

        # 2) tentar com scope (fallback)
        try:
            payload_scope = {"grant_type": "client_credentials", "scope": "extratos.leitura"}
            logging.info("[T2] Tentativa de token (com scope)...")
            r2 = requests.post(url, headers=headers, data=payload_scope,
                               auth=HTTPBasicAuth(client_id, client_secret), timeout=15)
            logging.info(f"[T2] status={r2.status_code} resp (preview): {r2.text[:300]}")
            if r2.status_code == 200 and r2.json().get("access_token"):
                self.token = r2.json().get("access_token")
                logging.info("Autenticação sucedida (com scope).")
                return True
        except Exception as e:
            logging.warning(f"Exceção na tentativa com scope: {e}")

        logging.error("Falha em ambas as tentativas de autenticação. Verifique credenciais e ambiente (homolog/prod).")
        return False

    def consultar_extrato(self, agencia, conta, mcitest):
        """
        Consulta o extrato - versão corrigida:
        - GET /conta-corrente/agencia/{agencia}/conta/{conta}
        - Parâmetros na query: gw-dev-app-key, dataInicioSolicitacao (DDMMAAAA int), dataFimSolicitacao (DDMMAAAA int),
          numeroPaginaSolicitacao (int), quantidadeRegistroPaginaSolicitacao (int)
        - Envia também o header x-br-com-bb-ipa-mciteste por compatibilidade.
        """
        if CONFIG["MOCK_MODE"]:
            return {
                "listaLancamento": [
                    {"dataLancamento": "15/11/2023", "numeroDocumento": "1001", "valorLancamento": 150.00, "textoDescricaoHistorico": "PIX RECEBIDO"},
                ]
            }, None

        extrato_url = CONFIG["API_URL"].format(agencia=agencia, conta=conta)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-Developer-Application-Key": CONFIG["APP_KEY"],
            # MCITest em header (algumas integrações exigem)
            "x-br-com-bb-ipa-mciteste": str(mcitest)
        }

        # --- ATENÇÃO AO FORMATO DAS DATAS: DDMMAAAA (sem pontos) ---
        # Ajuste aqui as datas conforme o período desejado
        # Se preferir, pode extrair das colunas/entrada para parametrizar por conta.
        data_inicio = "0"   # Ex: 01/11/2024 -> "01112024"
        data_fim   = "0"    # Ex: 30/11/2024 -> "30112024"

        params = {
            "gw-dev-app-key": CONFIG["APP_KEY"],
            "dataInicioSolicitacao": int(data_inicio),
            "dataFimSolicitacao": int(data_fim),
            "numeroPaginaSolicitacao": 1,              # inteiro
            "quantidadeRegistroPaginaSolicitacao": 200 # inteiro (50..200 conforme spec)
        }

        # Gerar URL de debug
        try:
            full_request_url = requests.Request('GET', extrato_url, params=params).prepare().url
            logging.info(f"URL de Requisição (GET) (Conta {agencia}-{conta}): {full_request_url}")
        except Exception as e:
            logging.warning(f"Não foi possível gerar a URL de debug: {e}")

        try:
            r = requests.get(extrato_url, headers=headers, params=params, timeout=20)
            logging.info(f"GET -> status={r.status_code}. resp (inic): {r.text[:400]}")
            if r.status_code == 200:
                return r.json(), None
            else:
                return None, f"Erro HTTP {r.status_code}: {r.text}"
        except requests.exceptions.HTTPError as e:
            return None, f"Erro HTTP {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return None, f"Erro genérico na consulta do extrato: {e}"

    def processar(self):
        logging.info("Iniciando processo de processamento de contas...")
        self._gerar_input_teste()

        try:
            df_contas = pd.read_excel(CONFIG["INPUT_FILE"], dtype=str)
            logging.info(f"Base de contas carregada. Total: {len(df_contas)} contas.")
        except Exception as e:
            logging.critical(f"Não foi possível ler o arquivo de entrada: {e}")
            return

        if not self.autenticar():
            logging.error("Autenticação falhou — abortando processo.")
            return

        abas_excel = {}

        for _, row in df_contas.iterrows():
            mcitest = row.get('MCITest')
            agencia = row['Agencia']
            conta = row['Conta']
            chave_conta = f"{agencia}-{conta}"

            logging.info(f"Processando conta: {chave_conta} (MCITest: {mcitest})")

            dados_json, erro = self.consultar_extrato(agencia, conta, mcitest)

            if erro:
                logging.error(f"Falha na conta {chave_conta}: {erro}")
                self.logs_execucao.append({
                    "Agencia": agencia,
                    "Conta": conta,
                    "Status": "FALHA",
                    "Detalhe": erro
                })
            else:
                try:
                    # Chave JSON de lista de lançamentos
                    lista_lancamentos = dados_json.get('listaLancamento', dados_json.get('data', []))
                    df_extrato = pd.DataFrame(lista_lancamentos)

                    logging.info(f"Conta {chave_conta}: Encontrados {len(df_extrato)} lançamentos.")

                    # Colunas obrigatórias (se não existir, cria vazia)
                    cols_desejadas = ['dataLancamento', 'numeroDocumento', 'valorLancamento', 'textoDescricaoHistorico']
                    df_extrato = df_extrato[cols_desejadas] if not df_extrato.empty else pd.DataFrame(columns=cols_desejadas)

                    abas_excel[chave_conta] = df_extrato
                    self.logs_execucao.append({
                        "Agencia": agencia,
                        "Conta": conta,
                        "Status": "OK",
                        "Detalhe": "Processado com sucesso"
                    })
                    logging.info(f"Conta {chave_conta} processada com sucesso.")
                except Exception as e:
                    logging.error(f"Erro ao processar JSON da conta {chave_conta}: {e}")
                    self.logs_execucao.append({
                        "Agencia": agencia,
                        "Conta": conta,
                        "Status": "FALHA",
                        "Detalhe": "Erro de Parse JSON"
                    })

        self.gerar_planilha_consolidada(abas_excel)

    def gerar_planilha_consolidada(self, abas_dados):
        logging.info("Gerando planilha consolidada...")

        try:
            with pd.ExcelWriter(CONFIG["OUTPUT_FILE"], engine='openpyxl') as writer:
                df_log = pd.DataFrame(self.logs_execucao)
                df_log.to_excel(writer, sheet_name='Log_Execucao', index=False)
                for nome_aba, df in abas_dados.items():
                    nome_safe = nome_aba[:31]
                    df.to_excel(writer, sheet_name=nome_safe, index=False)
            logging.info(f"Arquivo '{CONFIG['OUTPUT_FILE']}' gerado com sucesso!")
        except Exception as e:
            logging.error(f"Erro ao salvar Excel: {e}")

if __name__ == "__main__":
    bot = BankingAutomator()
    bot.processar()
    print("=== main.py finalizado ===")
