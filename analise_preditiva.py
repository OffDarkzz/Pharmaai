# ============================================
# ANÁLISE PREDITIVA
# ============================================

import math
from datetime import datetime, timedelta
from models import Paciente, Consulta, MedicamentoPrescrito

# ============================================
# 1. CÁLCULO DE RISCO DE DIABETES
# ============================================

def calcular_risco_diabetes(paciente):
    """
    Calcula o risco de diabetes tipo 2 baseado em:
    - Idade
    - IMC
    - Glicemia (última medição)
    - Histórico familiar (doenças informadas)
    """
    risco = 0
    fatores = []
    
    # Idade
    if paciente.idade >= 65:
        risco += 25
        fatores.append("Idade avançada (>65 anos)")
    elif paciente.idade >= 45:
        risco += 15
        fatores.append("Idade ≥45 anos")
    
    # IMC
    if paciente.peso and paciente.altura:
        imc = paciente.peso / ((paciente.altura/100) ** 2)
        if imc >= 30:
            risco += 25
            fatores.append(f"IMC ≥30 (Obesidade: {imc:.1f})")
        elif imc >= 25:
            risco += 15
            fatores.append(f"IMC ≥25 (Sobrepeso: {imc:.1f})")
    
    # Glicemia (última consulta)
    ultima_consulta = Consulta.query.filter_by(paciente_id=paciente.id).order_by(Consulta.data.desc()).first()
    if ultima_consulta and ultima_consulta.glicemia:
        if ultima_consulta.glicemia >= 126:
            risco += 25
            fatores.append(f"Glicemia ≥126 mg/dL ({ultima_consulta.glicemia} mg/dL)")
        elif ultima_consulta.glicemia >= 100:
            risco += 15
            fatores.append(f"Glicemia ≥100 mg/dL ({ultima_consulta.glicemia} mg/dL)")
    
    # Histórico familiar (verificar doenças)
    if paciente.doencas and "diabetes" in paciente.doencas.lower():
        risco += 10
        fatores.append("Histórico familiar de diabetes")
    
    # Hipertensão (fator de risco)
    if paciente.doencas and "hipertensao" in paciente.doencas.lower():
        risco += 5
        fatores.append("Hipertensão (fator de risco)")
    
    # Limitar risco a 100%
    risco = min(risco, 100)
    
    nivel = "Baixo" if risco < 30 else "Moderado" if risco < 60 else "Alto"
    
    return {
        "risco": risco,
        "nivel": nivel,
        "fatores": fatores,
        "tipo": "Diabetes tipo 2"
    }

# ============================================
# 2. CÁLCULO DE RISCO DE HIPERTENSÃO
# ============================================

def calcular_risco_hipertensao(paciente):
    """
    Calcula o risco de hipertensão baseado em:
    - Pressão arterial (última medição)
    - Idade
    - IMC
    """
    risco = 0
    fatores = []
    
    # Idade
    if paciente.idade >= 65:
        risco += 25
        fatores.append("Idade avançada (>65 anos)")
    elif paciente.idade >= 55:
        risco += 15
        fatores.append("Idade ≥55 anos")
    
    # IMC
    if paciente.peso and paciente.altura:
        imc = paciente.peso / ((paciente.altura/100) ** 2)
        if imc >= 30:
            risco += 20
            fatores.append(f"IMC ≥30 (Obesidade: {imc:.1f})")
        elif imc >= 25:
            risco += 10
            fatores.append(f"IMC ≥25 (Sobrepeso: {imc:.1f})")
    
    # Pressão arterial (última consulta)
    ultima_consulta = Consulta.query.filter_by(paciente_id=paciente.id).order_by(Consulta.data.desc()).first()
    if ultima_consulta:
        if ultima_consulta.pressao_sistolica and ultima_consulta.pressao_diastolica:
            if ultima_consulta.pressao_sistolica >= 140 or ultima_consulta.pressao_diastolica >= 90:
                risco += 30
                fatores.append(f"Pressão elevada: {ultima_consulta.pressao_sistolica}/{ultima_consulta.pressao_diastolica} mmHg")
            elif ultima_consulta.pressao_sistolica >= 130 or ultima_consulta.pressao_diastolica >= 85:
                risco += 15
                fatores.append(f"Pressão limítrofe: {ultima_consulta.pressao_sistolica}/{ultima_consulta.pressao_diastolica} mmHg")
    
    # Diabetes (fator de risco)
    if paciente.doencas and "diabetes" in paciente.doencas.lower():
        risco += 10
        fatores.append("Diabetes (fator de risco)")
    
    risco = min(risco, 100)
    
    nivel = "Baixo" if risco < 30 else "Moderado" if risco < 60 else "Alto"
    
    return {
        "risco": risco,
        "nivel": nivel,
        "fatores": fatores,
        "tipo": "Hipertensão"
    }

# ============================================
# 3. CÁLCULO DE RISCO DE OBESIDADE
# ============================================

