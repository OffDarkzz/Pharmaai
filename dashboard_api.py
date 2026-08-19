from models import Paciente, Consulta
from datetime import datetime, timedelta
import json

def get_dashboard_data(usuario_id):
    """Retorna todos os dados necessários para o dashboard (filtrado por usuário)"""
    
    # ===== 1. Totais =====
    total_pacientes = Paciente.query.filter_by(usuario_id=usuario_id).count()
    pacientes = Paciente.query.filter_by(usuario_id=usuario_id).all()
    consultas = Consulta.query.join(Paciente).filter(Paciente.usuario_id == usuario_id).all()
    total_consultas = len(consultas)
    consultas_pendentes = len([c for c in consultas if c.status == 'Pendente'])
    consultas_aprovadas = len([c for c in consultas if c.status == 'Aprovado'])

    # ===== 2. Distribuição por idade =====
    faixas_etarias = {'0-18': 0, '19-40': 0, '41-65': 0, '65+': 0}
    soma_idades = 0
    for p in pacientes:
        soma_idades += p.idade
        if p.idade <= 18:
            faixas_etarias['0-18'] += 1
        elif p.idade <= 40:
            faixas_etarias['19-40'] += 1
        elif p.idade <= 65:
            faixas_etarias['41-65'] += 1
        else:
            faixas_etarias['65+'] += 1
    media_idade = round(soma_idades / total_pacientes, 1) if total_pacientes else 0

    # ===== 3. Medicamentos mais sugeridos =====
    med_count = {}
    for c in consultas:
        if c.medicamentos_sugeridos:
            try:
                dados = json.loads(c.medicamentos_sugeridos)
                for s in dados.get('sugestoes', []):
                    nome = s.get('medicamento', 'Desconhecido')
                    med_count[nome] = med_count.get(nome, 0) + 1
            except:
                pass
    top_medicamentos = sorted(med_count.items(), key=lambda x: x[1], reverse=True)[:10]

    # ===== 4. CIDs mais frequentes =====
    cid_count = {}
    for c in consultas:
        if c.analise_completa:
            try:
                dados = json.loads(c.analise_completa)
                for cid_item in dados.get('diagnostico', {}).get('cids', []):
                    cid = cid_item.get('cid', 'R69')
                    cid_count[cid] = cid_count.get(cid, 0) + 1
            except:
                pass
    top_cids = sorted(cid_count.items(), key=lambda x: x[1], reverse=True)[:10]

    # ===== 5. Status das consultas =====
    status_contagem = {
        'Pendente': consultas_pendentes,
        'Analisado': len([c for c in consultas if c.status == 'Analisado']),
        'Aprovado': consultas_aprovadas
    }

    # ===== 6. Consultas por mês (últimos 6 meses) =====
    meses = []
    consultas_por_mes = []
    for i in range(5, -1, -1):
        mes = datetime.now().replace(day=1) - timedelta(days=30*i)
        meses.append(mes.strftime('%b/%Y'))
        inicio_mes = mes.replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            fim_mes = datetime.now()
        else:
            prox_mes = mes.replace(day=28) + timedelta(days=4)
            fim_mes = prox_mes - timedelta(days=prox_mes.day)
        count = len([c for c in consultas if c.data >= inicio_mes and c.data <= fim_mes])
        consultas_por_mes.append(count)

    return {
        'total_pacientes': total_pacientes,
        'total_consultas': total_consultas,
        'consultas_pendentes': consultas_pendentes,
        'consultas_aprovadas': consultas_aprovadas,
        'faixas_etarias': faixas_etarias,
        'top_medicamentos': top_medicamentos,
        'top_cids': top_cids,
        'status_contagem': status_contagem,
        'media_idade': media_idade,
        'meses': meses,
        'consultas_por_mes': consultas_por_mes
    }

# ============================================
# ANÁLISE DE TENDÊNCIAS
# ============================================

