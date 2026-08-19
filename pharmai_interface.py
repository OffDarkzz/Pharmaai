import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="PharmAI - Análise de Dados", layout="wide")

st.title("🩺 PharmAI - Módulo de Análise")

@st.cache_data
def carregar_csv():
    return pd.read_csv('cid10.csv')

try:
    df = carregar_csv()
    st.success(f"✅ {len(df)} registros da CID-10 carregados com sucesso!")
    
    st.subheader("📊 Visualização dos Dados")
    st.dataframe(df.head(20))

    # Aqui você pode adicionar qualquer filtro, gráfico ou análise de IA que quiser
    # no futuro.

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.info("Certifique-se de que o arquivo 'cid10.csv' está na raiz do projeto.")
