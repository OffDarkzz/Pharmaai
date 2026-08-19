import requests
from datetime import datetime, timedelta

# ============================================
# CONFIGURAÇÃO
# ============================================

ANVISA_API_URL = "https://api-medicamentos-anvisa.vercel.app"
_cache = {}
CACHE_TTL = timedelta(hours=6)

# ============================================
# FUNÇÃO DE BUSCA COM CACHE
# ============================================

def buscar_medicamento_anvisa_api(nome, usar_cache=True):
    """Busca medicamentos na API da ANVISA pelo nome."""
    nome = nome.strip()
    if not nome:
        return None

    cache_key = nome.lower()
    if usar_cache and cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return cached_data

    try:
        url = f"{ANVISA_API_URL}/{nome}"
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            dados = response.json()
            if dados:
                resultados = processar_dados_anvisa(dados)
                if resultados:
                    if usar_cache:
                        _cache[cache_key] = (resultados, datetime.now())
                    return resultados
        return None
    except Exception as e:
        print(f"Erro na API ANVISA: {e}")
        return None

def processar_dados_anvisa(dados):
    """Normaliza os dados retornados pela API da ANVISA."""
    resultados = []
    if isinstance(dados, list):
        lista = dados
    else:
        lista = [dados]

    for item in lista:
        medicamento = {
            "nome": item.get('NOME_PRODUTO', item.get('nome', item.get('NOME', 'N/A'))),
            "principio_ativo": item.get('PRINCIPIO_ATIVO', item.get('principio_ativo', item.get('SUBSTANCIA', 'N/A'))),
            "empresa": item.get('EMPRESA_DETENTORA_REGISTRO', item.get('empresa', item.get('FABRICANTE', 'N/A'))),
            "registro": item.get('NUMERO_REGISTRO', item.get('registro', item.get('REGISTRO', 'N/A'))),
            "tipo": item.get('TIPO_PRODUTO', item.get('tipo', item.get('CATEGORIA', 'N/A'))),
            "classe_terapeutica": item.get('CLASSE_TERAPEUTICA', item.get('classe_terapeutica', 'N/A')),
            "categoria_regulatoria": item.get('CATEGORIA_REGULATORIA', item.get('categoria_regulatoria', 'N/A')),
            "situacao": item.get('SITUACAO_REGISTRO', item.get('situacao', item.get('STATUS', 'Ativo'))),
            "fonte": "ANVISA"
        }
        medicamento = {k: v for k, v in medicamento.items() if v not in (None, '', 'N/A')}
        resultados.append(medicamento)
    
    return resultados

def limpar_cache():
    """Limpa o cache da API."""
    global _cache
    _cache = {}