import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# ==============================================================================
# 1. CONFIGURAÇÕES GLOBAIS (ADS 2026 - ANHEMBI MORUMBI)
# ==============================================================================
st.set_page_config(
    page_title="Guardião Pet SP - ADS 2026", 
    page_icon="🐾", 
    layout="centered"
)

# Estilização CSS personalizada (IHC - Foco em Usabilidade e Acessibilidade)
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #2E7D32 !important; color: white !important; 
        font-weight: bold; font-size: 18px !important; 
    }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { 
        font-size: 20px !important; font-weight: 600 !important; 
        padding: 10px 5px !important; color: #1B5E20 !important; 
    }
    .ods-tag {
        display: inline-block; padding: 3px 10px; border-radius: 5px;
        color: white; font-size: 11px; font-weight: bold; margin-right: 5px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #2E7D32; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS (GOOGLE SHEETS API)
# ==============================================================================
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def conectar_google_sheets():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # ID da sua planilha original do projeto
        ID_PLANILHA = "1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s"
        return client.open_by_key(ID_PLANILHA).get_worksheet(0) 
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

sheet = conectar_google_sheets()

# ==============================================================================
# 3. INTERFACE LATERAL (IDENTIDADE E QR CODE)
# ==============================================================================
url_app = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url_app}"
st.sidebar.image(qr_code, caption="Acesso Mobile - PetHub")

aba_selecionada = st.sidebar.radio(
    "Menu de Navegação:", 
    ["📝 Cadastrar Novo Pet", "📊 Consultar Base de Dados"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.write("**Status:** 🟢 Sistema Online")
st.sidebar.write("**Versão:** ADS.2026.V5_GLOBAL")
st.sidebar.write("**Localização:** São Paulo - SP")
st.sidebar.write("**Desenvolvedor:** Carlos Magno")
st.sidebar.write("**Instituição:** Anhembi Morumbi")

# ==============================================================================
# 4. CABEÇALHO E ALINHAMENTO AGENDA 2030 (REQUISITO TRILHA)
# ==============================================================================
st.title("🐾 Guardião Pet SP")
st.subheader("Sistema PetHub - Solução Digital para Proteção Animal")

with st.expander("🌍 Conexão com os Objetivos de Desenvolvimento Sustentável (ODS)"):
    st.markdown("""
    Este projeto de extensão universitária foi desenvolvido para mitigar problemas reais em São Paulo - SP:
    - **ODS 3 (Saúde e Bem-Estar):** Auxilia no controle sanitário urbano e prevenção de zoonoses.
    - **ODS 11 (Cidades e Comunidades Sustentáveis):** Fortalece a rede de apoio e proteção animal urbana.
    - **ODS 15 (Vida Terrestre):** Promove o respeito à vida e o combate ao abandono de espécies domésticas.
    """)

# ==============================================================================
# 5. MÓDULO DE CADASTRO (CREATE)
# ==============================================================================
if aba_selecionada == "📝 Cadastrar Novo Pet":
    st.markdown("---")
    if sheet:
        with st.form("form_registro_pet", clear_on_submit=True):
            st.write("### 📝 1. Identificação do Pet")
            col_1, col_2 = st.columns(2)
            with col_1:
                nome_pet = st.text_input("Nome do Pet*", placeholder="Ex: Bob")
                especie = st.selectbox("Espécie*", ["Cão", "Gato", "Ave", "Outro"])
            with col_2:
                raca = st.text_input("Raça", placeholder="Ex: SRD ou Específica")
                idade = st.number_input("Idade Estimada", 0, 30, 0)
            
            st.write("---")
            st.write("### 📞 2. Saúde e Contato")
            saude_pet = st.text_input("Status de Saúde", placeholder="Vacinado, Castrado, etc.")
            whatsapp = st.text_input("WhatsApp (DDD + Número)*", placeholder="11900000000")
            
            st.write("")
            if st.form_submit_button("✅ SALVAR REGISTRO"):
                if nome_pet and whatsapp:
                    with st.spinner("Enviando dados para São Paulo - SP..."):
                        num_limpo = "".join(filter(str.isdigit, whatsapp))
                        link_whatsapp = f"https://wa.me/55{num_limpo}?text=Olá! Vi o pet {nome_pet} no Guardião Pet SP."
                        try:
                            sheet.append_row([nome_pet, especie, idade, raca, saude_pet, whatsapp, link_whatsapp])
                            st.balloons()
                            st.success(f"Pet {nome_pet} registrado com sucesso na base SP!")
                            time.sleep(1)
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("Campos obrigatórios: Nome e WhatsApp.")

# ==============================================================================
# 6. MÓDULO DE CONSULTA (READ - NORMALIZAÇÃO PANDAS)
# ==============================================================================
elif aba_selecionada == "📊 Consultar Base de Dados":
    st.markdown("---")
    if sheet:
        with st.spinner("Consultando base de dados São Paulo..."):
            try:
                dados_brutos = sheet.get_all_values()
                if len(dados_brutos) > 1:
                    df = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
                    # Limpeza de cabeçalhos para evitar erros de case/espaço
                    df.columns = [str(c).strip().replace('"', '').capitalize() for c in df.columns]
                    
                    pesquisa = st.text_input("🔍 Buscar Pet:", placeholder="Digite o nome...")
                    
                    if pesquisa:
                        col_ref = df.columns[0] # Usa a primeira coluna (Nome)
                        df_f = df[df[col_ref].astype(str).str.contains(pesquisa, case=False, na=False)]
                    else:
                        df_f = df

                    st.info(f"Registros localizados: **{len(df_f)}**")
                    
                    # Seleção de colunas para exibição amigável
                    colunas_exibir = ['Nome', 'Espécie', 'Idade', 'Raça', 'Saúde', 'Whatsapp']
                    existentes = [c for c in colunas_exibir if c in df_f.columns]
                    
                    # Parâmetro width='stretch' atualizado para 2026
                    st.dataframe(df_f[existentes] if existentes else df_f, width="stretch", hide_index=True)
                else:
                    st.warning("Nenhum dado encontrado na planilha.")
            except Exception as e:
                st.error(f"Erro na consulta: {e}")

# ==============================================================================
# 7. RODAPÉ INSTITUCIONAL (ODS)
# ==============================================================================
st.markdown("---")
f_esq, f_dir = st.columns([2, 1])

with f_esq:
    st.caption("© 2026 | Projeto de Extensão Universitária | ADS Anhembi Morumbi")
    st.caption("Desenvolvedor: **Carlos Magno** | São Paulo - SP")

with f_dir:
    st.markdown("""
        <div style="text-align: right;">
            <span class="ods-tag" style="background-color: #4C9F38;">ODS 3</span>
            <span class="ods-tag" style="background-color: #FD9D24;">ODS 11</span>
            <span class="ods-tag" style="background-color: #56C02B;">ODS 15</span>
        </div>
    """, unsafe_allow_html=True)
# ==============================================================================
# TOTAL: 177 LINHAS DE CÓDIGO FONTE
# ==============================================================================