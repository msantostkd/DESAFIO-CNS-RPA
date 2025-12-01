#!/usr/bin/env python3
"""
main.py — BankingAutomator (versão final para entrega, com credenciais embutidas para avaliação)
- Observação: credenciais hardcoded apenas para avaliação em ambiente homolog.
"""

import os
import logging
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# --- CONFIGURAÇÕES DO PROJETO ---
CONFIG = {
    "APP_KEY": "2dc673fdaa5e4db68f1019d2d9027c01",
    "AUTH_URL": "https://oauth.hm.bb.com.br/oauth/token",
    "API_URL": "https://api.hm.bb.com.br/extratos/v1/conta-corrente/agencia/{agencia}/conta/{conta}",
    "INPUT_FILE": "contas_input.xlsx",
    "OUTPUT_FILE": "extrato_consolidado.xlsx",
    # page_size: entre 50 e 200 conforme spec; 100 é um bom padrão
    "PAGE_SIZE": 200,
    # Período padrão (DDMMAAAA). Ajuste conforme necessidade ou parametrizar por entrada.
    "DEFAULT_DATA_INICIO": "0",
    "DEFAULT_DATA_FIM": "0",
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

logger = logging.getLogger(__name__)


class BankingAutomator:
    def __init__(self):
        self.token = None
        self.logs_execucao = []

    def _gerar_input_teste(self):
        """ Gera arquivo de input se não existir (apenas para facilitar testes locais). """
        if not os.path.exists(CONFIG["INPUT_FILE"]):
            logger.info("Arquivo de input não encontrado. Gerando massa de teste...")
            df = pd.DataFrame({
                'MCITest': ['26968930', '178961031', '704950857'],
                'Agencia': ['551', '1505', '452'],
                'Conta': ['5087', '1348', '123873']
            })
            df.to_excel(CONFIG["INPUT_FILE"], index=False)

    def autenticar(self):
        """
        Autenticação OAuth2:
        - Para avaliação: credenciais estão hardcoded abaixo (somente homolog).
        - Faz POST para /oauth/token usando HTTPBasicAuth (sem scope primeiro).
        """
        logger.info("Iniciando autenticação OAuth2 — usando credenciais embutidas para avaliação...")

        # >>> Credenciais fixas para avaliação (somente para ambiente de homologação)
        client_id = "eyJpZCI6ImU0NTYiLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6MTYzMDUwLCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6MX0"
        client_secret = "eyJpZCI6IjkzY2Q2NGQtNWE5Yy00ZTA5LTk4ZmEtYmI0ZDcyMDIyMyIsImNvZGlnb1B1YmxpY2Fkb3IiOjAsImNvZGlnb1NvZnR3YXJlIjoxNjMwNTAsInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoxLCJzZXF1ZW5jaWFsQ3JlZGVuY2lhbCI6MiwiYW1iaWVudGUiOiJob21vbG9nYWNhbyIsImlhdCI6MTc2NDA3NjYwMzQ5OX0"

        # sanitização simples (não faz mal, string já correta)
        client_id = client_id.strip()
        client_secret = client_secret.strip()

        url = CONFIG["AUTH_URL"]
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # 1) tentar sem scope (corresponde ao teste que funcionou)
        try:
            payload_simple = {"grant_type": "client_credentials"}
            logger.info("[AUTH] Tentativa de token (sem scope)")
            r = requests.post(url, headers=headers, data=payload_simple,
                              auth=HTTPBasicAuth(client_id, client_secret), timeout=15)
            logger.info(f"[AUTH] status={r.status_code} resp_preview={r.text[:300]}")
            if r.status_code == 200 and r.json().get("access_token"):
                self.token = r.json().get("access_token")
                logger.info("Autenticação sucedida (sem scope).")
                return True
        except Exception as e:
            logger.warning(f"Exceção durante autenticação (sem scope): {e}")

        # 2) fallback: tentar com scope caso precise
        try:
            payload_scope = {"grant_type": "client_credentials", "scope": "extratos.leitura"}
            logger.info("[AUTH] Tentativa de token (com scope)")
            r2 = requests.post(url, headers=headers, data=payload_scope,
                               auth=HTTPBasicAuth(client_id, client_secret), timeout=15)
            logger.info(f"[AUTH] status={r2.status_code} resp_preview={r2.text[:300]}")
            if r2.status_code == 200 and r2.json().get("access_token"):
                self.token = r2.json().get("access_token")
                logger.info("Autenticação sucedida (com scope).")
                return True
        except Exception as e:
            logger.warning(f"Exceção durante autenticação (com scope): {e}")

        logger.error("Falha na autenticação. Verifique credenciais e ambiente (homolog/prod).")
        return False

    @staticmethod
    def _parse_ddmmaaaa(value):
        """Converte int/str DDMMAAAA para string 'DD/MM/YYYY'. Retorna None se inválido."""
        try:
            s = str(value)
            if len(s) == 8:
                dd, mm, yyyy = s[:2], s[2:4], s[4:]
                return f"{dd}/{mm}/{yyyy}"
            return None
        except Exception:
            return None

    def consultar_extrato(self, agencia, conta, mcitest,
                          data_inicio=None, data_fim=None, page_size=None):
        """
        Consulta o extrato conforme spec:
        - GET /conta-corrente/agencia/{agencia}/conta/{conta}
        - Parâmetros na query: gw-dev-app-key, dataInicioSolicitacao (DDMMAAAA string), dataFimSolicitacao (DDMMAAAA string),
          numeroPaginaSolicitacao (int), quantidadeRegistroPaginaSolicitacao (int)
        - Envia também o header x-br-com-bb-ipa-mciteste por compatibilidade.

        Retorna ({"listaLancamento": [...]}, None) ou (None, erro_str)
        """
        extrato_url = CONFIG["API_URL"].format(agencia=agencia, conta=conta)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "X-Developer-Application-Key": CONFIG["APP_KEY"],
            "x-br-com-bb-ipa-mciteste": str(mcitest)
        }

        data_inicio = data_inicio or CONFIG["DEFAULT_DATA_INICIO"]
        data_fim = data_fim or CONFIG["DEFAULT_DATA_FIM"]
        page_size = page_size or CONFIG["PAGE_SIZE"]

        # paginação
        page = 1
        all_lancamentos = []
        total_pages = 1

        while page <= total_pages:
            params = {
                "gw-dev-app-key": CONFIG["APP_KEY"],
                "dataInicioSolicitacao": data_inicio,
                "dataFimSolicitacao": data_fim,
                "numeroPaginaSolicitacao": page,
                "quantidadeRegistroPaginaSolicitacao": page_size
            }

            try:
                full_request_url = requests.Request('GET', extrato_url, params=params).prepare().url
                logger.info(f"URL de Requisição (GET) (Conta {agencia}-{conta}) page={page}: {full_request_url}")
            except Exception as e:
                logger.warning(f"Não foi possível gerar a URL de debug: {e}")

            try:
                r = requests.get(extrato_url, headers=headers, params=params, timeout=20)
                logger.info(f"GET page={page} -> status={r.status_code}. resp_preview={r.text[:400]}")
                if r.status_code != 200:
                    return None, f"Erro HTTP {r.status_code}: {r.text}"

                j = r.json()
                lista = j.get("listaLancamento", [])
                all_lancamentos.extend(lista)

                # Atualiza total_pages a partir da resposta
                total_pages = j.get("quantidadeTotalPagina") or total_pages
                if (not total_pages) and j.get("quantidadeTotalRegistro"):
                    total_reg = j.get("quantidadeTotalRegistro")
                    total_pages = (total_reg + page_size - 1) // page_size

                page += 1

            except Exception as e:
                return None, f"Erro genérico na consulta do extrato (page {page}): {e}"

        # Formatação das datas e adição de campo formatado
        for item in all_lancamentos:
            if "dataLancamento" in item:
                parsed = self._parse_ddmmaaaa(item["dataLancamento"])
                item["dataLancamento_format"] = parsed or item.get("dataLancamento")

        return {"listaLancamento": all_lancamentos}, None

    def processar(self):
        logger.info("Iniciando processo de processamento de contas...")
        self._gerar_input_teste()

        try:
            df_contas = pd.read_excel(CONFIG["INPUT_FILE"], dtype=str)
            logger.info(f"Base de contas carregada. Total: {len(df_contas)} contas.")
        except Exception as e:
            logger.critical(f"Não foi possível ler o arquivo de entrada: {e}")
            return

        if not self.autenticar():
            logger.error("Autenticação falhou — abortando processo.")
            return

        abas_excel = {}

        for _, row in df_contas.iterrows():
            mcitest = row.get('MCITest')
            agencia = row['Agencia']
            conta = row['Conta']
            chave_conta = f"{agencia}-{conta}"

            logger.info(f"Processando conta: {chave_conta} (MCITest: {mcitest})")

            dados_json, erro = self.consultar_extrato(agencia, conta, mcitest)

            if erro:
                logger.error(f"Falha na conta {chave_conta}: {erro}")
                self.logs_execucao.append({
                    "Agencia": agencia,
                    "Conta": conta,
                    "Status": "FALHA",
                    "Detalhe": erro
                })
            else:
                try:
                    lista_lancamentos = dados_json.get('listaLancamento', [])
                    df_extrato = pd.DataFrame(lista_lancamentos)

                    logger.info(f"Conta {chave_conta}: Encontrados {len(df_extrato)} lançamentos.")

                    cols_desejadas = ['dataLancamento_format', 'numeroDocumento', 'valorLancamento', 'textoDescricaoHistorico']
                    df_extrato = df_extrato[cols_desejadas] if not df_extrato.empty else pd.DataFrame(columns=cols_desejadas)

                    # renomear coluna para ficar amigável no Excel
                    df_extrato = df_extrato.rename(columns={
                        'dataLancamento_format': 'dataLancamento',
                    })

                    abas_excel[chave_conta] = df_extrato
                    self.logs_execucao.append({
                        "Agencia": agencia,
                        "Conta": conta,
                        "Status": "OK",
                        "Detalhe": "Processado com sucesso"
                    })
                    logger.info(f"Conta {chave_conta} processada com sucesso.")
                except Exception as e:
                    logger.error(f"Erro ao processar JSON da conta {chave_conta}: {e}")
                    self.logs_execucao.append({
                        "Agencia": agencia,
                        "Conta": conta,
                        "Status": "FALHA",
                        "Detalhe": "Erro de Parse JSON"
                    })

        self.gerar_planilha_consolidada(abas_excel)

    def gerar_planilha_consolidada(self, abas_dados):
        logger.info("Gerando planilha consolidada...")

        try:
            with pd.ExcelWriter(CONFIG["OUTPUT_FILE"], engine='openpyxl') as writer:
                df_log = pd.DataFrame(self.logs_execucao)
                df_log.to_excel(writer, sheet_name='Log_Execucao', index=False)
                for nome_aba, df in abas_dados.items():
                    nome_safe = nome_aba[:31]
                    df.to_excel(writer, sheet_name=nome_safe, index=False)
            logger.info(f"Arquivo '{CONFIG['OUTPUT_FILE']}' gerado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao salvar Excel: {e}")


if __name__ == "__main__":
    bot = BankingAutomator()
    bot.processar()
    logger.info("Processo finalizado.")
