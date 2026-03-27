import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA CONEXÃO (Substitua o bloco antigo por este) ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    # Tenta ler as chaves que você já salvou no site do Streamlit (Secrets)
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha (Certifique-se que o nome está 100% igual ao Google Sheets)
    nome_da_planilha = "PetHub - Banco de Dados" 
    planilha = client.open(nome_da_planilha).sheet1
    
except Exception as e:
    st.error(f"Erro ao conectar com o Google Sheets: {e}")

# --- INTERFACE DO SEU APP ---
st.title("Guardião Pet SP 🐾")

# Aqui você continua com o restante do seu código (st.text_input, st.selectbox, etc.)
# Exemplo rápido:
nome_pet = st.text_input("Nome do Pet")
tipo_pet = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])

if st.button("Cadastrar Pet"):
    if nome_pet:
        try:
            planilha.append_row(["27/03/2026", nome_pet, tipo_pet, "Vira-lata", "Carlos"])
            st.success(f"✅ O pet '{nome_pet}' foi cadastrado com sucesso!")
        except:
            st.error("Erro ao salvar na planilha. Verifique as permissões.")
    else:
        st.warning("Por favor, digite o nome do pet.")