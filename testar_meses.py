from app import app, db
from dashboard_api import get_dashboard_data

with app.app_context():
    dados = get_dashboard_data()
    print("Meses:", dados['meses'])
    print("Consultas por mês:", dados['consultas_por_mes'])