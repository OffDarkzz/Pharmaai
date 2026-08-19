import os

# Carrega variáveis de um arquivo .env, se existir (só pra uso local -
# no Render as variáveis já vêm do painel, então isso não faz nada lá).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================

# --- APIs Públicas (gratuitas) ---

# GSRS (Global Substance Registration System) - FDA/NIH
GSRS_URL = "https://gsrs.ncats.nih.gov/api/v1/substances"
# A GSRS é pública e não requer chave para consultas básicas

# openFDA - FDA (EUA)
OPENFDA_URL = "https://api.fda.gov/drug"
OPENFDA_API_KEY = os.environ.get("OPENFDA_API_KEY", "")  # Opcional: cadastre-se em https://api.data.gov/signup/ para limites maiores

# Health Canada Drug Product Database
HC_URL = "https://api.canada.ca/health-products/drug-product-database"

# ANVISA (Brasil) - API pública
ANVISA_URL = "https://api-medicamentos-anvisa.vercel.app"

# --- APIs Comerciais (opcionais) ---

# DrugBank - Requer cadastro (https://www.drugbank.com/register)
DRUGBANK_URL = "https://api.drugbank.com/v1"
DRUGBANK_API_KEY = os.environ.get("DRUGBANK_API_KEY", "")  # Preencher se tiver

# ============================================
# BANCO DE DADOS
# ============================================

# Em produção, defina DATABASE_URL apontando pro Postgres (ex: o Postgres
# gratuito do Render). Sem essa variável, cai no SQLite local - ótimo pra
# dev, mas no Render free o disco é apagado a cada redeploy ou quando o
# serviço "dorme" por inatividade, então os dados não persistem.
_database_url = os.environ.get("DATABASE_URL", "sqlite:///pharmaai.db")
if _database_url.startswith("postgres://"):
    # SQLAlchemy 1.4+ exige "postgresql://"; o Render (como o Heroku antes
    # dele) às vezes fornece a URL com o prefixo antigo "postgres://"
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = _database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-troque-em-producao")

# ============================================
# OUTRAS CONFIGURAÇÕES
# ============================================

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
PORT = int(os.environ.get("PORT", 5000))
HOST = "0.0.0.0"
