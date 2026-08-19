# ============================================
# API PHARMADB - Dados completos de medicamentos
# ============================================
# Documentação: https://pharmadb.com.br
# Planos: Free (20 req/dia), Starter, Pro, Pro+, Enterprise
# ============================================

import requests
import json
from datetime import datetime, timedelta

# === CONFIGURAÇÃO ===
# Cadastre-se em https://pharmadb.com.br para obter uma chave
PHARMADB_API_KEY = ""  # <-- COLOQUE SUA CHAVE AQUI
PHARMADB_URL = "https://api.pharmadb.com.br/v1"

# === CACHE ===
_cache = {}
CACHE_TTL = timedelta(days=7)

# ============================================
# FUNÇÕES PRINCIPAIS
# ============================================

def buscar_medicamento_pharmadb(nome, limite=10):
    """
    Busca medicamentos na PharmaDB pelo nome
    Retorna lista com dados detalhados (sem preços)
    """
    if not PHARMADB_API_KEY:
        return {"erro": "Chave da PharmaDB não configurada"}
    
    cache_key = f"pharmadb_{nome.lower()}"
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return cached_data
    
    try:
        url = f"{PHARMADB_URL}/medicamentos"
        headers = {
            "Authorization": f"Bearer {PHARMADB_API_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "nome": nome,
            "limite": limite
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            _cache[cache_key] = (dados, datetime.now())
            return dados
        elif response.status_code == 429:
            return {"erro": "Limite de requisições excedido (20 req/dia no plano free)"}
        else:
            return {"erro": f"Erro PharmaDB: {response.status_code}"}
    except Exception as e:
        return {"erro": f"Erro ao buscar na PharmaDB: {str(e)}"}

def buscar_interacoes_pharmadb(medicamento):
    """
    Busca interações medicamentosas na PharmaDB
    """
    if not PHARMADB_API_KEY:
        return {"erro": "Chave da PharmaDB não configurada"}
    
    cache_key = f"pharmadb_interacoes_{medicamento.lower()}"
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return cached_data
    
    try:
        url = f"{PHARMADB_URL}/interacoes"
        headers = {
            "Authorization": f"Bearer {PHARMADB_API_KEY}",
            "Content-Type": "application/json"
        }
        params = {"medicamento": medicamento}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            _cache[cache_key] = (dados, datetime.now())
            return dados
        else:
            return {"erro": f"Erro PharmaDB: {response.status_code}"}
    except Exception as e:
        return {"erro": f"Erro ao buscar interações: {str(e)}"}

def buscar_detalhes_medicamento_pharmadb(medicamento):
    """
    Busca detalhes completos de um medicamento (princípio ativo, fabricante, registro)
    """
    if not PHARMADB_API_KEY:
        return {"erro": "Chave da PharmaDB não configurada"}
    
    cache_key = f"pharmadb_detalhes_{medicamento.lower()}"
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return cached_data
    
    try:
        url = f"{PHARMADB_URL}/medicamentos/{medicamento}"
        headers = {
            "Authorization": f"Bearer {PHARMADB_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            _cache[cache_key] = (dados, datetime.now())
            return dados
        else:
            return {"erro": f"Erro PharmaDB: {response.status_code}"}
    except Exception as e:
        return {"erro": f"Erro ao buscar detalhes: {str(e)}"}