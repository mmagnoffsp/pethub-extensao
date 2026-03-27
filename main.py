import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾")

# 2. Configuração de Acesso ao Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    try:
        # Busca as credenciais configuradas no Streamlit Secrets
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
        st.write("### 📝 Informações do Pet")
        col1, col2 = st.columns(2)
        
        with col1:
            nome_pet = st.text_input("Nome do Pet")
            especie = st.selectbox("Espécie", ["Cão", "Gato", "Outro"])
        
        with col2:
            raca = st.text_input("Raça")
            idade = st.number_input("Idade Aproximada", min_value=0, max_value=30)

        # --- NOVO CAMPO DE SAÚDE / VACINAS ---
        st.write("### 🏥 Saúde e Vacinação")
        opcoes_vacinas = [
            "V8 / V10 (Cães)", 
            "Antirrábica", 
            "Gripe Canina", 
            "Giárdia", 
            "V3 / V4 / V5 (Gatos)", 
            "Vermifugado", 
            "Castrado",
            "Microchipado"
        ]
        selecao_vacinas = st.multiselect("Selecione as vacinas/procedimentos realizados:", opcoes_vacinas)
        outras_infos_saude = st.text_input("Outras observações de saúde (ex: alergias, remédios)", placeholder="Opcional")

        # --- CAMPO TELEFONE DO TUTOR ---
        st.write("### 📞 Contato")
        telefone = st.text_input("Seu WhatsApp (apenas números com DDD)", placeholder="119XXXXXXXX")
        
        enviado = st.form_submit_button("Finalizar Cadastro")
        
        if enviado:
            if nome_pet and telefone:
                # 1. Organiza os dados de saúde para a planilha
                # Junta as vacinas selecionadas e as observações extras em um único texto
                lista_saude = selecao_vacinas.copy()
                if outras_infos_saude:
                    lista_saude.append(f"Obs: {outras_infos_saude}")
                
                saude_final = ", ".join(lista_saude) if lista_saude else "Nenhuma informação fornecida"

                # 2. Limpa o telefone para o link do WhatsApp
                tel_limpo = "".join(filter(str.isdigit, telefone))
                
                # 3. URL do seu projeto online e Mensagem
                url_projeto = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
                mensagem_tutor = (
                    f"Olá! Tenho interesse em saber mais sobre o pet *{nome_pet}* "
                    f"que vi no Guardião Pet SP.\n\n"
                    f"Status de Saúde: {saude_final}\n"
                    f"Link do anúncio: {url_projeto}"
                )
                
                mensagem_url = urllib.parse.quote(mensagem_tutor)
                link_whatsapp = f"https://wa.me/55{tel_limpo}?text={mensagem_url}"
                
                # 4. Dados para a Planilha (Ordem das colunas)
                nova_linha = [
                    nome_pet, 
                    especie, 
                    raca, 
                    idade, 
                    saude_final,  # Coluna de Saúde atualizada
                    telefone, 
                    link_whatsapp
                ]
                
                # Envia para o Google Sheets
                try:
                    sheet.append_row(nova_linha)
                    st.success(f"O pet {nome_pet} foi cadastrado com sucesso!")
                    
                    st.markdown("---")
                    st.write("### 📲 Próximo Passo:")
                    st.info("Clique no botão abaixo para testar como o adotante entrará em contato com você:")
                    st.link_button(f"Simular conversa sobre {nome_pet}", link_whatsapp)
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
                
            else:
                st.warning("Por favor, preencha o nome do pet e o seu telefone de contato.")

    # --- QR CODE DE COMPARTILHAMENTO ---
    st.markdown("---")
    st.write("### 🔗 Compartilhe o Guardião Pet SP")
    url_app = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_app}"
    
    col_qr1, col_qr2 = st.columns([1, 2])
    with col_qr1:
        st.image(qr_url, caption="Escaneie para acessar")
    with col_qr2:
        st.write("Use este QR Code para divulgar o sistema de cadastro.")

else:
    st.warning("Aguardando conexão com o Google Sheets... Verifique suas credenciais.")