def calcular_risco_obesidade(paciente):
    """
    Calcula o risco de obesidade baseado em IMC
    """
    if not paciente.peso or not paciente.altura:
        return {
            "risco": 0,
            "nivel": "Indeterminado",
            "fatores": ["Peso e altura não informados"],
            "tipo": "Obesidade"
        }
    
    imc = paciente.peso / ((paciente.altura/100) ** 2)
    fatores = []
    
    if imc >= 30:
        risco = 80
        fatores.append(f"IMC atual: {imc:.1f} (Obesidade já estabelecida)")
        nivel = "Alto"
    elif imc >= 27:
        risco = 50
        fatores.append(f"IMC: {imc:.1f} (Pré-obesidade)")
        nivel = "Moderado"
    elif imc >= 25:
        risco = 30
        fatores.append(f"IMC: {imc:.1f} (Sobrepeso)")
        nivel = "Baixo"
    else:
        risco = 10
        fatores.append(f"IMC: {imc:.1f} (Peso normal)")
        nivel = "Baixo"
    
    return {
        "risco": risco,
        "nivel": nivel,
        "fatores": fatores,
        "tipo": "Obesidade",
        "imc": round(imc, 1)
    }

# ============================================
# 4. CÁLCULO DE RISCO DE ABANDONO
# ============================================

def calcular_risco_abandono(paciente):
    """
    Calcula o risco de abandono do tratamento baseado em:
    - Histórico de adesão
    - Número de consultas
    - Última consulta
    """
    risco = 0
    fatores = []
    
    consultas = Consulta.query.filter_by(paciente_id=paciente.id).order_by(Consulta.data.desc()).all()
    
    if not consultas:
        return {
            "risco": 0,
            "nivel": "Indeterminado",
            "fatores": ["Nenhuma consulta registrada"],
            "tipo": "Abandono"
        }
    
    # Última consulta
    ultima_consulta = consultas[0]
    dias_sem_consulta = (datetime.utcnow() - ultima_consulta.data).days
    
    if dias_sem_consulta > 90:
        risco += 30
        fatores.append(f"Última consulta há {dias_sem_consulta} dias")
    elif dias_sem_consulta > 60:
        risco += 20
        fatores.append(f"Última consulta há {dias_sem_consulta} dias")
    elif dias_sem_consulta > 30:
        risco += 10
        fatores.append(f"Última consulta há {dias_sem_consulta} dias")
    
    # Histórico de adesão
    adesoes = [c.adesao for c in consultas if c.adesao]
    if adesoes:
        # Contar adesões ruins
        ruins = sum(1 for a in adesoes if a in ['Baixa', 'Abandonou'])
        if ruins > 0:
            risco += ruins * 15
            fatores.append(f"{ruins} registros de baixa adesão/abandono")
        
        # Verificar se a última adesão foi ruim
        if adesoes and adesoes[0] in ['Baixa', 'Abandonou']:
            risco += 20
            fatores.append("Último registro de adesão: Baixa/Abandonou")
    
    # Número total de consultas (poucas consultas = mais risco)
    if len(consultas) < 3:
        risco += 15
        fatores.append("Poucas consultas registradas (menos de 3)")
    
    # Medicamentos prescritos (poucos medicamentos = menos engajamento)
    medicamentos = MedicamentoPrescrito.query.filter_by(paciente_id=paciente.id).all()
    if len(medicamentos) == 0:
        risco += 10
        fatores.append("Nenhum medicamento prescrito")
    
    risco = min(risco, 100)
    
    nivel = "Baixo" if risco < 30 else "Moderado" if risco < 60 else "Alto"
    
    return {
        "risco": risco,
        "nivel": nivel,
        "fatores": fatores,
        "tipo": "Abandono do tratamento",
        "dias_sem_consulta": dias_sem_consulta,
        "total_consultas": len(consultas)
    }

# ============================================
# 5. CÁLCULO DE RISCO CARDIOVASCULAR
# ============================================

def calcular_risco_cardiovascular(paciente):
    """
    Calcula o risco cardiovascular combinado
    """
    fatores = []
    risco = 0
    
    # Fatores de risco
    risco_diabetes = calcular_risco_diabetes(paciente)
    risco_hipertensao = calcular_risco_hipertensao(paciente)
    risco_obesidade = calcular_risco_obesidade(paciente)
    
    # Combinar riscos
    if risco_diabetes['risco'] > 50:
        risco += 20
        fatores.append("Alto risco de diabetes")
    
    if risco_hipertensao['risco'] > 50:
        risco += 20
        fatores.append("Alto risco de hipertensão")
    
    if risco_obesidade['risco'] > 50:
        risco += 15
        fatores.append("Alto risco de obesidade")
    
    # Idade
    if paciente.idade >= 65:
        risco += 15
        fatores.append("Idade ≥65 anos")
    elif paciente.idade >= 55:
        risco += 10
        fatores.append("Idade ≥55 anos")
    
    # Histórico
    if paciente.doencas:
        doencas_lower = paciente.doencas.lower()
        if "diabetes" in doencas_lower:
            risco += 10
            fatores.append("Diabetes (fator de risco cardiovascular)")
        if "hipertensao" in doencas_lower:
            risco += 10
            fatores.append("Hipertensão (fator de risco cardiovascular)")
        if "dislipidemia" in doencas_lower:
            risco += 10
            fatores.append("Dislipidemia (fator de risco cardiovascular)")
    
    # Fumar (simulado - poderia ser um campo no paciente)
    # Se tiver campo de tabagismo, adicionar
    
    risco = min(risco, 100)
    
    nivel = "Baixo" if risco < 30 else "Moderado" if risco < 60 else "Alto"
    
    return {
        "risco": risco,
        "nivel": nivel,
        "fatores": fatores,
        "tipo": "Cardiovascular",
        "componentes": {
            "diabetes": risco_diabetes['risco'],
            "hipertensao": risco_hipertensao['risco'],
            "obesidade": risco_obesidade['risco']
        }
    }

