import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse  # Essencial para formatar o link do WhatsApp

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾")

# 2. Configuração de Acesso ao Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    try:
        # Busca as credenciais configuradas no Streamlit Secrets (secrets.toml)
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # URL da sua planilha específica
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
        
        # --- CAMPO TELEFONE DO TUTOR ---
        telefone = st.text_input("Seu WhatsApp (apenas números com DDD)", placeholder="119XXXXXXXX")
        
        enviado = st.form_submit_button("Finalizar Cadastro")
        
        if enviado:
            if nome_pet and telefone:
                # 1. Limpa o telefone para garantir que o link funcione (remove () - e espaços)
                tel_limpo = "".join(filter(str.isdigit, telefone))
                
                # 2. URL do seu projeto online
                url_projeto = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
                
                # 3. Montagem da Mensagem que o Tutor vai receber
                # Inclui o nome do pet e o link do site no corpo do texto
                mensagem_tutor = (
                    f"Olá! Tenho interesse em saber mais sobre o pet *{nome_pet}* "
                    f"que vi no Guardião Pet SP.\n\n"
                    f"Link do anúncio: {url_projeto}"
                )
                
                # Codifica o texto para formato de URL (troca espaços por %20, etc)
                mensagem_url = urllib.parse.quote(mensagem_tutor)
                
                # 4. Link Final do WhatsApp (Adiciona o 55 do Brasil automaticamente)
                link_whatsapp = f"https://wa.me/55{tel_limpo}?text={mensagem_url}"
                
                # 5. Dados para a Planilha
                vacinas_placeholder = "-" 
                nova_linha = [nome_pet, especie, raca, idade, vacinas_placeholder, telefone, link_whatsapp]
                
                # Envia para o Google Sheets
                sheet.append_row(nova_linha)
                
                # --- EXIBIÇÃO DE SUCESSO ---
                st.success(f"O pet {nome_pet} foi cadastrado com sucesso na planilha!")
                
                st.markdown("---")
                st.write("### 📲 Próximo Passo:")
                st.info("Clique no botão abaixo para testar o envio da mensagem ao tutor:")
                
                # Botão que abre o WhatsApp com a mensagem e o link inclusos
                st.link_button(f"Enviar interesse por {nome_pet} via WhatsApp", link_whatsapp)
                
            else:
                st.warning("Por favor, preencha o nome do pet e o seu telefone de contato.")

    # --- QR CODE DE COMPARTILHAMENTO NO FINAL ---
    st.markdown("---")
    st.write("### 🔗 Compartilhe o Guardião Pet SP")
    url_app = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_app}"
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(qr_url, caption="Escaneie para acessar")
    with col2:
        st.write("Use este QR Code para que outras pessoas possam cadastrar pets no seu sistema.")