import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# 1. Configurações Iniciais da Página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾", layout="centered")

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
        st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return None

# 3. Interface do Usuário
st.title("🐾 Guardião Pet SP")
st.subheader("Sistema de Cadastro de Pets - Projeto PetHub")
st.markdown("---")

sheet = conectar_google_sheets()

if sheet:
    with st.form("form_pet", clear_on_submit=True):
        st.write("### 📝 1. Informações do Pet")
        col1, col2 = st.columns(2)
        
        with col1:
            nome_pet = st.text_input("Nome do Animal", placeholder="Ex: Thor, Mel...")
            especie = st.selectbox("Espécie", ["Cão", "Gato", "Outro"])
        
        with col2:
            raca = st.text_input("Raça", placeholder="Ex: SRD, Poodle...")
            idade = st.number_input("Idade Aproximada (anos)", min_value=0, max_value=30, step=1)

        st.write("---")
        st.write("### 🏥 2. Saúde e Vacinação")
        
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
        
        selecao_vacinas = st.multiselect("Marque os procedimentos realizados:", opcoes_vacinas)
        outras_infos_saude = st.text_input("Outras observações médicas", placeholder="Ex: Alergias, deficiências ou medicamentos")

        st.write("---")
        st.write("### 📞 3. Contato do Responsável")
        telefone = st.text_input("Seu WhatsApp (DDD + Número)", placeholder="Ex: 11988887777")
        
        st.write("")
        enviado = st.form_submit_button("✅ FINALIZAR E SALVAR CADASTRO")
        
        if enviado:
            if nome_pet and telefone:
                # Processamento de dados de saúde
                lista_saude = selecao_vacinas.copy()
                if outras_infos_saude:
                    lista_saude.append(f"Obs: {outras_infos_saude}")
                
                saude_final = ", ".join(lista_saude) if lista_saude else "Nenhuma informação fornecida"

                # Limpeza de telefone e geração de link
                tel_limpo = "".join(filter(str.isdigit, telefone))
                url_projeto = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
                
                mensagem_tutor = (
                    f"Olá! Tenho interesse em saber mais sobre o pet *{nome_pet}* "
                    f"cadastrado no Guardião Pet SP.\n\n"
                    f"Saúde: {saude_final}\n"
                    f"Link do Projeto: {url_projeto}"
                )
                
                mensagem_url = urllib.parse.quote(mensagem_tutor)
                link_whatsapp = f"https://wa.me/55{tel_limpo}?text={mensagem_url}"
                
                # Dados para a Planilha
                nova_linha = [nome_pet, especie, raca, idade, saude_final, telefone, link_whatsapp]
                
                try:
                    sheet.append_row(nova_linha)
                    st.success(f"🎉 Sucesso! {nome_pet} foi registrado na base de dados.")
                    st.info("💡 Teste o botão de contato que o adotante usará:")
                    st.link_button(f"Abrir conversa via WhatsApp", link_whatsapp)
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("⚠️ Atenção: Campos 'Nome do Pet' e 'WhatsApp' são obrigatórios.")

    # --- RODAPÉ INSTITUCIONAL E ACADÊMICO (EXTENSÃO) ---
    st.write("")
    st.write("")
    st.markdown("---")
    
    st.markdown("### 🏛️ Detalhes do Projeto de Extensão")
    
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        st.markdown(f"""
        **Instituição:** Universidade Anhembi Morumbi  
        **Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas  
        **Semestre:** 2º Semestre / 2026  
        **Desenvolvedor:** Carlos Magno
        """)

    with col_u2:
        st.markdown("""
        **Impacto Social e ODS (ONU):** ✅ **ODS 11:** Cidades e Comunidades Sustentáveis  
        ✅ **ODS 15:** Vida Terrestre (Proteção Animal)
        """)

    # QR Code e Divulgação
    st.markdown("---")
    url_publica = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
    qr_code_api = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url_publica}"
    
    col_qr, col_txt = st.columns([1, 3])
    with col_qr:
        st.image(qr_code_api, caption="QR Code do Sistema")
    with col_txt:
        st.write("### 🔗 Divulgação do Território")
        st.write("Utilize o QR Code ao lado para que protetores e ONGs da região possam cadastrar animais para adoção. O sistema centraliza os dados e automatiza o contato via WhatsApp.")

else:
    st.warning("⚠️ Sistema offline: Verifique a conexão com a API do Google Sheets nos Secrets.")