# ============================================
# 6. FUNÇÃO PRINCIPAL - ANÁLISE PREDITIVA COMPLETA
# ============================================

def analisar_paciente(paciente):
    """
    Realiza análise preditiva completa para um paciente
    """
    return {
        "diabetes": calcular_risco_diabetes(paciente),
        "hipertensao": calcular_risco_hipertensao(paciente),
        "obesidade": calcular_risco_obesidade(paciente),
        "abandono": calcular_risco_abandono(paciente),
        "cardiovascular": calcular_risco_cardiovascular(paciente)
    }

def analisar_todos_pacientes(usuario_id):
    """
    Analisa todos os pacientes de um usuário
    Retorna dados agregados para o dashboard preditivo
    """
    pacientes = Paciente.query.filter_by(usuario_id=usuario_id).all()
    
    resultados = []
    for p in pacientes:
        analise = analisar_paciente(p)
        # Calcular risco geral médio
        riscos = [
            analise['diabetes']['risco'],
            analise['hipertensao']['risco'],
            analise['cardiovascular']['risco']
        ]
        risco_medio = sum(riscos) / len(riscos) if riscos else 0
        
        resultados.append({
            "paciente": p,
            "analise": analise,
            "risco_medio": round(risco_medio, 1),
            "nivel_geral": "Alto" if risco_medio > 60 else "Moderado" if risco_medio > 30 else "Baixo"
        })
    
    # Estatísticas
    total_pacientes = len(resultados)
    alto_risco = sum(1 for r in resultados if r['nivel_geral'] == 'Alto')
    moderado_risco = sum(1 for r in resultados if r['nivel_geral'] == 'Moderado')
    baixo_risco = sum(1 for r in resultados if r['nivel_geral'] == 'Baixo')
    
    # Pacientes com maior risco
    pacientes_prioritarios = sorted(resultados, key=lambda x: x['risco_medio'], reverse=True)[:5]
    
    return {
        "total_pacientes": total_pacientes,
        "alto_risco": alto_risco,
        "moderado_risco": moderado_risco,
        "baixo_risco": baixo_risco,
        "pacientes_prioritarios": pacientes_prioritarios,
        "todos_resultados": resultados
    }

def obter_recomendacoes(analise):
    """
    Gera recomendações baseadas na análise preditiva
    """
    recomendacoes = []
    
    # Diabetes
    if analise['diabetes']['risco'] > 50:
        recomendacoes.append("🔬 Realizar teste de glicemia em jejum")
        recomendacoes.append("🍎 Orientar dieta com baixo índice glicêmico")
        if analise['diabetes']['risco'] > 70:
            recomendacoes.append("🩺 Encaminhar para endocrinologista")
    
    # Hipertensão
    if analise['hipertensao']['risco'] > 50:
        recomendacoes.append("🩸 Monitorar pressão arterial diariamente")
        recomendacoes.append("🧂 Orientar redução de sódio na dieta")
        if analise['hipertensao']['risco'] > 70:
            recomendacoes.append("🩺 Encaminhar para cardiologista")
    
    # Obesidade
    if analise['obesidade']['risco'] > 50:
        recomendacoes.append("⚖️ Orientar perda de peso")
        recomendacoes.append("🏃‍♂️ Incentivar atividade física regular")
    
    # Abandono
    if analise['abandono']['risco'] > 50:
        recomendacoes.append("📞 Reforçar contato com o paciente")
        recomendacoes.append("📝 Simplificar o esquema de medicação")
        if analise['abandono']['risco'] > 70:
            recomendacoes.append("🤝 Agendar consulta de acompanhamento em 15 dias")
    
    # Cardiovascular
    if analise['cardiovascular']['risco'] > 50:
        recomendacoes.append("❤️ Avaliar necessidade de AAS ou estatinas")
        recomendacoes.append("🩺 Solicitar perfil lipídico completo")
    
    return recomendacoes[:5]  # Limitar a 5 recomendações