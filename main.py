import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾")

# 2. Configuração de Acesso ao Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s/edit"
        planilha = client.open_by_url(URL_PLANILHA)
        return planilha.sheet1
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# 3. Interface do Usuário
st.title("🐾 Guardião Pet SP")
st.subheader("Cadastro de Pets - Projeto PetHub")

sheet = conectar_google_sheets()

if sheet:
    with st.form("form_pet"):
        nome_pet = st.text_input("Nome do Pet")
        especie = st.selectbox("Espécie", ["Cão", "Gato", "Outro"])
        raca = st.text_input("Raça")
        idade = st.number_input("Idade Aproximada", min_value=0, max_value=30)
        
        # --- NOVO CAMPO TELEFONE ---
        telefone = st.text_input("Telefone de Contato (com DDD)", placeholder="(11) 9XXXX-XXXX")
        
        enviado = st.form_submit_button("Cadastrar Pet")
        
        if enviado:
            if nome_pet and telefone:
                # IMPORTANTE: 
                # Coluna A: Nome | B: Espécie | C: Raça | D: Idade
                # Coluna E: Vacinas (deixamos vazio "" para não sobrescrever)
                # Coluna F: Telefone
                vacinas_placeholder = "-" 
                
                nova_linha = [nome_pet, especie, raca, idade, vacinas_placeholder, telefone]
                
                sheet.append_row(nova_linha)
                st.success(f"O pet {nome_pet} foi cadastrado com sucesso! Telefone salvo na coluna F.")
            else:
                st.warning("Por favor, preencha o nome do pet e o telefone.")

    # --- QR CODE INTEGRADO NO FINAL ---
    st.markdown("---")
    st.write("### 📲 Compartilhe este formulário")
    url_app = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_app}"
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(qr_url, caption="Aponte a câmera")
    with col2:
        st.info("Este QR Code leva diretamente para esta página de cadastro de pets.")