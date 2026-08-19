from app import app, db
from dashboard_api import get_dashboard_data

with app.app_context():
    dados = get_dashboard_data()
    print("Total pacientes:", dados.get('total_pacientes', 0))
    print("Total consultas:", dados.get('total_consultas', 0))
    print("Pendentes:", dados.get('consultas_pendentes', 0))
    print("Aprovados:", dados.get('consultas_aprovadas', 0))