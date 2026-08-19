import requests
import json
import time
from config import GSRS_URL, OPENFDA_URL, HC_URL, ANVISA_URL, OPENFDA_API_KEY

# ============================================
# 1. GSRS (FDA/NIH) - Busca por Princípio Ativo
# ============================================

def buscar_gsrs(termo):
    """
    Busca substâncias no GSRS pelo nome ou UNII.
    Retorna lista com UNII, nome, fórmula, etc.
    """
    url = f"{GSRS_URL}/search?q={termo}&size=10"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            dados = response.json()
            resultados = []
            for item in dados.get('content', []):
                substance = item.get('substance', {})
                unii = substance.get('unii', 'N/A')
                nome = substance.get('name', 'N/A')
                formula = substance.get('molecularFormula', 'N/A')
                resultados.append({
                    'unii': unii,
                    'nome': nome,
                    'formula': formula,
                    'fonte': 'GSRS'
                })
            return resultados
        else:
            return {'erro': f'GSRS erro: {response.status_code}'}
    except Exception as e:
        return {'erro': f'GSRS exceção: {str(e)}'}

# ============================================
# 2. openFDA (EUA) - Busca por Medicamento
# ============================================

def buscar_openFDA(termo, limite=5):
    """
    Busca medicamentos na openFDA por nome ou princípio ativo.
    Retorna dados do produto: nome, princípio ativo, fabricante, etc.
    """
    url = f"{OPENFDA_URL}/label.json"
    params = {
        'search': f'openfda.brand_name:{termo} OR openfda.substance_name:{termo}',
        'limit': limite
    }
    if OPENFDA_API_KEY:
        params['api_key'] = OPENFDA_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            dados = response.json()
            resultados = []
            for item in dados.get('results', []):
                openfda = item.get('openfda', {})
                resultados.append({
                    'nome': openfda.get('brand_name', ['N/A'])[0],
                    'principio_ativo': openfda.get('substance_name', ['N/A'])[0],
                    'fabricante': openfda.get('manufacturer_name', ['N/A'])[0],
                    'unii': openfda.get('unii', ['N/A'])[0],
                    'registro_fda': openfda.get('product_ndc', ['N/A'])[0],
                    'indicacao': item.get('indications_and_usage', ['N/A'])[0][:500],
                    'contraindicacao': item.get('contraindications', ['N/A'])[0][:500],
                    'fonte': 'FDA'
                })
            return resultados
        else:
            return {'erro': f'openFDA erro: {response.status_code}'}
    except Exception as e:
        return {'erro': f'openFDA exceção: {str(e)}'}

# ============================================
# 3. Health Canada - Busca por Medicamento
# ============================================

