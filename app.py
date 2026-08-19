from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, jsonify, session, flash
from models import db, Paciente, Consulta, Medicamento, Usuario, MedicamentoPrescrito
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, DEBUG, HOST, PORT
from medicamentos_api import analisar_queixa, buscar_medicamento_anvisa
from dashboard_api import get_dashboard_data, analisar_tendencias
from dose_api import calcular_dose, calcular_dose_para_paciente
from interacoes_api import verificar_interacoes_prescricao, verificar_interacoes
from analise_preditiva import analisar_todos_pacientes, analisar_paciente
from sugestao_tratamento import gerar_relatorio_sugestao
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import streamlit as st
import pandas as pd

# --- COLOQUE ISSO LOGO NO COMEÇO DO CÓDIGO ---
st.set_page_config(page_title="PharmAI", layout="wide")

# Crie uma função para carregar os dados e coloque o @st.cache_data nela
@st.cache_data
def carregar_dados():
    # Aqui vai o seu código que lê o CSV
    df = pd.read_csv('cid10.csv') # ou o nome do seu arquivo
    return df

# Agora chame a função. O Streamlit vai carregar UMA VEZ e guardar na memória.
df = carregar_dados()

# Depois disso, você pode escrever na tela
st.title("Sistema PharmAI")
st.write(f"Carregados {len(df)} registros da CID-10")
# ============================================
# INICIALIZAÇÃO DO APP
# ============================================

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
db.init_app(app)

with app.app_context():
    db.create_all()

# ============================================
# DECORATOR PARA EXIGIR LOGIN
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ROTA PARA ARQUIVOS ESTÁTICOS
# ============================================

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# ============================================
# FUNÇÃO PARA CALCULAR IMC
# ============================================

def calcular_imc(peso, altura):
    if peso and altura and altura > 0:
        altura_metros = altura / 100
        return round(peso / (altura_metros ** 2), 1)
    return None

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('cadastro'))
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('cadastro'))
        
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(nome=nome, email=email)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# ============================================
# ROTAS PRINCIPAIS
# ============================================

@app.route('/')
@login_required
def index():
    pacientes = Paciente.query.filter_by(usuario_id=session['usuario_id']).all()
    total_pacientes = len(pacientes)
    
    consultas = Consulta.query.join(Paciente).filter(Paciente.usuario_id == session['usuario_id']).all()
    total_consultas = len(consultas)
    consultas_pendentes = len([c for c in consultas if c.status == 'Pendente'])
    consultas_aprovadas = len([c for c in consultas if c.status == 'Aprovado'])
    
    return render_template(
        'index.html',
        pacientes=pacientes,
        total_pacientes=total_pacientes,
        total_consultas=total_consultas,
        consultas_pendentes=consultas_pendentes,
        consultas_aprovadas=consultas_aprovadas
    )

@app.route('/anamnese', methods=['GET', 'POST'])
@login_required
def anamnese():
    if request.method == 'POST':
        paciente = Paciente(
            usuario_id=session['usuario_id'],
            nome=request.form['nome'],
            idade=int(request.form['idade']),
            peso=float(request.form['peso']) if request.form['peso'] else None,
            altura=float(request.form['altura']) if request.form['altura'] else None,
            alergias=request.form['alergias'],
            doencas=request.form['doencas'],
            medicamentos_atuais=request.form['medicamentos_atuais']
        )
        db.session.add(paciente)
        db.session.commit()

        pressao_sistolica = request.form.get('pressao_sistolica')
        pressao_diastolica = request.form.get('pressao_diastolica')
        temperatura = request.form.get('temperatura')
        frequencia_cardiaca = request.form.get('frequencia_cardiaca')
        frequencia_respiratoria = request.form.get('frequencia_respiratoria')
        glicemia = request.form.get('glicemia')
        saturacao_o2 = request.form.get('saturacao_o2')
        imc = calcular_imc(paciente.peso, paciente.altura)

        analise = analisar_queixa(
            queixa=request.form['queixa'],
            idade=paciente.idade,
            doencas=paciente.doencas or '',
            alergias=paciente.alergias or '',
            medicamentos_atuais=paciente.medicamentos_atuais or ''
        )

        consulta = Consulta(
            paciente_id=paciente.id,
            data=datetime.utcnow(),
            queixa=request.form['queixa'],
            diagnostico=request.form['diagnostico'],
            observacoes=request.form['observacoes'],
            pressao_sistolica=int(pressao_sistolica) if pressao_sistolica else None,
            pressao_diastolica=int(pressao_diastolica) if pressao_diastolica else None,
            temperatura=float(temperatura) if temperatura else None,
            frequencia_cardiaca=int(frequencia_cardiaca) if frequencia_cardiaca else None,
            frequencia_respiratoria=int(frequencia_respiratoria) if frequencia_respiratoria else None,
            glicemia=int(glicemia) if glicemia else None,
            saturacao_o2=int(saturacao_o2) if saturacao_o2 else None,
            imc=imc,
            medicamentos_sugeridos=json.dumps(analise, ensure_ascii=False),
            analise_completa=json.dumps(analise, ensure_ascii=False),
            status='Pendente'
        )
        db.session.add(consulta)
        db.session.commit()

        return redirect(url_for('resultado', paciente_id=paciente.id))

    return render_template('anamnese.html')

