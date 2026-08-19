from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================
# MODELO: USUARIO (para autenticação)
# ============================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    pacientes = db.relationship('Paciente', backref='usuario', lazy=True, foreign_keys='Paciente.usuario_id')
    pacientes_transferidos = db.relationship('Paciente', backref='transferido', lazy=True, foreign_keys='Paciente.transferido_para')

    def set_senha(self, senha):
        from werkzeug.security import generate_password_hash
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha_hash, senha)

# ============================================
# MODELO: PACIENTE
# ============================================

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    transferido_para = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)
    alergias = db.Column(db.Text)
    doencas = db.Column(db.Text)
    medicamentos_atuais = db.Column(db.Text)
    
    consultas = db.relationship('Consulta', backref='paciente', lazy=True)

# ============================================
# MODELO: CONSULTA
# ============================================

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    
    queixa = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    
    pressao_sistolica = db.Column(db.Integer)
    pressao_diastolica = db.Column(db.Integer)
    temperatura = db.Column(db.Float)
    frequencia_cardiaca = db.Column(db.Integer)
    frequencia_respiratoria = db.Column(db.Integer)
    glicemia = db.Column(db.Integer)
    saturacao_o2 = db.Column(db.Integer)
    imc = db.Column(db.Float)
    
    medicamentos_sugeridos = db.Column(db.Text)
    medicamentos_receitados = db.Column(db.Text)
    parecer_farmaceutico = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendente')
    observacoes = db.Column(db.Text)
    analise_completa = db.Column(db.Text)
    dose_calculada = db.Column(db.Text)
    adesao = db.Column(db.String(20))  # Boa, Parcial, Baixa, Abandonou
motivo_nao_adesao = db.Column(db.Text)

# ============================================
# MODELO: MEDICAMENTO PRESCRITO (Histórico do Paciente)
# ============================================

class MedicamentoPrescrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consulta.id'), nullable=True)
    nome = db.Column(db.String(200), nullable=False)
    posologia = db.Column(db.Text)
    duracao = db.Column(db.String(100))
    data_prescricao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Ativo')  # Ativo, Concluído, Descontinuado
    
    paciente = db.relationship('Paciente', backref='medicamentos_prescritos')
    consulta = db.relationship('Consulta', backref='medicamentos_prescritos')

# ============================================
# MODELO: MEDICAMENTO (para busca local)
# ============================================

class Medicamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    principio_ativo = db.Column(db.String(200), index=True)
    laboratorio = db.Column(db.String(200))
    registro = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    indicacao = db.Column(db.Text)
    contraindicacao = db.Column(db.Text)
    efeitos_colaterais = db.Column(db.Text)
    posologia = db.Column(db.Text)
    interacoes = db.Column(db.Text)
    classificacao = db.Column(db.String(100))
    fonte = db.Column(db.String(100))
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)