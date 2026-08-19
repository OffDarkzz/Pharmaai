# ============================================
# CÁLCULO DE DOSE POR PESO
# ============================================

import re

# Base de dados de medicamentos com dose por peso
MEDICAMENTOS_DOSE = {
    "Paracetamol": {
        "dose_padrao": "500mg",
        "dose_peso": "10-15mg/kg",
        "dose_maxima_diaria": "4g",
        "intervalo": "4-6h",
        "observacao": "Máximo 5 dias de uso"
    },
    "Ibuprofeno": {
        "dose_padrao": "200-400mg",
        "dose_peso": "5-10mg/kg",
        "dose_maxima_diaria": "1.2g",
        "intervalo": "6-8h",
        "observacao": "Máximo 3-5 dias de uso"
    },
    "Amoxicilina": {
        "dose_padrao": "500mg",
        "dose_peso": "20-40mg/kg/dia",
        "dose_maxima_diaria": "2g",
        "intervalo": "8h",
        "observacao": "Dividir em 3 doses"
    },
    "Metformina": {
        "dose_padrao": "500mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "2.55g",
        "intervalo": "12h",
        "observacao": "Iniciar com dose baixa"
    },
    "Salbutamol": {
        "dose_padrao": "100-200mcg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "800mcg",
        "intervalo": "4-6h",
        "observacao": "Uso inalatório"
    },
    "Dipirona": {
        "dose_padrao": "500mg",
        "dose_peso": "10-15mg/kg",
        "dose_maxima_diaria": "4g",
        "intervalo": "6h",
        "observacao": "Máximo 3 dias de uso"
    },
    "Losartana": {
        "dose_padrao": "50mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "100mg",
        "intervalo": "24h",
        "observacao": "Ajuste conforme pressão"
    },
    "Omeprazol": {
        "dose_padrao": "20mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "40mg",
        "intervalo": "24h",
        "observacao": "Tomar antes do café da manhã"
    },
    "Sinvastatina": {
        "dose_padrao": "20mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "80mg",
        "intervalo": "24h",
        "observacao": "Tomar à noite"
    },
    "Azitromicina": {
        "dose_padrao": "500mg",
        "dose_peso": "10mg/kg",
        "dose_maxima_diaria": "500mg",
        "intervalo": "24h",
        "observacao": "3 dias de tratamento"
    },
    "Cefalexina": {
        "dose_padrao": "500mg",
        "dose_peso": "25-50mg/kg/dia",
        "dose_maxima_diaria": "4g",
        "intervalo": "6h",
        "observacao": "Dividir em 4 doses"
    },
    "Glibenclamida": {
        "dose_padrao": "2.5mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "15mg",
        "intervalo": "12h",
        "observacao": "Iniciar com dose baixa"
    },
    "Insulina NPH": {
        "dose_padrao": "10-30U",
        "dose_peso": "0.2-0.4U/kg",
        "dose_maxima_diaria": "N/A",
        "intervalo": "24h",
        "observacao": "Dose individualizada"
    },
    "Diclofenaco": {
        "dose_padrao": "50mg",
        "dose_peso": "1-2mg/kg",
        "dose_maxima_diaria": "150mg",
        "intervalo": "8-12h",
        "observacao": "Máximo 5 dias de uso"
    },
    "Cetirizina": {
        "dose_padrao": "10mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "10mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Loratadina": {
        "dose_padrao": "10mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "10mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Atorvastatina": {
        "dose_padrao": "20mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "80mg",
        "intervalo": "24h",
        "observacao": "Tomar à noite"
    },
    "Rosuvastatina": {
        "dose_padrao": "10mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "40mg",
        "intervalo": "24h",
        "observacao": "Tomar à noite"
    },
    "Budesonida": {
        "dose_padrao": "200mcg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "800mcg",
        "intervalo": "12h",
        "observacao": "Uso inalatório"
    },
    "N-acetilcisteina": {
        "dose_padrao": "600mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "1.2g",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Propranolol": {
        "dose_padrao": "40mg",
        "dose_peso": "0.5-1mg/kg",
        "dose_maxima_diaria": "240mg",
        "intervalo": "12h",
        "observacao": "Dividir em 2-3 doses"
    },
    "Metoprolol": {
        "dose_padrao": "50mg",
        "dose_peso": "0.5-1mg/kg",
        "dose_maxima_diaria": "200mg",
        "intervalo": "12h",
        "observacao": "Dividir em 2 doses"
    },
    "Amlodipina": {
        "dose_padrao": "5mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "10mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Enalapril": {
        "dose_padrao": "10mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "40mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Captopril": {
        "dose_padrao": "25mg",
        "dose_peso": "0.3-0.5mg/kg",
        "dose_maxima_diaria": "150mg",
        "intervalo": "8-12h",
        "observacao": "Dividir em 2-3 doses"
    },
    "Furosemida": {
        "dose_padrao": "40mg",
        "dose_peso": "0.5-1mg/kg",
        "dose_maxima_diaria": "120mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Hidroclorotiazida": {
        "dose_padrao": "25mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "50mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Espironolactona": {
        "dose_padrao": "25mg",
        "dose_peso": "1-3mg/kg",
        "dose_maxima_diaria": "100mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Warfarina": {
        "dose_padrao": "5mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "10mg",
        "intervalo": "24h",
        "observacao": "Ajuste por INR"
    },
    "Clopidogrel": {
        "dose_padrao": "75mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "75mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Prednisona": {
        "dose_padrao": "20mg",
        "dose_peso": "0.1-2mg/kg",
        "dose_maxima_diaria": "60mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Dexametasona": {
        "dose_padrao": "4mg",
        "dose_peso": "0.1-0.5mg/kg",
        "dose_maxima_diaria": "16mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Fluconazol": {
        "dose_padrao": "150mg",
        "dose_peso": "3-6mg/kg",
        "dose_maxima_diaria": "400mg",
        "intervalo": "24h",
        "observacao": "Dose única diária"
    },
    "Aciclovir": {
        "dose_padrao": "200mg",
        "dose_peso": "10-20mg/kg",
        "dose_maxima_diaria": "800mg",
        "intervalo": "4-6h",
        "observacao": "5 vezes ao dia"
    },
    "Metronidazol": {
        "dose_padrao": "400mg",
        "dose_peso": "15-30mg/kg",
        "dose_maxima_diaria": "1.5g",
        "intervalo": "8h",
        "observacao": "Dividir em 3 doses"
    },
    "Diazepam": {
        "dose_padrao": "5mg",
        "dose_peso": "0.1-0.3mg/kg",
        "dose_maxima_diaria": "30mg",
        "intervalo": "6-8h",
        "observacao": "Uso conforme necessidade"
    },
    "Alprazolam": {
        "dose_padrao": "0.5mg",
        "dose_peso": "N/A",
        "dose_maxima_diaria": "4mg",
        "intervalo": "8h",
        "observacao": "Uso conforme necessidade"
    }
}

def calcular_dose(medicamento, peso, idade):
    """
    Calcula a dose recomendada baseada no peso do paciente
    Retorna dicionário com dose calculada e informações
    """
    if not peso or peso <= 0:
        return {
            'erro': 'Peso não informado',
            'dose_calculada': 'Informe o peso do paciente',
            'dose_recomendada': 'Não disponível'
        }
    
    if medicamento not in MEDICAMENTOS_DOSE:
        return {
            'erro': 'Medicamento não encontrado na base',
            'dose_calculada': 'Medicamento sem dose por peso',
            'dose_recomendada': 'Consultar bula'
        }
    
    info = MEDICAMENTOS_DOSE[medicamento]
    dose_peso = info.get('dose_peso', 'N/A')
    dose_padrao = info.get('dose_padrao', 'N/A')
    
    # Calcular dose baseada no peso
    dose_calculada = None
    if dose_peso != 'N/A' and 'mg/kg' in dose_peso:
        try:
            numeros = re.findall(r'(\d+\.?\d*)', dose_peso)
            if len(numeros) >= 1:
                min_dose = float(numeros[0])
                max_dose = float(numeros[1]) if len(numeros) > 1 else min_dose
                dose_min = round(min_dose * peso, 1)
                dose_max = round(max_dose * peso, 1)
                dose_calculada = f"{dose_min}-{dose_max}mg"
                
                # Ajuste para idosos
                if idade > 65:
                    dose_calculada = f"{dose_min * 0.7:.1f}-{dose_max * 0.7:.1f}mg (idoso)"
        except Exception as e:
            dose_calculada = dose_padrao
    else:
        dose_calculada = dose_padrao
    
    return {
        'medicamento': medicamento,
        'peso': peso,
        'idade': idade,
        'dose_peso': dose_peso,
        'dose_padrao': dose_padrao,
        'dose_calculada': dose_calculada or 'Consultar bula',
        'dose_maxima_diaria': info.get('dose_maxima_diaria', 'N/A'),
        'intervalo': info.get('intervalo', 'N/A'),
        'observacao': info.get('observacao', 'N/A')
    }

def calcular_dose_para_paciente(paciente, medicamentos):
    """
    Calcula a dose para uma lista de medicamentos
    """
    resultados = []
    for med in medicamentos:
        resultado = calcular_dose(med, paciente.peso, paciente.idade)
        resultados.append(resultado)
    return resultados