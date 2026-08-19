import requests
import json
import csv
import os
from datetime import datetime, timedelta
from api_anvisa import buscar_medicamento_anvisa_api

# ============================================
# CONFIGURAÇÃO DA API ANVISA
# ============================================

ANVISA_API_URL = "https://api-medicamentos-anvisa.vercel.app"
_cache = {}
CACHE_TTL = timedelta(hours=6)

# ============================================
# CARREGAR CIDs DO ARQUIVO CSV (ou fallback)
# ============================================

_CIDS = []
def carregar_cids():
    """Carrega a lista de CIDs do arquivo cids.csv."""
    global _CIDS
    cids = []
    try:
        with open('cids.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo = row.get('codigo') or row.get('cid')
                descricao = row.get('descricao') or row.get('nome')
                if codigo and descricao:
                    cids.append({'codigo': codigo.strip(), 'descricao': descricao.strip()})
        if cids:
            print(f"📋 CID-10 carregados do CSV: {len(cids)} registros")
            _CIDS = cids
            return cids
    except FileNotFoundError:
        print("⚠️ Arquivo cids.csv não encontrado. Usando fallback mínimo.")
    except Exception as e:
        print(f"⚠️ Erro ao carregar cids.csv: {e}")
    
    # Fallback mínimo
    fallback = [
        {"codigo": "R69", "descricao": "Sintomas inespecíficos"},
        {"codigo": "R50", "descricao": "Febre"},
        {"codigo": "R05", "descricao": "Tosse"},
        {"codigo": "R10", "descricao": "Dor abdominal"},
        {"codigo": "R11", "descricao": "Náusea e vômito"},
        {"codigo": "R53", "descricao": "Fadiga"},
        {"codigo": "G43", "descricao": "Enxaqueca"},
        {"codigo": "J02", "descricao": "Faringite aguda"},
        {"codigo": "J03", "descricao": "Amigdalite aguda"},
        {"codigo": "J06", "descricao": "Infecções agudas das vias respiratórias"},
        {"codigo": "J20", "descricao": "Bronquite aguda"},
        {"codigo": "J30", "descricao": "Rinite alérgica"},
        {"codigo": "J32", "descricao": "Sinusite crônica"},
        {"codigo": "J45", "descricao": "Asma"},
        {"codigo": "K21", "descricao": "Doença do refluxo gastroesofágico"},
        {"codigo": "K29", "descricao": "Gastrite"},
        {"codigo": "K59", "descricao": "Outros distúrbios intestinais"},
        {"codigo": "L29", "descricao": "Prurido"},
        {"codigo": "L50", "descricao": "Urticária"},
        {"codigo": "M05", "descricao": "Artrite reumatoide"},
        {"codigo": "M10", "descricao": "Gota"},
        {"codigo": "N39", "descricao": "Outros distúrbios do trato urinário"},
        {"codigo": "E11", "descricao": "Diabetes mellitus tipo 2"},
        {"codigo": "E78", "descricao": "Distúrbios do metabolismo de lipoproteínas"},
        {"codigo": "I10", "descricao": "Hipertensão essencial"},
        {"codigo": "I50", "descricao": "Insuficiência cardíaca"},
        {"codigo": "F32", "descricao": "Episódio depressivo"},
        {"codigo": "F41", "descricao": "Outros transtornos ansiosos"},
        {"codigo": "G47", "descricao": "Distúrbios do sono"},
        {"codigo": "M54", "descricao": "Dorsalgia"},
        {"codigo": "M17", "descricao": "Osteoartrite do joelho"},
        {"codigo": "R42", "descricao": "Tontura"},
        {"codigo": "R63", "descricao": "Sede"},
        {"codigo": "R35", "descricao": "Poliúria"},
        {"codigo": "H53", "descricao": "Distúrbios visuais"},
        {"codigo": "T78", "descricao": "Reação alérgica"}
    ]
    _CIDS = fallback
    return fallback

carregar_cids()

# ============================================
# MAPEAMENTO DE DOENÇAS PARA CID-10 (com nomes e gravidade)
# ============================================

MAPEAMENTO_DOENCAS_CID = {
    "diabetes": {"cid": "E11", "nome": "Diabetes Mellitus Tipo 2", "gravidade": "Grave"},
    "hipertensao": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "pressao alta": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "dislipidemia": {"cid": "E78", "nome": "Dislipidemia", "gravidade": "Moderada"},
    "obesidade": {"cid": "E66", "nome": "Obesidade", "gravidade": "Grave"},
    "asma": {"cid": "J45", "nome": "Asma", "gravidade": "Moderada"},
    "osteoartrite": {"cid": "M17", "nome": "Osteoartrite do Joelho", "gravidade": "Moderada"},
    "artrite reumatoide": {"cid": "M05", "nome": "Artrite Reumatoide", "gravidade": "Grave"},
    "gota": {"cid": "M10", "nome": "Gota", "gravidade": "Moderada"},
    "depressao": {"cid": "F32", "nome": "Episódio Depressivo", "gravidade": "Grave"},
    "ansiedade": {"cid": "F41", "nome": "Transtorno de Ansiedade", "gravidade": "Moderada"},
    "insuficiencia cardiaca": {"cid": "I50", "nome": "Insuficiência Cardíaca", "gravidade": "Grave"},
    "doenca renal": {"cid": "N18", "nome": "Doença Renal Crônica", "gravidade": "Grave"},
    "hepatopatia": {"cid": "K70", "nome": "Doença Hepática Alcoólica", "gravidade": "Grave"},
    "insonia": {"cid": "G47", "nome": "Insônia", "gravidade": "Moderada"},
    "insônia": {"cid": "G47", "nome": "Insônia", "gravidade": "Moderada"}
}

# ============================================
# MAPEAMENTO DE SINTOMAS PARA CID-10 (com nomes e gravidade)
# ============================================

MAPEAMENTO_SINTOMAS_CID = {
    "dor de cabeca": {"cid": "G43", "nome": "Enxaqueca", "gravidade": "Moderada"},
    "dor de cabeça": {"cid": "G43", "nome": "Enxaqueca", "gravidade": "Moderada"},
    "cefaleia": {"cid": "G43", "nome": "Enxaqueca", "gravidade": "Moderada"},
    "enxaqueca": {"cid": "G43", "nome": "Enxaqueca", "gravidade": "Moderada"},
    "tontura": {"cid": "R42", "nome": "Tontura", "gravidade": "Leve"},
    "vertigem": {"cid": "R42", "nome": "Tontura", "gravidade": "Leve"},
    "febre": {"cid": "R50", "nome": "Febre", "gravidade": "Moderada"},
    "tosse": {"cid": "R05", "nome": "Tosse", "gravidade": "Leve"},
    "falta de ar": {"cid": "R06", "nome": "Dificuldade Respiratória", "gravidade": "Grave"},
    "asma": {"cid": "J45", "nome": "Asma", "gravidade": "Moderada"},
    "bronquite": {"cid": "J20", "nome": "Bronquite Aguda", "gravidade": "Moderada"},
    "diarreia": {"cid": "K59", "nome": "Diarreia", "gravidade": "Moderada"},
    "nausea": {"cid": "R11", "nome": "Náusea e Vômito", "gravidade": "Leve"},
    "vomito": {"cid": "R11", "nome": "Náusea e Vômito", "gravidade": "Leve"},
    "azia": {"cid": "K21", "nome": "Doença do Refluxo Gastroesofágico", "gravidade": "Moderada"},
    "refluxo": {"cid": "K21", "nome": "Doença do Refluxo Gastroesofágico", "gravidade": "Moderada"},
    "gastrite": {"cid": "K29", "nome": "Gastrite", "gravidade": "Moderada"},
    "dor abdominal": {"cid": "R10", "nome": "Dor Abdominal", "gravidade": "Moderada"},
    "dor no peito": {"cid": "R07", "nome": "Dor no Peito", "gravidade": "Grave"},
    "palpitacao": {"cid": "R00", "nome": "Palpitação", "gravidade": "Moderada"},
    "taquicardia": {"cid": "R00", "nome": "Taquicardia", "gravidade": "Grave"},
    "pressao alta": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "pressão alta": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "pressao": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "pressão": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "hipertensao": {"cid": "I10", "nome": "Hipertensão Arterial", "gravidade": "Moderada"},
    "sede": {"cid": "R63", "nome": "Sede Excessiva", "gravidade": "Leve"},
    "urinar varias vezes": {"cid": "R35", "nome": "Poliúria (Urina Frequente)", "gravidade": "Moderada"},
    "urina frequente": {"cid": "R35", "nome": "Poliúria (Urina Frequente)", "gravidade": "Moderada"},
    "fadiga": {"cid": "R53", "nome": "Fadiga", "gravidade": "Moderada"},
    "visao embacada": {"cid": "H53", "nome": "Distúrbio Visual", "gravidade": "Moderada"},
    "visão embaçada": {"cid": "H53", "nome": "Distúrbio Visual", "gravidade": "Moderada"},
    "aumento do apetite": {"cid": "R63", "nome": "Aumento do Apetite", "gravidade": "Leve"},
    "alergia": {"cid": "T78", "nome": "Reação Alérgica", "gravidade": "Moderada"},
    "coceira": {"cid": "L29", "nome": "Prurido (Coceira)", "gravidade": "Leve"},
    "urticaria": {"cid": "L50", "nome": "Urticária", "gravidade": "Moderada"},
    "coriza": {"cid": "J30", "nome": "Rinite Alérgica", "gravidade": "Leve"},
    "infeccao urinaria": {"cid": "N39", "nome": "Infecção do Trato Urinário", "gravidade": "Moderada"},
    "faringite": {"cid": "J02", "nome": "Faringite Aguda", "gravidade": "Moderada"},
    "sinusite": {"cid": "J32", "nome": "Sinusite Crônica", "gravidade": "Moderada"},
    "amigdalite": {"cid": "J03", "nome": "Amigdalite Aguda", "gravidade": "Moderada"},
    "otite": {"cid": "H66", "nome": "Otite Média", "gravidade": "Moderada"},
    "ansiedade": {"cid": "F41", "nome": "Transtorno de Ansiedade", "gravidade": "Moderada"},
    "insonia": {"cid": "G47", "nome": "Insônia", "gravidade": "Moderada"},
    "insônia": {"cid": "G47", "nome": "Insônia", "gravidade": "Moderada"},
    "depressao": {"cid": "F32", "nome": "Episódio Depressivo", "gravidade": "Grave"},
    "artrite": {"cid": "M05", "nome": "Artrite Reumatoide", "gravidade": "Grave"},
    "gota": {"cid": "M10", "nome": "Gota", "gravidade": "Moderada"},
    "colesterol": {"cid": "E78", "nome": "Dislipidemia", "gravidade": "Moderada"},
    "obesidade": {"cid": "E66", "nome": "Obesidade", "gravidade": "Grave"},
    "dor nas costas": {"cid": "M54", "nome": "Dorsalgia (Dor nas Costas)", "gravidade": "Moderada"},
    "dor lombar": {"cid": "M54", "nome": "Dorsalgia (Dor nas Costas)", "gravidade": "Moderada"},
    "dorsalgia": {"cid": "M54", "nome": "Dorsalgia (Dor nas Costas)", "gravidade": "Moderada"},
    "dor nos joelhos": {"cid": "M17", "nome": "Osteoartrite do Joelho", "gravidade": "Moderada"},
    "osteoartrite": {"cid": "M17", "nome": "Osteoartrite do Joelho", "gravidade": "Moderada"},
    "diabetes": {"cid": "E11", "nome": "Diabetes Mellitus Tipo 2", "gravidade": "Grave"},
    "dislipidemia": {"cid": "E78", "nome": "Dislipidemia", "gravidade": "Moderada"}
}

# ============================================
# MAPEAMENTO DE SINTOMAS PARA MEDICAMENTOS
# ============================================

MAPEAMENTO_SINTOMAS_MEDICAMENTOS = {
    "sede": ["Metformina", "Glibenclamida", "Insulina NPH"],
    "urinar varias vezes": ["Metformina", "Glibenclamida"],
    "urina frequente": ["Metformina", "Glibenclamida"],
    "fadiga": ["Metformina", "Glibenclamida", "Complexo B"],
    "visao embacada": ["Metformina", "Glibenclamida"],
    "visão embaçada": ["Metformina", "Glibenclamida"],
    "aumento do apetite": ["Metformina", "Glibenclamida"],
    "dor de cabeca": ["Paracetamol", "Ibuprofeno", "Dipirona"],
    "dor de cabeça": ["Paracetamol", "Ibuprofeno", "Dipirona"],
    "cefaleia": ["Paracetamol", "Ibuprofeno", "Dipirona"],
    "dor nas costas": ["Paracetamol", "Dipirona", "Ibuprofeno"],
    "dor lombar": ["Paracetamol", "Dipirona", "Ibuprofeno"],
    "dorsalgia": ["Paracetamol", "Dipirona", "Ibuprofeno"],
    "dor nos joelhos": ["Paracetamol", "Dipirona", "Ibuprofeno"],
    "enxaqueca": ["Dipirona", "Ibuprofeno", "Sumatriptano"],
    "dor no corpo": ["Dipirona", "Ibuprofeno", "Paracetamol"],
    "dor atras dos olhos": ["Dipirona", "Paracetamol"],
    "dor de garganta": ["Paracetamol", "Ibuprofeno", "Amoxicilina"],
    "dor muscular": ["Ibuprofeno", "Diclofenaco", "Paracetamol"],
    "dor articular": ["Ibuprofeno", "Diclofenaco", "Naproxeno"],
    "dor abdominal": ["Paracetamol", "Dipirona", "Hioscina"],
    "dor de dente": ["Dipirona", "Ibuprofeno", "Paracetamol"],
    "febre": ["Paracetamol", "Dipirona", "Ibuprofeno"],
    "inflamacao": ["Ibuprofeno", "Diclofenaco", "Naproxeno"],
    "dificuldade respiratoria": ["Salbutamol", "Budesonida"],
    "falta de ar": ["Salbutamol", "Budesonida"],
    "tosse": ["Bromexina", "Guaifenesina", "N-acetilcisteina"],
    "asma": ["Salbutamol", "Budesonida"],
    "bronquite": ["Amoxicilina", "Azitromicina", "Salbutamol"],
    "frequencia cardiaca alta": ["Propranolol", "Metoprolol"],
    "taquicardia": ["Propranolol", "Metoprolol"],
    "palpitacao": ["Propranolol", "Metoprolol"],
    "pressao alta": ["Losartana", "Captopril", "Enalapril"],
    "hipertensao": ["Losartana", "Captopril", "Enalapril"],
    "azia": ["Omeprazol", "Pantoprazol", "Ranitidina"],
    "refluxo": ["Omeprazol", "Pantoprazol"],
    "gastrite": ["Omeprazol", "Pantoprazol"],
    "nausea": ["Ondansetrona", "Metoclopramida"],
    "vomito": ["Ondansetrona", "Metoclopramida"],
    "diarreia": ["Loperamida", "Metronidazol"],
    "constipacao": ["Lactulose", "Bisacodil"],
    "alergia": ["Cetirizina", "Loratadina"],
    "coceira": ["Cetirizina", "Loratadina"],
    "urticaria": ["Cetirizina", "Loratadina"],
    "coriza": ["Loratadina", "Cetirizina"],
    "infeccao": ["Amoxicilina", "Azitromicina", "Cefalexina"],
    "infeccao urinaria": ["Ciprofloxacino", "Nitrofurantoina"],
    "faringite": ["Amoxicilina", "Azitromicina", "Paracetamol"],
    "sinusite": ["Amoxicilina", "Azitromicina", "Paracetamol"],
    "amigdalite": ["Amoxicilina", "Azitromicina", "Paracetamol"],
    "otite": ["Amoxicilina", "Azitromicina", "Paracetamol"],
    "ansiedade": ["Diazepam", "Alprazolam"],
    "insonia": ["Zolpidem", "Diazepam", "Melatonina"],
    "insônia": ["Zolpidem", "Diazepam", "Melatonina"],
    "depressao": ["Fluoxetina", "Sertralina"],
    "artrite": ["Ibuprofeno", "Diclofenaco"],
    "gota": ["Alopurinol", "Colchicina"],
    "diabetes": ["Metformina", "Glibenclamida", "Insulina NPH"],
    "colesterol": ["Sinvastatina", "Atorvastatina", "Rosuvastatina"],
    "obesidade": ["Orlistate", "Sibutramina"],
    "gripe": ["Paracetamol", "Dipirona", "Oseltamivir"],
    "resfriado": ["Paracetamol", "Dipirona"]
}

# ============================================
# MAPEAMENTO DE DOENÇAS PARA MEDICAMENTOS
# ============================================

MAPEAMENTO_DOENCAS_MEDICAMENTOS = {
    "diabetes": ["Metformina", "Glibenclamida", "Insulina NPH"],
    "hipertensao": ["Losartana", "Captopril", "Enalapril", "Amlodipina"],
    "dislipidemia": ["Sinvastatina", "Atorvastatina", "Rosuvastatina"],
    "obesidade": ["Orlistate", "Sibutramina"],
    "asma": ["Salbutamol", "Budesonida"],
    "artrite": ["Ibuprofeno", "Diclofenaco"],
    "osteoartrite": ["Glucosamina", "Condroitina", "Ibuprofeno"],
    "gota": ["Alopurinol", "Colchicina"],
    "depressao": ["Fluoxetina", "Sertralina"],
    "ansiedade": ["Diazepam", "Alprazolam"],
    "insuficiencia cardiaca": ["Losartana", "Captopril", "Furosemida"],
    "doenca renal": ["Alopurinol"],
    "hepatopatia": ["Ursodiol"],
    "insonia": ["Zolpidem", "Diazepam", "Melatonina"],
    "insônia": ["Zolpidem", "Diazepam", "Melatonina"]
}

# ============================================
# BASE DE DADOS LOCAL (POSOLOGIA E SEGURANÇA)
# ============================================

BASE_MEDICAMENTOS = {
    "Paracetamol": {
        "principio_ativo": "Paracetamol",
        "posologia": {
            "adulto": "500mg a 1000mg a cada 4-6h, máximo 4g/dia",
            "idoso": "500mg a 750mg a cada 6h, máximo 3g/dia",
            "crianca": "10-15mg/kg a cada 4-6h"
        },
        "duracao": "Máximo 5 dias",
        "contraindicacao": "Insuficiência hepática grave, alergia ao paracetamol",
        "interacoes": ["Álcool", "Warfarina"],
        "tipo": "Analgésico/Antitérmico",
        "registro": "123456789",
        "alerta_idoso": False
    },
    "Ibuprofeno": {
        "principio_ativo": "Ibuprofeno",
        "posologia": {
            "adulto": "200-400mg a cada 6-8h, máximo 1.2g/dia",
            "idoso": "200mg a cada 8h, máximo 600mg/dia (evitar uso prolongado)",
            "crianca": "5-10mg/kg a cada 6-8h"
        },
        "duracao": "Máximo 3-5 dias",
        "contraindicacao": "Úlcera, insuficiência renal, alergia a AINEs",
        "interacoes": ["AAS", "Warfarina", "Losartana"],
        "tipo": "AINE",
        "registro": "987654321",
        "alerta_idoso": True
    },
    "Dipirona": {
        "principio_ativo": "Dipirona sódica",
        "posologia": {
            "adulto": "500mg a 1g a cada 6h, máximo 4g/dia",
            "idoso": "500mg a cada 8h, máximo 2g/dia",
            "crianca": "10-15mg/kg a cada 6h"
        },
        "duracao": "Máximo 3 dias",
        "contraindicacao": "Discrasias sanguíneas, alergia a dipirona",
        "interacoes": ["Clorpromazina", "Metotrexato"],
        "tipo": "Analgésico/Antitérmico",
        "registro": "456789123",
        "alerta_idoso": True
    },
    "Losartana": {
        "principio_ativo": "Losartana potássica",
        "posologia": {
            "adulto": "50mg 1x/dia, até 100mg/dia",
            "idoso": "50mg 1x/dia (monitorar função renal)",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Gravidez, insuficiência renal grave",
        "interacoes": ["Ibuprofeno", "AAS", "Lítio"],
        "tipo": "Anti-hipertensivo (BRA)",
        "registro": "789123456",
        "alerta_idoso": True
    },
    "Metformina": {
        "principio_ativo": "Metformina",
        "posologia": {
            "adulto": "500mg 2-3x/dia, máximo 2.55g/dia",
            "idoso": "500mg 2x/dia, avaliar função renal",
            "crianca": "A partir de 10 anos"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Insuficiência renal, acidose metabólica",
        "interacoes": ["Álcool", "Ibuprofeno"],
        "tipo": "Antidiabético (biguanida)",
        "registro": "321654987",
        "alerta_idoso": True
    },
    "Amoxicilina": {
        "principio_ativo": "Amoxicilina",
        "posologia": {
            "adulto": "500mg a cada 8h",
            "idoso": "Ajuste renal",
            "crianca": "20-40mg/kg/dia dividido em 3 doses"
        },
        "duracao": "7-10 dias",
        "contraindicacao": "Alergia a penicilinas",
        "interacoes": ["Metotrexato", "Warfarina"],
        "tipo": "Antibiótico (penicilina)",
        "registro": "654987321",
        "alerta_idoso": False
    },
    "Omeprazol": {
        "principio_ativo": "Omeprazol",
        "posologia": {
            "adulto": "20mg 1x/dia",
            "idoso": "20mg 1x/dia, avaliar interações",
            "crianca": "10mg 1x/dia"
        },
        "duracao": "4-8 semanas",
        "contraindicacao": "Alergia ao omeprazol",
        "interacoes": ["Clopidogrel", "Cetoconazol"],
        "tipo": "Inibidor de bomba de prótons",
        "registro": "147258369",
        "alerta_idoso": True
    },
    "Sinvastatina": {
        "principio_ativo": "Sinvastatina",
        "posologia": {
            "adulto": "10-40mg/dia",
            "idoso": "10-20mg/dia, avaliar interações",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Doença hepática ativa, gravidez",
        "interacoes": ["Ibuprofeno", "Amiodarona"],
        "tipo": "Hipolipemiante (estatina)",
        "registro": "258369147",
        "alerta_idoso": True
    },
    "Salbutamol": {
        "principio_ativo": "Salbutamol",
        "posologia": {
            "adulto": "100-200mcg spray 3-4x/dia",
            "idoso": "100mcg spray 3x/dia, usar com cautela",
            "crianca": "100mcg spray 3-4x/dia"
        },
        "duracao": "Conforme necessidade",
        "contraindicacao": "Alergia ao salbutamol",
        "interacoes": ["Propranolol", "Diuréticos"],
        "tipo": "Broncodilatador β2-agonista",
        "registro": "369147258",
        "alerta_idoso": True
    },
    "Propranolol": {
        "principio_ativo": "Propranolol",
        "posologia": {
            "adulto": "10-40mg 2-3x/dia",
            "idoso": "10-20mg 2x/dia, dose reduzida",
            "crianca": "0.5-1mg/kg/dia"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Asma, bradicardia, insuficiência cardíaca",
        "interacoes": ["Salbutamol", "Ibuprofeno"],
        "tipo": "Betabloqueador",
        "registro": "741852963",
        "alerta_idoso": True
    },
    "Diclofenaco": {
        "principio_ativo": "Diclofenaco sódico",
        "posologia": {
            "adulto": "50mg 2-3x/dia",
            "idoso": "50mg 2x/dia, usar com extrema cautela",
            "crianca": "1-2mg/kg/dia"
        },
        "duracao": "Máximo 5 dias",
        "contraindicacao": "Úlcera, insuficiência renal",
        "interacoes": ["AAS", "Warfarina"],
        "tipo": "AINE",
        "registro": "852963741",
        "alerta_idoso": True
    },
    "Cetirizina": {
        "principio_ativo": "Cetirizina",
        "posologia": {
            "adulto": "10mg 1x/dia",
            "idoso": "5mg 1x/dia, reduzir dose",
            "crianca": "5mg 1x/dia"
        },
        "duracao": "Conforme necessidade",
        "contraindicacao": "Insuficiência renal",
        "interacoes": ["Álcool"],
        "tipo": "Anti-histamínico (2ª geração)",
        "registro": "963741852",
        "alerta_idoso": True
    },
    "Loratadina": {
        "principio_ativo": "Loratadina",
        "posologia": {
            "adulto": "10mg 1x/dia",
            "idoso": "10mg 1x/dia, sem ajuste",
            "crianca": "5mg 1x/dia"
        },
        "duracao": "Conforme necessidade",
        "contraindicacao": "Alergia à loratadina",
        "interacoes": [],
        "tipo": "Anti-histamínico (2ª geração)",
        "registro": "159753456",
        "alerta_idoso": False
    },
    "Atorvastatina": {
        "principio_ativo": "Atorvastatina",
        "posologia": {
            "adulto": "10-80mg/dia",
            "idoso": "10-40mg/dia, avaliar interações",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Doença hepática ativa, gravidez",
        "interacoes": ["Ibuprofeno", "Amiodarona"],
        "tipo": "Hipolipemiante (estatina)",
        "registro": "753159456",
        "alerta_idoso": True
    },
    "Glibenclamida": {
        "principio_ativo": "Glibenclamida",
        "posologia": {
            "adulto": "2.5-5mg 1-2x/dia",
            "idoso": "2.5mg 1x/dia, dose reduzida",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Diabetes tipo 1, insuficiência renal",
        "interacoes": ["Álcool", "Ibuprofeno"],
        "tipo": "Antidiabético (sulfonilureia)",
        "registro": "456753159",
        "alerta_idoso": True
    },
    "Insulina NPH": {
        "principio_ativo": "Insulina NPH",
        "posologia": {
            "adulto": "Dose individualizada (10-30 U/dia)",
            "idoso": "Dose individualizada, risco de hipoglicemia",
            "crianca": "Dose individualizada"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Hipoglicemia",
        "interacoes": ["Betabloqueadores", "Álcool"],
        "tipo": "Insulina (ação intermediária)",
        "registro": "159753753",
        "alerta_idoso": False
    },
    "Enalapril": {
        "principio_ativo": "Enalapril",
        "posologia": {
            "adulto": "5-20mg/dia",
            "idoso": "5-10mg/dia, ajuste de dose",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Gravidez, estenose renal",
        "interacoes": ["Ibuprofeno", "AAS"],
        "tipo": "Anti-hipertensivo (IECA)",
        "registro": "753951456",
        "alerta_idoso": True
    },
    "Captopril": {
        "principio_ativo": "Captopril",
        "posologia": {
            "adulto": "12.5-50mg 2-3x/dia",
            "idoso": "12.5-25mg 2x/dia, ajuste de dose",
            "crianca": "0.3-0.5mg/kg/dose"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Gravidez, estenose renal",
        "interacoes": ["Ibuprofeno", "AAS"],
        "tipo": "Anti-hipertensivo (IECA)",
        "registro": "951753456",
        "alerta_idoso": True
    },
    "Amlodipina": {
        "principio_ativo": "Amlodipina",
        "posologia": {
            "adulto": "5-10mg 1x/dia",
            "idoso": "5mg 1x/dia",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Hipotensão grave, choque cardiogênico",
        "interacoes": ["Simvastatina", "Ciclosporina"],
        "tipo": "Bloqueador de canal de cálcio",
        "registro": "456789951",
        "alerta_idoso": True
    },
    "Rosuvastatina": {
        "principio_ativo": "Rosuvastatina",
        "posologia": {
            "adulto": "5-40mg/dia",
            "idoso": "5-20mg/dia, ajuste de dose",
            "crianca": "Não recomendado"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Doença hepática ativa, gravidez",
        "interacoes": ["Ciclosporina", "Warfarina"],
        "tipo": "Hipolipemiante (estatina)",
        "registro": "789456123",
        "alerta_idoso": True
    },
    "Budesonida": {
        "principio_ativo": "Budesonida",
        "posologia": {
            "adulto": "200-800mcg 2x/dia (inalatório)",
            "idoso": "200-400mcg 2x/dia, dose mínima eficaz",
            "crianca": "100-400mcg 2x/dia"
        },
        "duracao": "Uso contínuo",
        "contraindicacao": "Alergia à budesonida",
        "interacoes": ["Cetoconazol", "Eritromicina"],
        "tipo": "Corticóide inalatório",
        "registro": "147258753",
        "alerta_idoso": False
    },
    "Bromexina": {
        "principio_ativo": "Bromexina",
        "posologia": {
            "adulto": "8-16mg 3x/dia",
            "idoso": "8mg 3x/dia, dose reduzida",
            "crianca": "4-8mg 3x/dia"
        },
        "duracao": "5-7 dias",
        "contraindicacao": "Úlcera, alergia à bromexina",
        "interacoes": [],
        "tipo": "Expectorante",
        "registro": "753951258",
        "alerta_idoso": True
    },
    "Guaifenesina": {
        "principio_ativo": "Guaifenesina",
        "posologia": {
            "adulto": "200-400mg a cada 4h, máximo 2.4g/dia",
            "idoso": "200mg a cada 6h, dose reduzida",
            "crianca": "100-200mg a cada 4h"
        },
        "duracao": "Conforme necessidade",
        "contraindicacao": "Alergia à guaifenesina",
        "interacoes": [],
        "tipo": "Expectorante",
        "registro": "258753951",
        "alerta_idoso": True
    },
    "N-acetilcisteina": {
        "principio_ativo": "Acetilcisteína",
        "posologia": {
            "adulto": "600mg 1x/dia",
            "idoso": "600mg 1x/dia, sem ajuste",
            "crianca": "100-200mg 2x/dia"
        },
        "duracao": "5-10 dias",
        "contraindicacao": "Alergia à acetilcisteína",
        "interacoes": ["Carbocisteína"],
        "tipo": "Mucolítico",
        "registro": "951258753",
        "alerta_idoso": False
    },
    "Melatonina": {
        "principio_ativo": "Melatonina",
        "posologia": {
            "adulto": "3-10mg 1x/dia ao deitar",
            "idoso": "3-5mg 1x/dia ao deitar",
            "crianca": "Não recomendado"
        },
        "duracao": "Conforme necessidade",
        "contraindicacao": "Alergia à melatonina",
        "interacoes": ["Álcool", "Antidepressivos"],
        "tipo": "Hormônio do sono",
        "registro": "951753852",
        "alerta_idoso": False
    }
}

# ============================================
# BUSCAR CID POR SINTOMA (DIAGNÓSTICO INTELIGENTE COM NOME E GRAVIDADE)
# ============================================

def buscar_cid_por_sintoma(queixa, doencas=None, idade=None):
    """
    Busca no CSV os CIDs mais relevantes baseados na queixa e doenças.
    Retorna lista de diagnósticos com nome, gravidade e fonte.
    """
    queixa_lower = queixa.lower()
    palavras_chave = queixa_lower.split()
    
    # Palavras a ignorar
    palavras_ignorar = ["com", "e", "de", "do", "da", "para", "por", "na", "no", "em", "uma", "um", "as", "os", "à", "ao", "que", "se", "mas", "ou", "pois", "porque", "assim", "então"]
    palavras_filtradas = [p for p in palavras_chave if len(p) > 2 and p not in palavras_ignorar]
    
    # ===== Obter doenças informadas (para não duplicar) =====
    doencas_informadas = []
    if doencas:
        doencas_informadas = [d.strip().lower() for d in doencas.split(',') if d.strip()]
    
    # ===== 1. CIDs de doenças informadas (prioridade máxima) =====
    cids_doencas = []
    for doenca in doencas_informadas:
        for chave, info in MAPEAMENTO_DOENCAS_CID.items():
            if chave in doenca:
                if info['cid'] not in [c['codigo'] for c in cids_doencas]:
                    cids_doencas.append({
                        'codigo': info['cid'],
                        'nome': info['nome'],
                        'gravidade': info['gravidade'],
                        'fonte': 'Doença informada',
                        'prioridade': 1
                    })
    
    # ===== 2. CIDs de sintomas (prioridade média - apenas se não for doença informada) =====
    cids_sintomas = []
    for sintoma, info in MAPEAMENTO_SINTOMAS_CID.items():
        if sintoma in queixa_lower:
            # Verifica se o CID já está nas doenças informadas
            if info['cid'] not in [c['codigo'] for c in cids_doencas] and info['cid'] not in [c['codigo'] for c in cids_sintomas]:
                cids_sintomas.append({
                    'codigo': info['cid'],
                    'nome': info['nome'],
                    'gravidade': info['gravidade'],
                    'fonte': 'Sintoma',
                    'prioridade': 2
                })
    
    # ===== 3. CIDs do CSV (complementar - apenas se necessário) =====
    cids_csv = []
    if len(cids_doencas) + len(cids_sintomas) < 5:
        # Termos que indicam diagnósticos válidos
        termos_validos = ["dor", "febre", "tosse", "asma", "diabetes", "hipertensão", "artrite", "insônia", "ansiedade", "depressão", "infecção", "alergia", "gastrite", "refluxo", "sinusite", "faringite", "amigdalite", "otite", "gota", "colesterol", "obesidade"]
        
        for item in _CIDS:
            descricao_lower = item['descricao'].lower()
            codigo = item['codigo']
            # Verifica se o CID já foi adicionado
            if codigo in [c['codigo'] for c in cids_doencas] or codigo in [c['codigo'] for c in cids_sintomas] or codigo in [c['codigo'] for c in cids_csv]:
                continue
            
            # Busca por palavras-chave e verifica se é um termo válido
            for palavra in palavras_filtradas:
                if len(palavra) > 2 and palavra in descricao_lower:
                    # Verifica se é um diagnóstico válido
                    if any(termo in descricao_lower for termo in termos_validos):
                        # Determina gravidade
                        gravidade = "Moderada"
                        if any(p in descricao_lower for p in ["grave", "agudo", "severa", "crônico"]):
                            gravidade = "Grave"
                        elif any(p in descricao_lower for p in ["leve", "benigno", "menor"]):
                            gravidade = "Leve"
                        
                        cids_csv.append({
                            'codigo': codigo,
                            'nome': item['descricao'],
                            'gravidade': gravidade,
                            'fonte': 'CSV',
                            'prioridade': 3
                        })
                        break
    
    # ===== 4. Combinar e ordenar por prioridade =====
    todos_cids = cids_doencas + cids_sintomas + cids_csv
    
    # Remove duplicatas (mantém a primeira ocorrência)
    vistos = set()
    resultado_final = []
    for cid in todos_cids:
        if cid['codigo'] not in vistos:
            vistos.add(cid['codigo'])
            resultado_final.append(cid)
    
    # Limita a 7 diagnósticos
    return resultado_final[:7]

# ============================================
# FUNÇÃO DE BUSCA COM FALLBACK (LOCAL + API)
# ============================================

def buscar_medicamento_anvisa(nome):
    dados_api = buscar_medicamento_anvisa_api(nome)
    if dados_api:
        return dados_api
    
    nome_limpo = nome.strip().lower().capitalize()
    if nome_limpo in BASE_MEDICAMENTOS:
        dados = BASE_MEDICAMENTOS[nome_limpo].copy()
        dados["nome"] = nome_limpo
        dados["fonte"] = "Base local"
        return [dados]
    
    return {"erro": f"Medicamento '{nome}' não encontrado na ANVISA ou base local."}

# ============================================
# VERIFICAR SEGURANÇA (CORRIGIDO PARA IDOSOS)
# ============================================

def verificar_seguranca(idade, doencas, alergias, medicamento):
    alertas = []
    contraindicado = False
    
    doencas_lista = [d.strip().lower() for d in doencas.split(',') if d.strip()]
    alergias_lista = [a.strip().lower() for a in alergias.split(',') if a.strip()]

    regras = {
        "Paracetamol": {"contra_doencas": ["hepatopatia", "insuficiencia hepatica"], "contra_alergias": ["paracetamol"], "alerta_idoso": False},
        "Ibuprofeno": {"contra_doencas": ["ulcera", "gastrite", "insuficiencia renal", "insuficiencia cardiaca"], "contra_alergias": ["ibuprofeno", "aines", "aspirina"], "alerta_idoso": True},
        "Dipirona": {"contra_doencas": ["discrasias sanguineas", "anemia", "leucemia"], "contra_alergias": ["dipirona", "metamizol"], "alerta_idoso": True},
        "Losartana": {"contra_doencas": ["insuficiencia renal grave", "gravidez"], "contra_alergias": ["losartana"], "alerta_idoso": True},
        "Metformina": {"contra_doencas": ["insuficiencia renal", "acidose metabolica"], "contra_alergias": ["metformina"], "alerta_idoso": True},
        "Amoxicilina": {"contra_doencas": ["mononucleose"], "contra_alergias": ["penicilina", "amoxicilina"], "alerta_idoso": False},
        "Omeprazol": {"contra_doencas": [], "contra_alergias": ["omeprazol"], "alerta_idoso": True},
        "Sinvastatina": {"contra_doencas": ["doenca hepatica ativa", "gravidez"], "contra_alergias": ["sinvastatina", "estatinas"], "alerta_idoso": True},
        "Salbutamol": {"contra_doencas": ["arritmias", "hipertireoidismo"], "contra_alergias": ["salbutamol"], "alerta_idoso": True},
        "Propranolol": {"contra_doencas": ["asma", "bradicardia", "insuficiencia cardiaca"], "contra_alergias": ["propranolol"], "alerta_idoso": True},
        "Diclofenaco": {"contra_doencas": ["ulcera", "gastrite", "insuficiencia renal"], "contra_alergias": ["diclofenaco", "aines"], "alerta_idoso": True},
        "Cetirizina": {"contra_doencas": ["insuficiencia renal"], "contra_alergias": ["cetirizina"], "alerta_idoso": True},
        "Loratadina": {"contra_doencas": [], "contra_alergias": ["loratadina"], "alerta_idoso": False},
        "Atorvastatina": {"contra_doencas": ["doenca hepatica ativa", "gravidez"], "contra_alergias": ["atorvastatina"], "alerta_idoso": True},
        "Glibenclamida": {"contra_doencas": ["insuficiencia renal"], "contra_alergias": ["glibenclamida"], "alerta_idoso": True},
        "Insulina NPH": {"contra_doencas": [], "contra_alergias": ["insulina"], "alerta_idoso": False},
        "Enalapril": {"contra_doencas": ["gravidez", "estenose renal"], "contra_alergias": ["enalapril"], "alerta_idoso": True},
        "Captopril": {"contra_doencas": ["gravidez", "estenose renal"], "contra_alergias": ["captopril"], "alerta_idoso": True},
        "Amlodipina": {"contra_doencas": ["hipotensao grave"], "contra_alergias": ["amlodipina"], "alerta_idoso": True},
        "Rosuvastatina": {"contra_doencas": ["doenca hepatica ativa", "gravidez"], "contra_alergias": ["rosuvastatina"], "alerta_idoso": True},
        "Budesonida": {"contra_doencas": [], "contra_alergias": ["budesonida"], "alerta_idoso": False},
        "Bromexina": {"contra_doencas": ["ulcera"], "contra_alergias": ["bromexina"], "alerta_idoso": True},
        "Guaifenesina": {"contra_doencas": [], "contra_alergias": ["guaifenesina"], "alerta_idoso": True},
        "N-acetilcisteina": {"contra_doencas": [], "contra_alergias": ["acetilcisteina"], "alerta_idoso": False},
        "Melatonina": {"contra_doencas": [], "contra_alergias": ["melatonina"], "alerta_idoso": False}
    }

    regra_med = regras.get(medicamento, {})

    if idade > 65:
        if regra_med.get('alerta_idoso', False):
            alertas.append("⚠️ Medicamento com risco aumentado em idosos")
            medicamentos_alto_risco = ["Ibuprofeno", "Diclofenaco", "Naproxeno", "Celecoxib", "Diazepam", "Alprazolam", "Zolpidem"]
            if medicamento in medicamentos_alto_risco:
                alertas.append("❌ Medicamento de alto risco para idosos - evitar")
                contraindicado = True
        else:
            alertas.append("✅ Medicamento seguro para idosos (com ajuste de dose)")
            if medicamento == "Paracetamol":
                alertas.append("⚠️ Ajustar dose em idosos: máximo 3g/dia")
            elif medicamento == "Budesonida":
                alertas.append("⚠️ Usar dose mínima eficaz em idosos (200mcg 2x/dia)")
            elif medicamento == "Melatonina":
                alertas.append("⚠️ Dose para idosos: 3-5mg ao deitar")

    if any(p in doencas.lower() for p in ["hipertensao", "hipertensão"]) and medicamento in ["Ibuprofeno", "Diclofenaco", "Naproxeno", "Celecoxib"]:
        alertas.append("❌ AINE contraindicado em hipertensos (pode elevar a pressão)")
        contraindicado = True

    for doenca in doencas_lista:
        for contra in regra_med.get('contra_doencas', []):
            if contra in doenca:
                alertas.append(f"❌ Contraindicado para: {doenca}")
                contraindicado = True

    for alergia in alergias_lista:
        for contra in regra_med.get('contra_alergias', []):
            if contra in alergia:
                alertas.append(f"❌ Alergia a: {alergia}")
                contraindicado = True

    alertas = list(dict.fromkeys(alertas))

    return {
        "seguro": not contraindicado and len(alertas) <= 1,
        "contraindicado": contraindicado,
        "alertas": alertas,
        "nivel": "Vermelho" if contraindicado else "Amarelo" if alertas else "Verde"
    }

# ============================================
# ANÁLISE DE QUEIXA (PRINCIPAL)
# ============================================

def analisar_queixa(queixa, idade, doencas, alergias, medicamentos_atuais):
    queixa_lower = queixa.lower()
    sugestoes = []
    cids_encontrados = []
    medicamentos_encontrados = set()
    alertas = []

    # ============================================================
    # 1. DIAGNÓSTICO (CID-10) - COM NOME E GRAVIDADE
    # ============================================================

    cids_encontrados = buscar_cid_por_sintoma(queixa_lower, doencas, idade)
    
    if not cids_encontrados:
        cids_encontrados = [{
            'codigo': 'R69',
            'nome': 'Sintomas inespecíficos',
            'gravidade': 'Leve',
            'fonte': 'Fallback',
            'prioridade': 0
        }]

    # ============================================================
    # 2. SUGESTÃO DE MEDICAMENTOS
    # ============================================================

    for sintoma, medicamentos in MAPEAMENTO_SINTOMAS_MEDICAMENTOS.items():
        if sintoma in queixa_lower:
            for med in medicamentos:
                medicamentos_encontrados.add(med)

    if doencas:
        doencas_lista = [d.strip().lower() for d in doencas.split(',') if d.strip()]
        for doenca in doencas_lista:
            for chave, medicamentos in MAPEAMENTO_DOENCAS_MEDICAMENTOS.items():
                if chave in doenca:
                    for med in medicamentos:
                        medicamentos_encontrados.add(med)

    # ============================================================
    # 3. REMOVER MEDICAMENTOS EM USO
    # ============================================================
    
    if medicamentos_atuais:
        atuais = set()
        for item in medicamentos_atuais.split(','):
            item = item.strip().lower()
            nomes_medicamentos = [
                'metformina', 'losartana', 'omeprazol', 'enalapril', 'captopril',
                'sinvastatina', 'atorvastatina', 'rosuvastatina', 'glibenclamida',
                'insulina', 'salbutamol', 'budesonida', 'diclofenaco', 'ibuprofeno',
                'paracetamol', 'dipirona', 'amoxicilina', 'azitromicina', 'cefalexina',
                'ciprofloxacino', 'nitrofurantoina', 'pantoprazol', 'ranitidina',
                'diazepam', 'alprazolam', 'zolpidem', 'fluoxetina', 'sertralina',
                'amitriptilina', 'propranolol', 'metoprolol', 'carvedilol', 'atenolol',
                'amlodipina', 'hidroclorotiazida', 'furosemida', 'espironolactona'
            ]
            for nome in nomes_medicamentos:
                if nome in item:
                    atuais.add(nome.capitalize())
                    break
        medicamentos_encontrados = medicamentos_encontrados - atuais

    if not medicamentos_encontrados:
        medicamentos_encontrados = {"Paracetamol", "Ibuprofeno", "Dipirona"}

    # ============================================================
    # 4. FILTRAR POR SEGURANÇA
    # ============================================================

    categorias = {
        "anti-hipertensivo": ["Losartana", "Captopril", "Enalapril", "Amlodipina", "Propranolol", "Metoprolol"],
        "antidiabetico": ["Metformina", "Glibenclamida", "Insulina NPH"],
        "broncodilatador": ["Salbutamol", "Budesonida", "Formoterol"],
        "expectorante": ["Bromexina", "Guaifenesina", "N-acetilcisteina"],
        "analgesico": ["Paracetamol", "Dipirona", "Ibuprofeno", "Diclofenaco", "Naproxeno"],
        "anti-hiperlipidemia": ["Sinvastatina", "Atorvastatina", "Rosuvastatina"],
        "antialergico": ["Cetirizina", "Loratadina"],
        "ansiolitico": ["Diazepam", "Alprazolam"],
        "antidepressivo": ["Fluoxetina", "Sertralina"],
        "hipnotico": ["Zolpidem", "Melatonina"]
    }

    medicamento_categoria = {}
    for cat, meds in categorias.items():
        for med in meds:
            medicamento_categoria[med] = cat

    prioridades = []
    if any(p in queixa_lower for p in ["falta de ar", "dificuldade respiratoria", "asma"]):
        prioridades.append("broncodilatador")
    if any(p in queixa_lower for p in ["pressao alta", "hipertensao", "taquicardia"]):
        prioridades.append("anti-hipertensivo")
    if any(p in queixa_lower for p in ["diabetes", "sede", "urinar"]):
        prioridades.append("antidiabetico")
    if any(p in queixa_lower for p in ["dor", "enxaqueca", "cefaleia"]):
        prioridades.append("analgesico")
    if any(p in queixa_lower for p in ["colesterol", "dislipidemia"]):
        prioridades.append("anti-hiperlipidemia")
    if any(p in queixa_lower for p in ["alergia", "coceira", "urticaria"]):
        prioridades.append("antialergico")
    if any(p in queixa_lower for p in ["ansiedade", "insonia", "insônia"]):
        prioridades.append("hipnotico")
    if any(p in queixa_lower for p in ["depressao"]):
        prioridades.append("antidepressivo")

    selecionados = []

    for cat in prioridades:
        meds_cat = [m for m in medicamentos_encontrados if medicamento_categoria.get(m) == cat]
        meds_cat.sort(key=lambda m: 0 if not BASE_MEDICAMENTOS.get(m, {}).get('alerta_idoso', True) else 1)
        if meds_cat:
            melhor = meds_cat[0]
            if melhor not in selecionados:
                selecionados.append(melhor)
        if len(selecionados) >= 5:
            break

    if len(selecionados) < 5:
        restantes = [m for m in medicamentos_encontrados if m not in selecionados]
        restantes.sort(key=lambda m: (
            0 if not BASE_MEDICAMENTOS.get(m, {}).get('alerta_idoso', True) else 1,
            0 if BASE_MEDICAMENTOS.get(m, {}).get('posologia') else 1
        ))
        for m in restantes:
            if m not in selecionados:
                selecionados.append(m)
            if len(selecionados) >= 5:
                break

    # ============================================================
    # 5. CONSTRUIR AS SUGESTÕES FINAIS
    # ============================================================

    for med in selecionados:
        dados_local = BASE_MEDICAMENTOS.get(med, {})
        
        dados_api = buscar_medicamento_anvisa_api(med)
        if dados_api and isinstance(dados_api, list) and dados_api:
            info_med = dados_api[0]
            if info_med.get('registro') in (None, '', 'N/A'):
                info_med['registro'] = dados_local.get('registro', 'N/A')
            if info_med.get('tipo') in (None, '', 'N/A'):
                info_med['tipo'] = dados_local.get('tipo', 'N/A')
            if info_med.get('empresa') in (None, '', 'N/A'):
                info_med['empresa'] = dados_local.get('empresa', 'N/A')
            info_med['fonte'] = 'ANVISA'
        else:
            info_med = {
                "principio_ativo": dados_local.get('principio_ativo', med),
                "empresa": dados_local.get('empresa', 'N/A'),
                "registro": dados_local.get('registro', 'N/A'),
                "tipo": dados_local.get('tipo', 'N/A'),
                "fonte": "Base local"
            }

        posologia_dict = dados_local.get('posologia', {})
        if idade > 65:
            posologia_texto = posologia_dict.get('idoso', posologia_dict.get('adulto', 'Consultar bula'))
        elif idade < 18:
            posologia_texto = posologia_dict.get('crianca', posologia_dict.get('adulto', 'Consultar bula'))
        else:
            posologia_texto = posologia_dict.get('adulto', 'Consultar bula')

        seguranca = verificar_seguranca(idade, doencas, alergias, med)

        sugestao = {
            'medicamento': med,
            'principio_ativo': info_med.get('principio_ativo', med),
            'laboratorio': info_med.get('empresa', 'N/A'),
            'registro': info_med.get('registro', 'N/A'),
            'tipo': info_med.get('tipo', 'N/A'),
            'fonte': info_med.get('fonte', 'Base local'),
            'posologia': posologia_texto,
            'duracao': dados_local.get('duracao', 'Consultar bula'),
            'contraindicacao': dados_local.get('contraindicacao', 'N/A'),
            'interacoes': dados_local.get('interacoes', []),
            'seguranca': seguranca
        }
        sugestoes.append(sugestao)

    # ============================================================
    # 6. ORDENAR POR SEGURANÇA
    # ============================================================

    ordem = {"Verde": 0, "Amarelo": 1, "Vermelho": 2}
    sugestoes.sort(key=lambda x: ordem.get(x['seguranca']['nivel'], 3))

    # ============================================================
    # 7. ALERTAS ESPECÍFICOS
    # ============================================================

    if idade > 65:
        alertas.append("🧓 Idoso (>65 anos): atenção redobrada com doses e interações")
    if "sede" in queixa_lower or "urinar" in queixa_lower:
        alertas.append("⚠️ Sintomas sugestivos de hiperglicemia - monitorar glicemia")
    if "fadiga" in queixa_lower:
        alertas.append("⚠️ Fadiga - pode ser relacionada à diabetes ou anemia")
    if "visão embaçada" in queixa_lower or "visao embacada" in queixa_lower:
        alertas.append("⚠️ Visão embaçada - possível retinopatia diabética, encaminhar ao oftalmologista")
    if "diabetes" in doencas.lower():
        alertas.append("🩸 Paciente diabético - evitar corticoides, ajustar antidiabéticos")
    if "hipertensao" in doencas.lower():
        alertas.append("❤️ Paciente hipertenso - evitar AINEs (ibuprofeno, diclofenaco)")
    if "dislipidemia" in doencas.lower():
        alertas.append("🩺 Paciente com dislipidemia - manter estatinas e orientar dieta")
    if alergias:
        alertas.append(f"⚠️ Alergias registradas: {alergias}")
    if medicamentos_atuais:
        alertas.append(f"💊 Medicamentos em uso: {medicamentos_atuais}")

    # ============================================================
    # 8. CALCULAR SEGUROS
    # ============================================================

    seguros = sum(1 for s in sugestoes if s['seguranca']['seguro'])

    # ============================================================
    # 9. RETORNO
    # ============================================================

    return {
        'diagnostico': {
            'cids': cids_encontrados,
            'descricao': f'Diagnóstico baseado nos sintomas e doenças informadas (CSV contém {len(_CIDS)} CIDs)'
        },
        'sugestoes': sugestoes,
        'total_sugestoes': len(sugestoes),
        'seguros': seguros,
        'alertas': alertas,
        'analise_realizada': True,
        'fonte': 'ANVISA + Base local + CID-10'
    }