import requests
import pandas as pd
import logging
import os
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- CONFIGURAÇÕES DO PROJETO ---
CONFIG = {
    "CLIENT_ID": os.getenv("BB_CLIENT_ID", "seu_client_id_aqui"),
    "CLIENT_SECRET": os.getenv("BB_CLIENT_SECRET", "seu_client_secret_aqui"),
    "APP_KEY": os.getenv("BB_APP_KEY", "sua_developer_app_key_aqui"),
    "AUTH_URL": "https://oauth.sandbox.bb.com.br/oauth/token",
    "API_URL": "https://api.hm.bb.com.br/contas/v1/extratos",
    "INPUT_FILE": "contas_input.xlsx",
    "OUTPUT_FILE": "extrato_consolidado.xlsx",
    "MOCK_MODE": True
}

# --- CONFIGURAÇÃO DE LOG ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("execucao.log"),
        logging.StreamHandler()
    ]
)

class BankingAutomator:
    def __init__(self):
        self.token = None
        self.logs_execucao = []

    def _gerar_input_teste(self):
        if not os.path.exists(CONFIG["INPUT_FILE"]):
            logging.info("Arquivo de input não encontrado. Gerando massa de teste...")
            df = pd.DataFrame({
                'Agencia': ['1234', '5678', '9012'],
                'Conta': ['11111-1', '22222-2', '33333-3']
            })
            df.to_excel(CONFIG["INPUT_FILE"], index=False)

    def autenticar(self):
        logging.info("Iniciando autenticação OAuth2...")

        if CONFIG["MOCK_MODE"]:
            self.token = "mock_token_123456"
            logging.info("Autenticação MOCK realizada com sucesso.")
            return True

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "scope": "extratos.leitura"
        }

        try:
            response = requests.post(
                CONFIG["AUTH_URL"],
                auth=HTTPBasicAuth(CONFIG["CLIENT_ID"], CONFIG["CLIENT_SECRET"]),
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            self.token = response.json().get('access_token')
            if not self.token:
                raise ValueError("Token não encontrado na resposta.")
            logging.info("Autenticação realizada com sucesso.")
            return True
        except Exception as e:
            logging.error(f"Falha na autenticação: {str(e)}")
            return False

    def consultar_extrato(self, agencia, conta):
        if CONFIG["MOCK_MODE"]:
            if conta == '33333-3':
                return None, "Erro 404: Conta não localizada na base do banco."
            return {
                "data": [
                    {"dataLancamento": "15/11/2023", "numeroDocumento": "1001", "valorLancamento": 150.00, "textoDescricaoHistorico": "PIX RECEBIDO"},
                    {"dataLancamento": "16/11/2023", "numeroDocumento": "1002", "valorLancamento": -50.00, "textoDescricaoHistorico": "PGTO BOLETO"},
                    {"dataLancamento": "17/11/2023", "numeroDocumento": "1003", "valorLancamento": -20.00, "textoDescricaoHistorico": "TAR BANCARIA"}
                ]
            }, None

        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Developer-Application-Key": CONFIG["APP_KEY"],
            "Content-Type": "application/json"
        }
        params = {"agencia": agencia, "conta": conta}

        try:
            response = requests.get(CONFIG["API_URL"], headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.HTTPError as e:
            return None, f"Erro HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return None, f"Erro genérico: {str(e)}"

    def processar(self):
        self._gerar_input_teste()

        try:
            df_contas = pd.read_excel(CONFIG["INPUT_FILE"], dtype=str)
            logging.info(f"Base de contas carregada. Total: {len(df_contas)} contas.")
        except Exception as e:
            logging.critical(f"Não foi possível ler o arquivo de entrada: {e}")
            return

        if not self.autenticar():
            return

        abas_excel = {}

        for _, row in df_contas.iterrows():
            agencia = row['Agencia']
            conta = row['Conta']
            chave_conta = f"{agencia}-{conta}"

            logging.info(f"Processando conta: {chave_conta}")
            dados_json, erro = self.consultar_extrato(agencia, conta)

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
                    lista_lancamentos = dados_json.get('data', [])
                    df_extrato = pd.DataFrame(lista_lancamentos)
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