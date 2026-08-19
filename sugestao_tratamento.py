# ============================================
# SUGESTÃO DE TRATAMENTO BASEADA EM DADOS REAIS
# ============================================

from models import Paciente, Consulta, MedicamentoPrescrito
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import json

# ============================================
# 1. ENCONTRAR PACIENTES SIMILARES
# ============================================

def encontrar_pacientes_similares(paciente, limite=10):
    """
    Encontra pacientes com perfil semelhante ao paciente atual
    """
    similaridade = []
    
    # Buscar todos os pacientes (exceto o atual)
    todos_pacientes = Paciente.query.filter(Paciente.id != paciente.id).all()
    
    for p in todos_pacientes:
        score = calcular_similaridade(paciente, p)
        if score > 0:
            similaridade.append({
                "paciente": p,
                "score": score
            })
    
    # Ordenar por similaridade
    similaridade.sort(key=lambda x: x['score'], reverse=True)
    
    return similaridade[:limite]

def calcular_similaridade(paciente1, paciente2):
    """
    Calcula o grau de similaridade entre dois pacientes
    Retorna uma pontuação de 0 a 100
    """
    score = 0
    total_pesos = 0
    
    # 1. Idade (peso: 20%)
    if paciente1.idade and paciente2.idade:
        diferenca_idade = abs(paciente1.idade - paciente2.idade)
        if diferenca_idade <= 5:
            score += 20
        elif diferenca_idade <= 10:
            score += 15
        elif diferenca_idade <= 20:
            score += 10
        elif diferenca_idade <= 30:
            score += 5
        total_pesos += 20
    
    # 2. Doenças (peso: 30%)
    if paciente1.doencas and paciente2.doencas:
        doencas1 = set([d.strip().lower() for d in paciente1.doencas.split(',') if d.strip()])
        doencas2 = set([d.strip().lower() for d in paciente2.doencas.split(',') if d.strip()])
        
        if doencas1 and doencas2:
            interseccao = len(doencas1.intersection(doencas2))
            uniao = len(doencas1.union(doencas2))
            if uniao > 0:
                score += (interseccao / uniao) * 30
        total_pesos += 30
    
    # 3. IMC (peso: 15%)
    if paciente1.peso and paciente1.altura and paciente2.peso and paciente2.altura:
        imc1 = paciente1.peso / ((paciente1.altura/100) ** 2)
        imc2 = paciente2.peso / ((paciente2.altura/100) ** 2)
        diferenca_imc = abs(imc1 - imc2)
        if diferenca_imc <= 2:
            score += 15
        elif diferenca_imc <= 5:
            score += 10
        elif diferenca_imc <= 8:
            score += 5
        total_pesos += 15
    
    # 4. Sexo (peso: 10%) - se tiver campo
    # 5. Medicamentos em uso (peso: 25%)
    if paciente1.medicamentos_atuais and paciente2.medicamentos_atuais:
        meds1 = set([m.strip().lower() for m in paciente1.medicamentos_atuais.split(',') if m.strip()])
        meds2 = set([m.strip().lower() for m in paciente2.medicamentos_atuais.split(',') if m.strip()])
        
        if meds1 and meds2:
            interseccao = len(meds1.intersection(meds2))
            uniao = len(meds1.union(meds2))
            if uniao > 0:
                score += (interseccao / uniao) * 25
        total_pesos += 25
    
    # Normalizar para 100
    if total_pesos > 0:
        score = (score / total_pesos) * 100
    
    return round(score, 1)

# ============================================
# 2. ANALISAR TRATAMENTOS DE PACIENTES SIMILARES
# ============================================