def analisar_tendencias(usuario_id):
    """
    Analisa tendências nos atendimentos do usuário
    Retorna insights e dados para gráficos
    """
    pacientes = Paciente.query.filter_by(usuario_id=usuario_id).all()
    consultas = Consulta.query.join(Paciente).filter(Paciente.usuario_id == usuario_id).all()
    
    if not consultas:
        return {
            'tem_dados': False,
            'mensagem': 'Nenhuma consulta registrada para análise.'
        }
    
    # ===== 1. Medicamentos mais prescritos =====
    medicamentos_contagem = {}
    for c in consultas:
        if c.medicamentos_receitados:
            for linha in c.medicamentos_receitados.split('\n'):
                linha = linha.strip()
                if linha and len(linha) > 3:
                    nome = linha.split('-')[0].strip()
                    if nome:
                        medicamentos_contagem[nome] = medicamentos_contagem.get(nome, 0) + 1
    
    top_medicamentos = sorted(medicamentos_contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # ===== 2. Doenças mais frequentes =====
    doencas_contagem = {}
    for p in pacientes:
        if p.doencas:
            for doenca in p.doencas.split(','):
                doenca = doenca.strip().lower()
                if doenca:
                    doencas_contagem[doenca] = doencas_contagem.get(doenca, 0) + 1
    
    top_doencas = sorted(doencas_contagem.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # ===== 3. Faixa etária mais atendida =====
    faixas = {'0-18': 0, '19-40': 0, '41-65': 0, '65+': 0}
    for p in pacientes:
        if p.idade <= 18:
            faixas['0-18'] += 1
        elif p.idade <= 40:
            faixas['19-40'] += 1
        elif p.idade <= 65:
            faixas['41-65'] += 1
        else:
            faixas['65+'] += 1
    
    # ===== 4. Adesão ao tratamento =====
    adesao_contagem = {'Boa': 0, 'Parcial': 0, 'Baixa': 0, 'Abandonou': 0}
    for c in consultas:
        if c.adesao:
            adesao_contagem[c.adesao] = adesao_contagem.get(c.adesao, 0) + 1
    
    # ===== 5. Status das consultas =====
    status_contagem = {'Pendente': 0, 'Analisado': 0, 'Aprovado': 0}
    for c in consultas:
        if c.status:
            status_contagem[c.status] = status_contagem.get(c.status, 0) + 1
    
    # ===== 6. Evolução mensal =====
    from datetime import datetime, timedelta
    meses = []
    consultas_por_mes = []
    for i in range(11, -1, -1):
        mes = datetime.now().replace(day=1) - timedelta(days=30*i)
        meses.append(mes.strftime('%b/%Y'))
        inicio_mes = mes.replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            fim_mes = datetime.now()
        else:
            prox_mes = mes.replace(day=28) + timedelta(days=4)
            fim_mes = prox_mes - timedelta(days=prox_mes.day)
        count = len([c for c in consultas if c.data >= inicio_mes and c.data <= fim_mes])
        consultas_por_mes.append(count)
    
    # ===== 7. Insights =====
    insights = []
    
    # Insight: Medicamento mais prescrito
    if top_medicamentos:
        med, count = top_medicamentos[0]
        insights.append(f"💊 O medicamento mais prescrito é **{med}** com {count} prescrições.")
    
    # Insight: Doença mais comum
    if top_doencas:
        doenca, count = top_doencas[0]
        insights.append(f"🩺 A doença mais comum é **{doenca}** com {count} pacientes.")
    
    # Insight: Faixa etária predominante
    faixa_mais_comum = max(faixas, key=faixas.get)
    if faixas[faixa_mais_comum] > 0:
        nomes_faixas = {'0-18': 'crianças/adolescentes', '19-40': 'adultos jovens', '41-65': 'adultos maduros', '65+': 'idosos'}
        insights.append(f"👤 A faixa etária mais atendida é de **{nomes_faixas[faixa_mais_comum]}** ({faixa_mais_comum} anos).")
    
    # Insight: Adesão
    total_adesao = sum(adesao_contagem.values())
    if total_adesao > 0:
        boa_adesao = adesao_contagem.get('Boa', 0)
        if boa_adesao / total_adesao > 0.7:
            insights.append(f"✅ {round(boa_adesao/total_adesao*100)}% dos pacientes têm **boa adesão** ao tratamento.")
        elif boa_adesao / total_adesao < 0.3:
            insights.append(f"⚠️ Apenas {round(boa_adesao/total_adesao*100)}% dos pacientes têm boa adesão. **Atenção necessária**.")
    
    # Insight: Consultas pendentes
    pendentes = status_contagem.get('Pendente', 0)
    if pendentes > 5:
        insights.append(f"⏳ **{pendentes} consultas pendentes** de aprovação. Recomenda-se revisá-las.")
    
    # Insight: Tendência de crescimento
    if len(consultas_por_mes) >= 6:
        ultimos_3 = sum(consultas_por_mes[-3:])
        anteriores_3 = sum(consultas_por_mes[-6:-3])
        if anteriores_3 > 0 and ultimos_3 > anteriores_3:
            crescimento = round((ultimos_3 - anteriores_3) / anteriores_3 * 100)
            insights.append(f"📈 Crescimento de **{crescimento}%** nos atendimentos nos últimos 3 meses.")
        elif anteriores_3 > 0 and ultimos_3 < anteriores_3:
            queda = round((anteriores_3 - ultimos_3) / anteriores_3 * 100)
            insights.append(f"📉 Queda de **{queda}%** nos atendimentos nos últimos 3 meses.")
    
    # Insight: Interações medicamentosas frequentes
    interacoes_contagem = {}
    for c in consultas:
        if c.observacoes and 'INTERAÇÕES DETECTADAS' in c.observacoes:
            interacoes_contagem['Com interação'] = interacoes_contagem.get('Com interação', 0) + 1
    
    if interacoes_contagem.get('Com interação', 0) > 0:
        insights.append(f"⚠️ **{interacoes_contagem['Com interação']} consultas** com interações medicamentosas detectadas.")
    
    return {
        'tem_dados': True,
        'total_pacientes': len(pacientes),
        'total_consultas': len(consultas),
        'top_medicamentos': top_medicamentos,
        'top_doencas': top_doencas,
        'faixas_etarias': faixas,
        'adesao_contagem': adesao_contagem,
        'status_contagem': status_contagem,
        'meses': meses,
        'consultas_por_mes': consultas_por_mes,
        'insights': insights
    }