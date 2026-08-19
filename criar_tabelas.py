from app import app, db
from sqlalchemy import inspect

print("🔄 Criando tabelas...")

with app.app_context():
    db.create_all()
    print("✅ Tabelas criadas com sucesso!")

    # Verificar as tabelas
    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()
    print(f"📋 Tabelas criadas: {tabelas}")

    # Verificar colunas da tabela consulta
    if 'consulta' in tabelas:
        colunas = [col['name'] for col in inspector.get_columns('consulta')]
        print("\n📋 Colunas da tabela 'consulta':")
        for col in colunas:
            print(f"  - {col}")

print("🏁 Pronto!")