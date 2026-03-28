import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import time

# 1. Configurações Iniciais da Página (Heurística #8: Estética e Minimalismo)
st.set_page_config(
    page_title="Guardião Pet SP", 
    page_icon="🐾", 
    layout="centered"
)

# Estilização CSS para melhorar a experiência do usuário
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #2E7D32;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração de Acesso ao Google Sheets (Heurística #1: Status do Sistema)
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def conectar_google_sheets():
    try:
        # Busca as credenciais configuradas no Streamlit Secrets
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=scope
        )
        client = gspread.authorize(creds)
        
        # URL da planilha oficial do projeto PetHub
        URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s/edit"
        planilha = client.open_by_url(URL_PLANILHA)
        return planilha.sheet1
    except Exception as e:
        st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return None

# 3. Interface do Usuário - Cabeçalho Institucional
st.title("🐾 Guardião Pet SP")
st.subheader("Sistema de Cadastro de Pets - Projeto PetHub")
st.markdown("---")

# Heurística #10: Ajuda e Documentação (Breve instrução inicial)
st.info("Bem-vindo! Este sistema integra protetores e ONGs à rede de adoção de São Paulo. Preencha os campos abaixo para registrar um animal.")

sheet = conectar_google_sheets()

if sheet:
    # Heurística #5: Prevenção de Erros (Uso do formulário para evitar envios acidentais)
    with st.form("form_pet", clear_on_submit=True):
        st.write("### 📝 1. Informações Básicas do Pet")
        col1, col2 = st.columns(2)
        
        with col1:
            nome_pet = st.text_input("Nome do Animal*", placeholder="Ex: Thor, Mel...", help="Campo obrigatório")
            
            # Heurística #6: Reconhecimento em vez de Memorização (Lista ampla de espécies)
            opcoes_especies = [
                "Cão", "Gato", "Ave (Calopsita, Papagaio, etc.)", 
                "Roedor (Hamster, Coelho, etc.)", "Réptil (Tartaruga, Lagarto)", 
                "Equino (Cavalo)", "Suíno (Mini Porco)", "Peixe", "Outro"
            ]
            escolha_especie = st.selectbox("Espécie*", opcoes_especies)
            
            # Campo condicional para espécie (Flexibilidade e Eficiência - Heurística #7)
            if escolha_especie == "Outro":
                especie_final = st.text_input("Especifique a espécie:", placeholder="Ex: Furão, Cabra...")
            else:
                especie_final = escolha_especie
        
        with col2:
            raca = st.text_input("Raça", placeholder="Ex: SRD, Poodle, Siames...", help="Se desconhecida, use SRD")
            idade = st.number_input("Idade Aproximada (anos)", min_value=0, max_value=50, step=1)

        st.write("---")
        st.write("### 🏥 2. Saúde, Vacinação e Bem-estar")
        
        # Lógica de Vacinas Adaptável (Heurística #2: Correspondência com o Mundo Real)
        if escolha_especie == "Cão":
            opcoes_vacinas = ["V8 / V10", "Antirrábica", "Gripe Canina", "Giárdia", "Vermifugado", "Castrado", "Microchipado"]
        elif escolha_especie == "Gato":
            opcoes_vacinas = ["V3 / V4 / V5", "Antirrábica", "Vermifugado", "Castrado", "Microchipado"]
        else:
            opcoes_vacinas = ["Vacinação em dia", "Vermifugado", "Castrado", "Microchipado", "Avaliado por Veterinário"]
        
        selecao_vacinas = st.multiselect("Marque os procedimentos realizados:", opcoes_vacinas)
        outras_infos_saude = st.text_area("Outras observações médicas", placeholder="Ex: Alergias, deficiências ou medicamentos em uso...", height=100)

        st.write("---")
        st.write("### 📞 3. Contato e Perfil do Responsável")
        
        perfil_responsavel = st.selectbox(
            "Você está cadastrando como:",
            [
                "Protetor / Tutor Individual", 
                "ONG (Organização Não Governamental)", 
                "Pet Parceira em Feiras e Eventos"
            ]
        )
        
        telefone = st.text_input("Seu WhatsApp (DDD + Número)*", placeholder="Ex: 11988887777", help="Apenas números com DDD")
        
        st.write("")
        # Heurística #4: Consistência e Padrões
        enviado = st.form_submit_button("✅ FINALIZAR E SALVAR CADASTRO")
        
        if enviado:
            if nome_pet and telefone:
                # Heurística #1: Fornecer feedback de processamento
                with st.spinner("Processando cadastro e salvando na nuvem..."):
                    # Processamento de dados de saúde
                    lista_saude = selecao_vacinas.copy()
                    if outras_infos_saude:
                        lista_saude.append(f"Obs: {outras_infos_saude}")
                    
                    saude_final = ", ".join(lista_saude) if lista_saude else "Nenhuma informação fornecida"

                    # Automação de Link de WhatsApp
                    tel_limpo = "".join(filter(str.isdigit, telefone))
                    url_projeto = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
                    
                    tipo_msg = "da sua ONG" if "ONG" in perfil_responsavel else "da feira/evento" if "Feiras" in perfil_responsavel else "seu pet"
                    
                    mensagem_tutor = (
                        f"Olá! Tenho interesse em saber mais sobre o pet *{nome_pet}* ({especie_final}) {tipo_msg} "
                        f"cadastrado no Guardião Pet SP.\n\n"
                        f"Saúde: {saude_final}\n"
                        f"Link do Projeto: {url_projeto}"
                    )
                    
                    mensagem_url = urllib.parse.quote(mensagem_tutor)
                    link_whatsapp = f"https://wa.me/55{tel_limpo}?text={mensagem_url}"
                    
                    # 4. Dados para a Planilha (Heurística #1: Status)
                    nova_linha = [nome_pet, especie_final, idade, raca, saude_final, telefone, perfil_responsavel, link_whatsapp]
                    
                    try:
                        sheet.append_row(nova_linha)
                        st.balloons() # Feedback visual de sucesso
                        st.success(f"🎉 Sucesso! {nome_pet} foi registrado na base de dados com segurança.")
                        
                        st.info(f"💡 Link de contato direto gerado para o perfil: {perfil_responsavel}")
                        st.link_button(f"Abrir WhatsApp de {nome_pet}", link_whatsapp)
                        
                    except Exception as e:
                        # Heurística #9: Ajudar usuários a reconhecer erros
                        st.error(f"Erro ao salvar na planilha: {e}")
            else:
                # Heurística #9: Mensagem de erro clara
                st.warning("⚠️ Atenção: Os campos 'Nome do Pet' e 'WhatsApp' são fundamentais para o cadastro.")

    # --- RODAPÉ INSTITUCIONAL, ACADÊMICO E ODS ---
    st.write("")
    st.markdown("---")
    st.markdown("### 🏛️ Detalhes do Projeto de Extensão")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown(f"""
        **Instituição:** Universidade Anhembi Morumbi  
        **Curso:** Tecnologia em ADS | 2º Semestre / 2026  
        **Desenvolvedor:** Carlos Magno
        """)
    with col_u2:
        st.markdown("""
        **Impacto Social e ODS (ONU):** ✅ **ODS 11:** Cidades e Comunidades Sustentáveis  
        ✅ **ODS 15:** Vida Terrestre (Proteção e Bem-Estar Animal)
        """)

    st.markdown("---")
    # Gerador de QR Code dinâmico para divulgação (Heurística #7: Atalhos)
    url_publica = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
    qr_code_api = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url_publica}"
    
    col_qr, col_txt = st.columns([1, 3])
    with col_qr:
        st.image(qr_code_api, caption="Divulgue o App")
    with col_txt:
        st.write("### 🔗 Divulgação do Território")
        st.write("Utilize o QR Code acima em feiras de adoção e clínicas parceiras da Penha e região para que mais animais sejam cadastrados.")

else:
    # Heurística #9: Diagnóstico de erro crítico
    st.error("⚠️ Sistema Offline: Não foi possível conectar ao Banco de Dados. Verifique as credenciais GCP.")