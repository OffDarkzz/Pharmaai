from app import app, db
from models import Paciente, Consulta, Usuario

with app.app_context():
    print("="*60)
    print("USUÁRIOS CADASTRADOS:")
    for u in Usuario.query.all():
        print(f"  ID: {u.id} - {u.nome} - {u.email}")
    
    print("\nPACIENTES CADASTRADOS:")
    for p in Paciente.query.all():
        print(f"  ID: {p.id} - {p.nome} - Usuario ID: {p.usuario_id}")
    
    print("\nCONSULTAS:")
    for c in Consulta.query.all():
        print(f"  ID: {c.id} - Paciente ID: {c.paciente_id} - Status: {c.status}")
    print("="*60)