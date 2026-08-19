from app import app, db
from sqlalchemy import inspect
import os

print("🔄 Criando banco de dados...")

# Deletar banco se existir
if os.path.exists('pharmaai.db'):
    os.remove('pharmaai.db')
    print("🗑️ Banco antigo removido.")

with app.app_context():
    db.create_all()
    print("✅ Banco criado com sucesso!")

    # Verificar tabelas
    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()
    print(f"📋 Tabelas criadas: {tabelas}")

    # Verificar colunas da tabela 'paciente'
    if 'paciente' in tabelas:
        colunas = [col['name'] for col in inspector.get_columns('paciente')]
        print("\n📋 Colunas da tabela 'paciente':")
        for col in colunas:
            print(f"  - {col}")

    # Verificar colunas da tabela 'usuario'
    if 'usuario' in tabelas:
        colunas = [col['name'] for col in inspector.get_columns('usuario')]
        print("\n📋 Colunas da tabela 'usuario':")
        for col in colunas:
            print(f"  - {col}")

print("🏁 Pronto!")