@app.route('/resultado/<int:paciente_id>')
@login_required
def resultado(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).first()
    sugestoes = None
    if consulta and consulta.medicamentos_sugeridos:
        try:
            sugestoes = json.loads(consulta.medicamentos_sugeridos)
        except:
            sugestoes = None
    return render_template('resultado.html', paciente=paciente, consulta=consulta, sugestoes=sugestoes)

@app.route('/editar/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def editar(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).first()

    if request.method == 'POST':
        paciente.nome = request.form['nome']
        paciente.idade = int(request.form['idade'])
        paciente.peso = float(request.form['peso']) if request.form['peso'] else None
        paciente.altura = float(request.form['altura']) if request.form['altura'] else None
        paciente.alergias = request.form['alergias']
        paciente.doencas = request.form['doencas']
        paciente.medicamentos_atuais = request.form['medicamentos_atuais']

        if consulta:
            consulta.queixa = request.form['queixa']
            consulta.diagnostico = request.form['diagnostico']
            consulta.observacoes = request.form['observacoes']
            consulta.pressao_sistolica = int(request.form['pressao_sistolica']) if request.form['pressao_sistolica'] else None
            consulta.pressao_diastolica = int(request.form['pressao_diastolica']) if request.form['pressao_diastolica'] else None
            consulta.temperatura = float(request.form['temperatura']) if request.form['temperatura'] else None
            consulta.frequencia_cardiaca = int(request.form['frequencia_cardiaca']) if request.form['frequencia_cardiaca'] else None
            consulta.frequencia_respiratoria = int(request.form['frequencia_respiratoria']) if request.form['frequencia_respiratoria'] else None
            consulta.glicemia = int(request.form['glicemia']) if request.form['glicemia'] else None
            consulta.saturacao_o2 = int(request.form['saturacao_o2']) if request.form['saturacao_o2'] else None
            consulta.imc = calcular_imc(paciente.peso, paciente.altura)

            analise = analisar_queixa(
                queixa=consulta.queixa,
                idade=paciente.idade,
                doencas=paciente.doencas or '',
                alergias=paciente.alergias or '',
                medicamentos_atuais=paciente.medicamentos_atuais or ''
            )
            consulta.medicamentos_sugeridos = json.dumps(analise, ensure_ascii=False)
            consulta.analise_completa = json.dumps(analise, ensure_ascii=False)
            consulta.medicamentos_receitados = ''
            consulta.parecer_farmaceutico = ''
            consulta.adesao = ''
            consulta.motivo_nao_adesao = ''
            consulta.status = 'Pendente'

        db.session.commit()
        return redirect(url_for('resultado', paciente_id=paciente.id))

    return render_template('editar.html', paciente=paciente, consulta=consulta)

@app.route('/aprovar/<int:consulta_id>', methods=['POST'])
@login_required
def aprovar(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    paciente = Paciente.query.filter_by(id=consulta.paciente_id, usuario_id=session['usuario_id']).first_or_404()
    
    medicamentos_receitados = request.form.get('medicamentos_receitados', '')
    consulta.medicamentos_receitados = medicamentos_receitados
    consulta.parecer_farmaceutico = request.form.get('parecer_farmaceutico', '')
    consulta.status = request.form.get('status', 'Aprovado')
    
    consulta.adesao = request.form.get('adesao')
    consulta.motivo_nao_adesao = request.form.get('motivo_nao_adesao', '')
    
    interacoes = verificar_interacoes_prescricao(
        medicamentos_receitados, 
        paciente.medicamentos_atuais or ''
    )
    
    if interacoes:
        consulta.observacoes = (consulta.observacoes or '') + '\n\n⚠️ INTERAÇÕES DETECTADAS:\n' + '\n'.join([
            f"• {i['medicamento1']} + {i['medicamento2']}: {i['descricao']} - {i['recomendacao']}"
            for i in interacoes
        ])
    
    if medicamentos_receitados:
        for linha in medicamentos_receitados.split('\n'):
            linha = linha.strip()
            if linha and len(linha) > 3:
                medicamento = MedicamentoPrescrito(
                    paciente_id=paciente.id,
                    consulta_id=consulta.id,
                    nome=linha[:200],
                    posologia=linha,
                    duracao='Conforme prescrição',
                    status='Ativo'
                )
                db.session.add(medicamento)
    
    db.session.commit()
    
    if interacoes:
        gravidade_grave = any(i['nivel'] == 'Grave' for i in interacoes)
        if gravidade_grave:
            flash('⚠️ ATENÇÃO: Interações GRAVES detectadas! Verifique as observações da consulta.', 'danger')
        else:
            flash('🟡 Atenção: Interações medicamentosas detectadas. Verifique as observações.', 'warning')
    
    return redirect(url_for('resultado', paciente_id=consulta.paciente_id))

@app.route('/historico/<int:paciente_id>')
@login_required
def historico(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consultas = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).all()
    return render_template('historico.html', paciente=paciente, consultas=consultas)

@app.route('/prontuario/<int:paciente_id>')
@login_required
def prontuario(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consultas = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).all()
    medicamentos = MedicamentoPrescrito.query.filter_by(paciente_id=paciente_id).order_by(MedicamentoPrescrito.data_prescricao.desc()).all()
    total_consultas = len(consultas)
    total_medicamentos = len(medicamentos)
    
    return render_template('prontuario.html', 
        paciente=paciente, 
        consultas=consultas, 
        medicamentos=medicamentos,
        total_consultas=total_consultas,
        total_medicamentos=total_medicamentos
    )

@app.route('/imc_evolucao/<int:paciente_id>')
@login_required
def imc_evolucao(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consultas = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.asc()).all()
    
    datas = []
    imcs = []
    pesos = []
    
    for c in consultas:
        if c.imc and c.data:
            datas.append(c.data.strftime('%d/%m/%Y'))
            imcs.append(c.imc)
            if c.paciente and c.paciente.peso:
                pesos.append(c.paciente.peso)
            else:
                pesos.append(None)
    
    return render_template('imc_evolucao.html', 
        paciente=paciente, 
        datas=datas, 
        imcs=imcs,
        pesos=pesos,
        total_consultas=len(consultas)
    )

@app.route('/deletar/<int:paciente_id>', methods=['POST'])
@login_required
def deletar(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    Consulta.query.filter_by(paciente_id=paciente_id).delete()
    MedicamentoPrescrito.query.filter_by(paciente_id=paciente_id).delete()
    db.session.delete(paciente)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/buscar_medicamento', methods=['GET', 'POST'])
@login_required
def buscar_medicamento():
    resultado = None
    if request.method == 'POST':
        termo = request.form.get('nome_medicamento')
        if termo:
            dados = buscar_medicamento_anvisa(termo)
            if dados and not isinstance(dados, dict) and dados:
                resultado = {'dados': dados, 'termo': termo, 'fonte': 'ANVISA'}
            elif isinstance(dados, dict) and dados.get('erro'):
                resultado = {'erro': dados.get('erro'), 'termo': termo}
            else:
                resultado = {'erro': f'Medicamento "{termo}" não encontrado.', 'termo': termo}
    return render_template('buscar_medicamentos.html', resultado=resultado)

@app.route('/pdf/<int:paciente_id>')
@login_required
def gerar_pdf(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).first()
    if not consulta:
        return "Nenhuma consulta encontrada", 404

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1a5276'), alignment=1, spaceAfter=30)
    story.append(Paragraph("PharmaAI - Relatório de Atendimento", titulo_style))

    story.append(Paragraph("<b>DADOS DO PACIENTE</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Nome:</b> {paciente.nome}", styles['Normal']))
    story.append(Paragraph(f"<b>Idade:</b> {paciente.idade} anos", styles['Normal']))
    story.append(Paragraph(f"<b>Peso:</b> {paciente.peso or 'Não informado'} kg", styles['Normal']))
    story.append(Paragraph(f"<b>Altura:</b> {paciente.altura or 'Não informado'} cm", styles['Normal']))
    story.append(Paragraph(f"<b>Alergias:</b> {paciente.alergias or 'Nenhuma'}", styles['Normal']))
    story.append(Paragraph(f"<b>Doenças:</b> {paciente.doencas or 'Nenhuma'}", styles['Normal']))
    story.append(Paragraph(f"<b>Medicamentos em uso:</b> {paciente.medicamentos_atuais or 'Nenhum'}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>SINAIS VITAIS E EXAMES</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Pressão Arterial:</b> {consulta.pressao_sistolica or 'N/I'}/{consulta.pressao_diastolica or 'N/I'} mmHg", styles['Normal']))
    story.append(Paragraph(f"<b>Temperatura:</b> {consulta.temperatura or 'N/I'} °C", styles['Normal']))
    story.append(Paragraph(f"<b>Frequência Cardíaca:</b> {consulta.frequencia_cardiaca or 'N/I'} bpm", styles['Normal']))
    story.append(Paragraph(f"<b>Frequência Respiratória:</b> {consulta.frequencia_respiratoria or 'N/I'} irpm", styles['Normal']))
    story.append(Paragraph(f"<b>Glicemia:</b> {consulta.glicemia or 'N/I'} mg/dL", styles['Normal']))
    story.append(Paragraph(f"<b>Saturação O₂:</b> {consulta.saturacao_o2 or 'N/I'} %", styles['Normal']))
    if consulta.imc:
        story.append(Paragraph(f"<b>IMC:</b> {consulta.imc} kg/m²", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>QUEIXA E DIAGNÓSTICO</b>", styles['Heading2']))
    story.append(Paragraph(f"<b>Queixa:</b> {consulta.queixa}", styles['Normal']))
    story.append(Paragraph(f"<b>Diagnóstico:</b> {consulta.diagnostico or 'Não informado'}", styles['Normal']))
    story.append(Paragraph(f"<b>Data:</b> {consulta.data.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    if consulta.medicamentos_sugeridos:
        try:
            sugestoes = json.loads(consulta.medicamentos_sugeridos)
            story.append(Paragraph("<b>SUGESTÕES DO SISTEMA</b>", styles['Heading2']))
            if sugestoes.get('sugestoes'):
                for s in sugestoes['sugestoes'][:5]:
                    story.append(Paragraph(f"• {s['medicamento']} - {s['principio_ativo']} - {s['posologia']} ({s['seguranca']['nivel']})", styles['Normal']))
                    if s.get('fonte'):
                        story.append(Paragraph(f"  Fonte: {s['fonte']}", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        except:
            pass

    if consulta.medicamentos_receitados:
        story.append(Paragraph("<b>PRESCRIÇÃO APROVADA</b>", styles['Heading2']))
        story.append(Paragraph(consulta.medicamentos_receitados.replace('\n', '<br/>'), styles['Normal']))
        if consulta.parecer_farmaceutico:
            story.append(Paragraph("<b>Parecer:</b>", styles['Normal']))
            story.append(Paragraph(consulta.parecer_farmaceutico, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    
    if consulta.adesao:
        story.append(Paragraph("<b>ADESÃO AO TRATAMENTO</b>", styles['Heading2']))
        adesao_texto = consulta.adesao
        if consulta.motivo_nao_adesao:
            adesao_texto += f" - Motivo: {consulta.motivo_nao_adesao}"
        story.append(Paragraph(f"<b>Status:</b> {adesao_texto}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"<b>Status da Consulta:</b> {consulta.status}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    footer_style = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1)
    story.append(Paragraph("Documento gerado pelo PharmaAI - Sistema de apoio à decisão clínica", footer_style))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"pharmaai_{paciente.nome}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

@app.route('/dashboard')
@login_required
def dashboard():
    dados = get_dashboard_data(session['usuario_id'])
    return render_template('dashboard.html', dados=dados)

@app.route('/analise_tendencias')
@login_required
def analise_tendencias():
    dados = analisar_tendencias(session['usuario_id'])
    return render_template('analise_tendencias.html', dados=dados)

@app.route('/analise_preditiva')
@login_required
def analise_preditiva():
    dados = analisar_todos_pacientes(session['usuario_id'])
    return render_template('analise_preditiva.html', dados=dados)

@app.route('/sugestao_tratamento/<int:paciente_id>')
@login_required
def sugestao_tratamento(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    relatorio = gerar_relatorio_sugestao(paciente)
    return render_template('sugestao_tratamento.html', paciente=paciente, relatorio=relatorio)

@app.route('/calcular_dose/<int:paciente_id>')
@login_required
def calcular_dose_paciente(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    
    consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.data.desc()).first()
    medicamentos = []
    
    if consulta and consulta.medicamentos_receitados:
        for linha in consulta.medicamentos_receitados.split('\n'):
            linha = linha.strip()
            if linha and len(linha) > 3:
                nome = linha.split('-')[0].strip()
                if nome:
                    medicamentos.append(nome)
    
    if not medicamentos:
        medicamentos = ['Paracetamol', 'Ibuprofeno']
    
    resultados = calcular_dose_para_paciente(paciente, medicamentos)
    
    return render_template('dose_calculada.html', 
        paciente=paciente, 
        resultados=resultados,
        consulta=consulta
    )

@app.route('/verificar_interacoes', methods=['GET', 'POST'])
@login_required
def verificar_interacoes_view():
    resultado = None
    if request.method == 'POST':
        medicamentos_input = request.form.get('medicamentos', '')
        medicamentos = [m.strip() for m in medicamentos_input.split(',') if m.strip()]
        if medicamentos:
            resultado = verificar_interacoes(medicamentos)
    return render_template('verificar_interacoes.html', resultado=resultado)

# ============================================
# ROTAS DE TRANSFERÊNCIA
# ============================================

@app.route('/buscar_usuarios', methods=['GET'])
@login_required
def buscar_usuarios():
    termo = request.args.get('q', '')
    if len(termo) < 2:
        return jsonify({'usuarios': []})
    
    usuarios = Usuario.query.filter(
        Usuario.id != session['usuario_id'],
        (Usuario.nome.ilike(f'%{termo}%') | Usuario.email.ilike(f'%{termo}%'))
    ).limit(10).all()
    
    resultado = [
        {'id': u.id, 'nome': u.nome, 'email': u.email}
        for u in usuarios
    ]
    return jsonify({'usuarios': resultado})

@app.route('/transferir/<int:paciente_id>', methods=['POST'])
@login_required
def transferir_paciente(paciente_id):
    paciente = Paciente.query.filter_by(id=paciente_id, usuario_id=session['usuario_id']).first_or_404()
    
    usuario_destino_id = request.form.get('usuario_destino_id')
    if not usuario_destino_id:
        flash('Selecione um usuário para transferir.', 'danger')
        return redirect(url_for('resultado', paciente_id=paciente_id))
    
    usuario_destino = Usuario.query.get(usuario_destino_id)
    if not usuario_destino:
        flash('Usuário destino não encontrado.', 'danger')
        return redirect(url_for('resultado', paciente_id=paciente_id))
    
    if usuario_destino_id == session['usuario_id']:
        flash('Não é possível transferir para você mesmo.', 'danger')
        return redirect(url_for('resultado', paciente_id=paciente_id))
    
    paciente.usuario_id = int(usuario_destino_id)
    db.session.commit()
    
    flash(f'Paciente {paciente.nome} transferido para {usuario_destino.nome}!', 'success')
    return redirect(url_for('index'))

# ============================================
# RODAR O APP
# ============================================

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
