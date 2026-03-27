import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾")

# 2. Configuração de Acesso ao Google Sheets
# O escopo define o que o "robô" pode fazer (ler e escrever)
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    try:
        # Puxa as credenciais das Secrets (Configuradas no site do Streamlit)
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # URL da sua planilha (ajustada para o formato de abertura)
        URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s/edit"
        
        # Abre a planilha pela URL e seleciona a primeira aba
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
        
        enviado = st.form_submit_button("Cadastrar Pet")
        
        if enviado:
            if nome_pet:
                # Adiciona os dados na próxima linha disponível da planilha
                nova_linha = [nome_pet, especie, raca, idade]
                sheet.append_row(nova_linha)
                st.success(f"O pet {nome_pet} foi cadastrado com sucesso!")
            else:
                st.warning("Por favor, preencha o nome do pet.")

---

### Próximos passos para colocar no ar:

1.  **Salvar e Enviar:** * No VS Code, salve o arquivo.
    * No terminal, digite:
      `git add .`
      `git commit -m "Fix: Conexão via URL e interface limpa"`
      `git push origin main`

2.  **Verificar a Planilha (Crucial!):**
    * Abra sua planilha no navegador.
    * Clique em **Compartilhar**.
    * Verifique se o e-mail `pethub-operator@pethub-extensao2026.iam.gserviceaccount.com` está lá como **Editor**. Se não estiver, o código dará erro de "Permission Denied".

3.  **Aguardar o Deploy:**
    * O site [https://guardiao-pet-sp-mmagnoff.streamlit.app](https://guardiao-pet-sp-mmagnoff.streamlit.app) vai atualizar sozinho em cerca de 30 segundos após o seu `git push`.

**Quer que eu fique de olho no link para ver se o formulário aparece ou prefere que eu já prepare o QR Code oficial?**