def analisar_tratamentos_similares(paciente):
    """
    Analisa os tratamentos de pacientes similares
    Retorna sugestões de medicamentos com base em dados reais
    """
    pacientes_similares = encontrar_pacientes_similares(paciente)
    
    if not pacientes_similares:
        return {
            "tem_dados": False,
            "mensagem": "Nenhum paciente similar encontrado para comparação."
        }
    
    # Coletar medicamentos prescritos para pacientes similares
    medicamentos_contagem = {}
    medicamentos_detalhes = {}
    
    for item in pacientes_similares:
        p = item['paciente']
        consultas = Consulta.query.filter_by(paciente_id=p.id).all()
        
        for consulta in consultas:
            if consulta.medicamentos_receitados:
                for linha in consulta.medicamentos_receitados.split('\n'):
                    linha = linha.strip()
                    if linha and len(linha) > 3:
                        # Extrair nome e posologia
                        partes = linha.split('-')
                        nome = partes[0].strip() if partes else linha
                        posologia = partes[1].strip() if len(partes) > 1 else ''
                        
                        if nome:
                            medicamentos_contagem[nome] = medicamentos_contagem.get(nome, 0) + 1
                            if nome not in medicamentos_detalhes:
                                medicamentos_detalhes[nome] = {
                                    'posologias': [],
                                    'pacientes': [],
                                    'consultas': []
                                }
                            if posologia:
                                medicamentos_detalhes[nome]['posologias'].append(posologia)
                            if p.id not in medicamentos_detalhes[nome]['pacientes']:
                                medicamentos_detalhes[nome]['pacientes'].append(p.id)
                            if consulta.id not in medicamentos_detalhes[nome]['consultas']:
                                medicamentos_detalhes[nome]['consultas'].append(consulta.id)
    
    # Ordenar por frequência
    medicamentos_ordenados = sorted(medicamentos_contagem.items(), key=lambda x: x[1], reverse=True)
    
    # Montar sugestões
    sugestoes = []
    for nome, count in medicamentos_ordenados[:10]:
        detalhes = medicamentos_detalhes.get(nome, {})
        
        # Posologia mais comum
        posologias = detalhes.get('posologias', [])
        posologia_comum = max(set(posologias), key=posologias.count) if posologias else ''
        
        # Calcular eficácia baseada em aprovações
        consultas_ids = detalhes.get('consultas', [])
        total_aprovadas = 0
        for cid in consultas_ids:
            consulta = Consulta.query.get(cid)
            if consulta and consulta.status == 'Aprovado':
                total_aprovadas += 1
        
        taxa_aprovacao = round((total_aprovadas / len(consultas_ids)) * 100) if consultas_ids else 0
        
        sugestoes.append({
            'medicamento': nome,
            'frequencia': count,
            'pacientes': len(detalhes.get('pacientes', [])),
            'posologia_comum': posologia_comum,
            'taxa_aprovacao': taxa_aprovacao,
            'consultas': len(consultas_ids)
        })
    
    return {
        "tem_dados": True,
        "pacientes_similares": len(pacientes_similares),
        "sugestoes": sugestoes,
        "melhor_score": pacientes_similares[0]['score'] if pacientes_similares else 0
    }

# ============================================
# 3. GERAR RELATÓRIO DE SUGESTÃO
# ============================================

def gerar_relatorio_sugestao(paciente):
    """
    Gera um relatório completo de sugestão de tratamento
    """
    analise = analisar_tratamentos_similares(paciente)
    
    if not analise['tem_dados']:
        return {
            "paciente": paciente.nome,
            "tem_dados": False,
            "mensagem": "Sem dados suficientes para gerar sugestões."
        }
    
    # Buscar medicamentos que o paciente já usa (para não sugerir duplicatas)
    medicamentos_atuais = set()
    if paciente.medicamentos_atuais:
        for m in paciente.medicamentos_atuais.split(','):
            nome = m.strip().split()[0].capitalize() if m.strip() else ''
            if nome:
                medicamentos_atuais.add(nome)
    
    # Filtrar medicamentos que o paciente já usa
    sugestoes_filtradas = []
    for s in analise['sugestoes']:
        if s['medicamento'] not in medicamentos_atuais:
            sugestoes_filtradas.append(s)
    
    return {
        "paciente": paciente.nome,
        "tem_dados": True,
        "pacientes_similares": analise['pacientes_similares'],
        "melhor_score": analise['melhor_score'],
        "sugestoes": sugestoes_filtradas[:5],
        "medicamentos_atuais": list(medicamentos_atuais)
    }