def buscar_health_canada(termo, limite=5):
    """
    Busca medicamentos no banco de dados do Health Canada.
    Retorna DIN, nome, fabricante, etc.
    """
    url = f"{HC_URL}/drug-products"
    params = {
        'search': termo,
        'limit': limite
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            dados = response.json()
            resultados = []
            for item in dados.get('data', []):
                resultados.append({
                    'nome': item.get('brandName', 'N/A'),
                    'principio_ativo': item.get('medicinalIngredient', 'N/A'),
                    'fabricante': item.get('manufacturer', 'N/A'),
                    'din': item.get('drugIdentificationNumber', 'N/A'),
                    'registro_hc': item.get('drugIdentificationNumber', 'N/A'),
                    'fonte': 'Health Canada'
                })
            return resultados
        else:
            return {'erro': f'Health Canada erro: {response.status_code}'}
    except Exception as e:
        return {'erro': f'Health Canada exceção: {str(e)}'}

# ============================================
# 4. ANVISA (Brasil) - Já temos, mantemos compatibilidade
# ============================================

def buscar_anvisa(nome):
    """Busca medicamentos na ANVISA (adaptador para manter compatibilidade)"""
    try:
        url = f"{ANVISA_URL}/{nome}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            if isinstance(dados, list):
                return dados
            else:
                return [dados]
        else:
            return {'erro': f'ANVISA erro: {response.status_code}'}
    except Exception as e:
        return {'erro': f'ANVISA exceção: {str(e)}'}

# ============================================
# 5. FUNÇÃO ORQUESTRADORA (busca em todas as fontes)
# ============================================

def buscar_medicamento_global(termo):
    """
    Busca um medicamento em todas as fontes disponíveis
    e consolida os resultados.
    """
    resultados = {
        'anvisa': [],
        'fda': [],
        'health_canada': [],
        'gsrs': []
    }
    
    # ANVISA
    anvisa = buscar_anvisa(termo)
    if not isinstance(anvisa, dict) or not anvisa.get('erro'):
        resultados['anvisa'] = anvisa if isinstance(anvisa, list) else [anvisa]
    
    # openFDA
    fda = buscar_openFDA(termo)
    if not isinstance(fda, dict) or not fda.get('erro'):
        resultados['fda'] = fda if isinstance(fda, list) else [fda]
    
    # Health Canada
    hc = buscar_health_canada(termo)
    if not isinstance(hc, dict) or not hc.get('erro'):
        resultados['health_canada'] = hc if isinstance(hc, list) else [hc]
    
    # GSRS
    gsrs = buscar_gsrs(termo)
    if not isinstance(gsrs, dict) or not gsrs.get('erro'):
        resultados['gsrs'] = gsrs if isinstance(gsrs, list) else [gsrs]
    
    # Consolidar em uma lista única (deduplicar por nome/UNII)
    consolidados = []
    vistos = set()
    
    # Processar ANVISA
    for item in resultados['anvisa']:
        chave = item.get('NOME_PRODUTO', item.get('nome', termo))
        if chave not in vistos:
            vistos.add(chave)
            consolidados.append({
                'nome': item.get('NOME_PRODUTO', item.get('nome', 'N/A')),
                'principio_ativo': item.get('PRINCIPIO_ATIVO', item.get('principio_ativo', 'N/A')),
                'laboratorio': item.get('EMPRESA_DETENTORA_REGISTRO', item.get('empresa', 'N/A')),
                'registro': item.get('NUMERO_REGISTRO', item.get('registro', 'N/A')),
                'tipo': item.get('TIPO_PRODUTO', item.get('tipo', 'N/A')),
                'fonte': 'ANVISA'
            })
    
    # Processar FDA
    for item in resultados['fda']:
        chave = item.get('nome', termo)
        if chave not in vistos:
            vistos.add(chave)
            consolidados.append({
                'nome': item.get('nome', 'N/A'),
                'principio_ativo': item.get('principio_ativo', 'N/A'),
                'laboratorio': item.get('fabricante', 'N/A'),
                'registro': item.get('registro_fda', 'N/A'),
                'tipo': 'Referência' if item.get('fonte') == 'FDA' else 'N/A',
                'fonte': 'FDA'
            })
    
    # Processar Health Canada
    for item in resultados['health_canada']:
        chave = item.get('nome', termo)
        if chave not in vistos:
            vistos.add(chave)
            consolidados.append({
                'nome': item.get('nome', 'N/A'),
                'principio_ativo': item.get('principio_ativo', 'N/A'),
                'laboratorio': item.get('fabricante', 'N/A'),
                'registro': item.get('din', 'N/A'),
                'tipo': 'N/A',
                'fonte': 'Health Canada'
            })
    
    # Processar GSRS (substâncias, não medicamentos)
    for item in resultados['gsrs']:
        chave = item.get('unii', termo)
        if chave not in vistos:
            vistos.add(chave)
            consolidados.append({
                'nome': item.get('nome', 'N/A'),
                'principio_ativo': item.get('nome', 'N/A'),
                'laboratorio': 'N/A',
                'registro': item.get('unii', 'N/A'),
                'tipo': 'Substância',
                'fonte': 'GSRS'
            })
    
    return consolidados