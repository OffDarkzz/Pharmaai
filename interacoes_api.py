# ============================================
# INTERAÇÕES MEDICAMENTOSAS - MÚLTIPLAS FONTES
# ============================================

import re
from datetime import datetime
from api_pharmadb import buscar_interacoes_pharmadb

# ============================================
# BASE LOCAL DE INTERAÇÕES (FALLBACK)
# ============================================

INTERACOES_LOCAL = {
    # === ANTICOAGULANTES + AINEs ===
    ("warfarin", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de sangramento aumentado significativamente.",
        "recomendacao": "🚫 EVITAR associação. Monitorar INR e sinais de sangramento."
    },
    ("warfarin", "diclofenaco"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de sangramento aumentado significativamente.",
        "recomendacao": "🚫 EVITAR associação. Monitorar INR."
    },
    ("warfarin", "aas"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de sangramento aumentado significativamente.",
        "recomendacao": "🚫 EVITAR associação. Monitorar INR rigorosamente."
    },
    ("warfarin", "amoxicilina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Amoxicilina pode potencializar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR frequentemente."
    },
    ("warfarin", "azitromicina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Azitromicina pode potencializar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR frequentemente."
    },
    ("warfarin", "ciprofloxacino"): {
        "nivel": "Grave",
        "descricao": "⚠️ Ciprofloxacino pode potencializar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR frequentemente."
    },
    ("warfarin", "metronidazol"): {
        "nivel": "Grave",
        "descricao": "⚠️ Metronidazol potencializa o efeito da Warfarina.",
        "recomendacao": "🚫 EVITAR associação ou monitorar INR diariamente."
    },
    ("warfarin", "fluconazol"): {
        "nivel": "Grave",
        "descricao": "⚠️ Fluconazol potencializa o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR frequentemente."
    },
    ("warfarin", "clopidogrel"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de sangramento aumentado.",
        "recomendacao": "🔬 Monitorar sinais de sangramento."
    },
    ("warfarin", "heparina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de sangramento aumentado significativamente.",
        "recomendacao": "🔬 Monitorar coagulação rigorosamente."
    },
    ("warfarin", "sertralina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Sertralina pode aumentar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR."
    },
    ("warfarin", "fluoxetina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Fluoxetina pode aumentar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR."
    },
    ("warfarin", "amiodarona"): {
        "nivel": "Grave",
        "descricao": "⚠️ Amiodarona aumenta o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR frequentemente."
    },
    
    # === ANTI-HIPERTENSIVOS + AINEs ===
    ("losartana", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo e aumentar o risco de lesão renal.",
        "recomendacao": "🚫 EVITAR associação. Preferir Paracetamol para dor."
    },
    ("losartana", "diclofenaco"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo e aumentar o risco de lesão renal.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("captopril", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("enalapril", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("ramipril", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("valsartana", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito anti-hipertensivo.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("losartana", "espironolactona"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de hipercalemia grave.",
        "recomendacao": "🔬 Monitorar níveis de potássio."
    },
    
    # === ANTIDIABÉTICOS ===
    ("metformina", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode alterar função renal e aumentar o risco de acidose lática.",
        "recomendacao": "🔬 Monitorar função renal. Evitar uso prolongado."
    },
    ("metformina", "diclofenaco"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de acidose lática e lesão renal.",
        "recomendacao": "🔬 Monitorar função renal."
    },
    ("metformina", "insulina"): {
        "nivel": "Moderada",
        "descricao": "🟡 Efeito hipoglicemiante potencializado.",
        "recomendacao": "🔬 Monitorar glicemia e ajustar doses."
    },
    ("metformina", "glibenclamida"): {
        "nivel": "Moderada",
        "descricao": "🟡 Efeito hipoglicemiante potencializado.",
        "recomendacao": "🔬 Monitorar glicemia e ajustar doses."
    },
    ("metformina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Risco de acidose lática aumentado.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    
    # === ESTATINAS ===
    ("sinvastatina", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de miopatia e rabdomiólise aumentado.",
        "recomendacao": "🚫 EVITAR associação ou monitorar sintomas musculares."
    },
    ("atorvastatina", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de miopatia e rabdomiólise aumentado.",
        "recomendacao": "🚫 EVITAR associação ou monitorar sintomas musculares."
    },
    ("rosuvastatina", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de miopatia e rabdomiólise aumentado.",
        "recomendacao": "🚫 EVITAR associação ou monitorar sintomas musculares."
    },
    ("sinvastatina", "amiodarona"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de miopatia e rabdomiólise aumentado.",
        "recomendacao": "🚫 EVITAR associação. Considerar alternativa."
    },
    ("atorvastatina", "amiodarona"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de miopatia e rabdomiólise aumentado.",
        "recomendacao": "🚫 EVITAR associação. Considerar alternativa."
    },
    ("rosuvastatina", "ciclosporina"): {
        "nivel": "Moderada",
        "descricao": "🟡 Aumento da concentração de Rosuvastatina.",
        "recomendacao": "🔬 Ajustar dose e monitorar função renal."
    },
    
    # === ANTIBIÓTICOS ===
    ("amoxicilina", "metotrexato"): {
        "nivel": "Moderada",
        "descricao": "🟡 Amoxicilina pode aumentar a toxicidade do Metotrexato.",
        "recomendacao": "🔬 Monitorar sinais de toxicidade."
    },
    ("ciprofloxacino", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de convulsões aumentado.",
        "recomendacao": "🚫 EVITAR associação em pacientes com epilepsia."
    },
    ("ciprofloxacino", "teofilina"): {
        "nivel": "Grave",
        "descricao": "⚠️ Aumento da concentração de Teofilina.",
        "recomendacao": "🔬 Monitorar níveis de Teofilina."
    },
    ("azitromicina", "digoxina"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode aumentar a concentração de Digoxina.",
        "recomendacao": "🔬 Monitorar níveis de Digoxina."
    },
    
    # === ANTIDEPRESSIVOS ===
    ("fluoxetina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode potencializar o efeito sedativo do álcool.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    ("sertralina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode potencializar o efeito sedativo do álcool.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    ("amitriptilina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Potencialização do efeito sedativo.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    ("fluoxetina", "warfarin"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode aumentar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR."
    },
    ("sertralina", "warfarin"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode aumentar o efeito da Warfarina.",
        "recomendacao": "🔬 Monitorar INR."
    },
    ("fluoxetina", "tramadol"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de síndrome serotoninérgica.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("sertralina", "tramadol"): {
        "nivel": "Grave",
        "descricao": "⚠️ Risco de síndrome serotoninérgica.",
        "recomendacao": "🚫 EVITAR associação."
    },
    
    # === BENZODIAZEPÍNICOS ===
    ("diazepam", "alcool"): {
        "nivel": "Grave",
        "descricao": "⚠️ Potencialização do efeito sedativo. Risco de depressão respiratória.",
        "recomendacao": "🚫 EVITAR consumo de álcool durante o tratamento."
    },
    ("alprazolam", "alcool"): {
        "nivel": "Grave",
        "descricao": "⚠️ Potencialização do efeito sedativo. Risco de depressão respiratória.",
        "recomendacao": "🚫 EVITAR consumo de álcool durante o tratamento."
    },
    ("zolpidem", "alcool"): {
        "nivel": "Grave",
        "descricao": "⚠️ Potencialização do efeito sedativo. Risco de depressão respiratória.",
        "recomendacao": "🚫 EVITAR consumo de álcool durante o tratamento."
    },
    ("clonazepam", "alcool"): {
        "nivel": "Grave",
        "descricao": "⚠️ Potencialização do efeito sedativo. Risco de depressão respiratória.",
        "recomendacao": "🚫 EVITAR consumo de álcool durante o tratamento."
    },
    ("diazepam", "antidepressivos"): {
        "nivel": "Moderada",
        "descricao": "🟡 Potencialização do efeito sedativo.",
        "recomendacao": "⚠️ Usar com cautela. Monitorar sonolência."
    },
    
    # === INIBIDORES DE BOMBA DE PRÓTONS ===
    ("omeprazol", "clopidogrel"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode reduzir o efeito do Clopidogrel.",
        "recomendacao": "🔄 Considerar alternativa (Pantoprazol) ou monitorar eficácia."
    },
    ("omeprazol", "cetoconazol"): {
        "nivel": "Moderada",
        "descricao": "🟡 Omeprazol pode reduzir a absorção do Cetoconazol.",
        "recomendacao": "⏰ Administrar Cetoconazol 2 horas antes do Omeprazol."
    },
    ("omeprazol", "digoxina"): {
        "nivel": "Moderada",
        "descricao": "🟡 Omeprazol pode aumentar a absorção da Digoxina.",
        "recomendacao": "🔬 Monitorar níveis de Digoxina."
    },
    
    # === ANTI-HISTAMÍNICOS ===
    ("cetirizina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode potencializar o efeito sedativo do álcool.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    ("loratadina", "alcool"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode potencializar o efeito sedativo do álcool.",
        "recomendacao": "🚫 Evitar consumo de álcool durante o tratamento."
    },
    
    # === BRONCODILATADORES + BETABLOQUEADORES ===
    ("salbutamol", "propranolol"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode reduzir o efeito broncodilatador do Salbutamol.",
        "recomendacao": "⚠️ Usar com cautela em pacientes asmáticos."
    },
    ("salbutamol", "metoprolol"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode reduzir o efeito broncodilatador do Salbutamol.",
        "recomendacao": "⚠️ Usar com cautela em pacientes asmáticos."
    },
    
    # === CARDIOLÓGICOS ===
    ("digoxina", "amiodarona"): {
        "nivel": "Grave",
        "descricao": "⚠️ Aumento da concentração de Digoxina. Risco de toxicidade.",
        "recomendacao": "🔬 Monitorar níveis de Digoxina e ajustar dose."
    },
    ("digoxina", "verapamil"): {
        "nivel": "Grave",
        "descricao": "⚠️ Aumento da concentração de Digoxina. Risco de toxicidade.",
        "recomendacao": "🔬 Monitorar níveis de Digoxina."
    },
    ("digoxina", "furosemida"): {
        "nivel": "Moderada",
        "descricao": "🟡 Pode causar hipocalemia e aumentar o risco de arritmias.",
        "recomendacao": "🔬 Monitorar níveis de potássio."
    },
    
    # === OUTROS ===
    ("metotrexato", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Aumento da toxicidade do Metotrexato.",
        "recomendacao": "🚫 EVITAR associação ou monitorar níveis plasmáticos."
    },
    ("litio", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Aumento da concentração de Lítio. Risco de toxicidade.",
        "recomendacao": "🔬 Monitorar níveis de Lítio."
    },
    ("aas", "ibuprofeno"): {
        "nivel": "Grave",
        "descricao": "⚠️ Pode reduzir o efeito antiagregante do AAS.",
        "recomendacao": "⏰ Administrar Ibuprofeno 8 horas antes ou 2 horas após o AAS."
    },
    ("ibuprofeno", "diclofenaco"): {
        "nivel": "Grave",
        "descricao": "⚠️ Evitar associação de AINEs. Risco de efeitos adversos aditivos.",
        "recomendacao": "🚫 EVITAR associação."
    },
    ("losartana", "amlodipina"): {
        "nivel": "Moderada",
        "descricao": "🟡 Efeito anti-hipertensivo potencializado.",
        "recomendacao": "🔬 Monitorar pressão arterial."
    }
}

# ============================================
# SINÔNIMOS
# ============================================

SINONIMOS = {
    "warfarin": ["varfarina", "warfarin", "warf", "coumadin"],
    "ibuprofeno": ["ibuprofeno", "ibu", "ibupro", "advil", "motrin"],
    "aas": ["aas", "aspirina", "ácido acetilsalicílico"],
    "amoxicilina": ["amoxicilina", "amoxil", "amox"],
    "azitromicina": ["azitromicina", "zitromax", "azit"],
    "ciprofloxacino": ["ciprofloxacino", "cipro", "cip"],
    "losartana": ["losartana", "losart", "los", "cozaar"],
    "diclofenaco": ["diclofenaco", "diclofen", "voltaren"],
    "captopril": ["captopril", "cap", "capto"],
    "enalapril": ["enalapril", "enal", "renitec"],
    "metformina": ["metformina", "metform", "glifage"],
    "sinvastatina": ["sinvastatina", "sinvastat", "zocor"],
    "atorvastatina": ["atorvastatina", "atorvastat", "lipitor"],
    "rosuvastatina": ["rosuvastatina", "rosuvastat", "crestor"],
    "amiodarona": ["amiodarona", "amiodar", "cordarone"],
    "metotrexato": ["metotrexato", "metotrex"],
    "digoxina": ["digoxina", "digoxin"],
    "litio": ["lítio", "litio", "lithium"],
    "omeprazol": ["omeprazol", "omep", "losec", "prilosec"],
    "clopidogrel": ["clopidogrel", "clopidog", "plavix"],
    "cetirizina": ["cetirizina", "cetiriz", "zyrtec"],
    "loratadina": ["loratadina", "lorata", "clarityn"],
    "amlodipina": ["amlodipina", "amlodipin", "norvasc"],
    "glibenclamida": ["glibenclamida", "gliben", "daonil"],
    "insulina": ["insulina", "insulin"],
    "salbutamol": ["salbutamol", "salbuta", "ventolin"],
    "propranolol": ["propranolol", "propran", "inderal"],
    "metoprolol": ["metoprolol", "metoprol", "seloken"],
    "diazepam": ["diazepam", "diaze", "valium"],
    "alprazolam": ["alprazolam", "alpraz", "frontal", "xanax"],
    "zolpidem": ["zolpidem", "zolpid", "ambien"],
    "fluoxetina": ["fluoxetina", "fluox", "prozac"],
    "sertralina": ["sertralina", "sertra", "zoloft"],
    "metronidazol": ["metronidazol", "metron", "flagyl"],
    "fluconazol": ["fluconazol", "flucon", "zol"],
    "espironolactona": ["espironolactona", "espiron", "aldactone"],
    "naproxeno": ["naproxeno", "naprox", "naprosyn"],
    "celecoxib": ["celecoxib", "celeco", "celebrex"],
    "heparina": ["heparina", "heparin"],
    "ramipril": ["ramipril", "ramip", "tritace"],
    "valsartana": ["valsartana", "valsart", "diovan"],
    "atenolol": ["atenolol", "atenol", "tenormin"],
    "verapamil": ["verapamil", "verap", "isoptin"],
    "furosemida": ["furosemida", "furosem", "lasix"],
    "hidroclorotiazida": ["hidroclorotiazida", "hctz", "hidrocloro"],
    "tramadol": ["tramadol", "tramal"],
    "teofilina": ["teofilina", "teofil", "teo"],
    "pantoprazol": ["pantoprazol", "pantopraz", "panto"]
}

# ============================================
# FUNÇÃO DE NORMALIZAÇÃO
# ============================================

def normalizar_medicamento(nome):
    """Normaliza o nome do medicamento"""
    nome = nome.strip().lower()
    
    # Remove dose
    import re
    nome = re.sub(r'\d+mg', '', nome)
    nome = re.sub(r'\d+mcg', '', nome)
    nome = re.sub(r'\d+g', '', nome)
    nome = re.sub(r'\d+ml', '', nome)
    nome = nome.strip()
    
    # Remove palavras comuns
    palavras_remover = ['cloridrato', 'sódico', 'potássico', 'cálcico', 'comprimido', 'capsula', 'spray']
    for palavra in palavras_remover:
        nome = nome.replace(palavra, '').strip()
    
    # Verifica sinônimos
    for padrao, sinonimos in SINONIMOS.items():
        if nome in sinonimos:
            return padrao
        for sinonimo in sinonimos:
            if sinonimo in nome or nome in sinonimo:
                return padrao
    
    return nome

# ============================================
# FUNÇÃO PRINCIPAL
# ============================================

def verificar_interacoes(medicamentos):
    """
    Verifica interações entre medicamentos
    Prioridade: 1. PharmaDB (se disponível) 2. Base local
    """
    if not medicamentos:
        return []
    
    medicamentos = [m.strip() for m in medicamentos if m.strip()]
    if len(medicamentos) < 2:
        return []
    
    todas_interacoes = []
    vistos = set()
    
    # Normalizar medicamentos
    medicamentos_norm = []
    medicamentos_orig = []
    
    for med in medicamentos:
        normalizado = normalizar_medicamento(med)
        medicamentos_norm.append(normalizado)
        medicamentos_orig.append(med)
    
    # 1. Tentar PharmaDB (se tiver chave configurada)
    from api_pharmadb import PHARMADB_API_KEY
    if PHARMADB_API_KEY:
        for i, med1 in enumerate(medicamentos_norm):
            for j, med2 in enumerate(medicamentos_norm):
                if i >= j:
                    continue
                
                chave = tuple(sorted([med1, med2]))
                if chave in vistos:
                    continue
                vistos.add(chave)
                
                resultado = buscar_interacoes_pharmadb(med1)
                if resultado and not resultado.get('erro'):
                    for inter in resultado.get('interacoes', []):
                        if med2 in inter.get('medicamento', '').lower():
                            todas_interacoes.append({
                                'medicamento1': medicamentos_orig[i],
                                'medicamento2': medicamentos_orig[j],
                                'nivel': inter.get('severidade', 'Moderada'),
                                'descricao': inter.get('descricao', 'Interação identificada na PharmaDB'),
                                'recomendacao': inter.get('recomendacao', 'Consultar bula para detalhes'),
                                'fonte': 'PharmaDB',
                                'data': datetime.now().strftime('%d/%m/%Y')
                            })
    
    # 2. Fallback para base local (se não encontrou ou PharmaDB não disponível)
    if not todas_interacoes:
        for i, med1 in enumerate(medicamentos_norm):
            for j, med2 in enumerate(medicamentos_norm):
                if i >= j:
                    continue
                
                chave1 = (med1, med2)
                chave2 = (med2, med1)
                chave = tuple(sorted([med1, med2]))
                
                if chave in vistos:
                    continue
                vistos.add(chave)
                
                interacao = None
                if chave1 in INTERACOES_LOCAL:
                    interacao = INTERACOES_LOCAL[chave1].copy()
                elif chave2 in INTERACOES_LOCAL:
                    interacao = INTERACOES_LOCAL[chave2].copy()
                
                if interacao:
                    interacao['medicamento1'] = medicamentos_orig[i]
                    interacao['medicamento2'] = medicamentos_orig[j]
                    interacao['fonte'] = 'Base local'
                    interacao['data'] = datetime.now().strftime('%d/%m/%Y')
                    todas_interacoes.append(interacao)
    
    return todas_interacoes

def verificar_interacoes_prescricao(medicamentos_receitados, medicamentos_atuais):
    """Verifica interações entre medicamentos receitados e em uso"""
    lista_medicamentos = []
    
    if medicamentos_receitados:
        for linha in medicamentos_receitados.split('\n'):
            linha = linha.strip()
            if linha and len(linha) > 3:
                nome = linha.split('-')[0].strip()
                if nome:
                    lista_medicamentos.append(nome)
    
    if medicamentos_atuais:
        for item in medicamentos_atuais.split(','):
            item = item.strip()
            if item:
                nome = item.split()[0].strip()
                if nome:
                    lista_medicamentos.append(nome)
    
    return verificar_interacoes(lista_medicamentos)

def buscar_interacao(med1, med2):
    """Busca interação entre dois medicamentos específicos"""
    resultado = verificar_interacoes([med1, med2])
    return resultado[0] if resultado else None