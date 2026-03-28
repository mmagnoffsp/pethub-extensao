import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# ==============================================================================
# 1. CONFIGURAÇÕES GLOBAIS (ADS 2026)
# ==============================================================================
st.set_page_config(
    page_title="Guardião Pet SP - ADS 2026", 
    page_icon="🐾", 
    layout="centered"
)

# Estilização CSS personalizada para o Projeto PetHub
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #2E7D32; color: white; 
        font-weight: bold; font-size: 18px !important; 
    }
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { 
        font-size: 20px !important; font-weight: 600 !important; 
        padding: 10px 5px !important; color: #1B5E20 !important; 
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #2E7D32;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS (USANDO ID FIXO)
# ==============================================================================
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def conectar_google_sheets():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # ID extraído da sua URL original
        ID_PLANILHA = "1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s"
        
        # Acessa a primeira aba da planilha
        return client.open_by_key(ID_PLANILHA).get_worksheet(0) 
    except Exception as e:
        st.error(f"Erro Crítico de Acesso: {e}")
        return None

sheet = conectar_google_sheets()

# ==============================================================================
# 3. INTERFACE LATERAL (QR CODE E STATUS)
# ==============================================================================
url_app = "https://guardiao-pet-sp-mmagnoff.streamlit.app"
qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url_app}"
st.sidebar.image(qr_code, caption="Acesse o PetHub")

aba_selecionada = st.sidebar.radio(
    "Menu de Navegação:", 
    ["📝 Cadastrar Novo Pet", "📊 Consultar Base de Dados"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.write("**Status:** 🟢 Online")
st.sidebar.write("**Build:** ADS.2026.FINAL.CORRIGIDO")
st.sidebar.write("**Dev:** Carlos Magno (Penha, SP)")
st.sidebar.write("**Instituição:** Anhembi Morumbi")

# ==============================================================================
# 4. MÓDULO DE CADASTRO (CREATE)
# ==============================================================================
if aba_selecionada == "📝 Cadastrar Novo Pet":
    st.title("🐾 Guardião Pet SP")
    st.subheader("Sistema PetHub - Projeto de Extensão ADS")
    st.markdown("---")
    
    if sheet:
        with st.form("form_pet", clear_on_submit=True):
            st.write("### 📝 Informações do Animal")
            c1, c2 = st.columns(2)
            with c1:
                nome_pet = st.text_input("Nome do Pet*", placeholder="Ex: Tor")
                especie = st.selectbox("Espécie*", ["Cão", "Gato", "Ave", "Outro"])
            with c2:
                raca = st.text_input("Raça", placeholder="Ex: SRD")
                idade = st.number_input("Idade Estimada", 0, 30, 0)
            
            st.write("---")
            st.write("### 📞 Contato e Saúde")
            saude = st.text_input("Status de Saúde", placeholder="Ex: Vacinado e Castrado")
            zap = st.text_input("WhatsApp (DDD + Número)*", placeholder="11912345678")
            
            if st.form_submit_button("✅ SALVAR NO BANCO DE DADOS"):
                if nome_pet and zap:
                    with st.spinner("Sincronizando..."):
                        num_limpo = "".join(filter(str.isdigit, zap))
                        link_w = f"https://wa.me/55{num_limpo}?text=Olá! Vi o pet {nome_pet} no Guardião Pet SP."
                        try:
                            # Ordem: Nome, Espécie, Idade, Raça, Saúde, WhatsApp, Link
                            sheet.append_row([nome_pet, especie, idade, raca, saude, zap, link_w])
                            st.balloons()
                            st.success(f"Registro de {nome_pet} concluído!")
                            time.sleep(2)
                        except Exception as err:
                            st.error(f"Erro ao salvar: {err}")
                else:
                    st.warning("Preencha os campos obrigatórios (*)")

# ==============================================================================
# 5. MÓDULO DE CONSULTA (READ - CORREÇÃO DE EXIBIÇÃO TOTAL)
# ==============================================================================
elif aba_selecionada == "📊 Consultar Base de Dados":
    st.title("📊 Base Regional de Animais")
    st.markdown("Consulte aqui todos os pets registrados no sistema.")
    
    if sheet:
        with st.spinner("Lendo dados da planilha..."):
            try:
                # Captura todos os valores da planilha
                raw_values = sheet.get_all_values()
                
                if len(raw_values) > 1:
                    # Cria o DataFrame com a primeira linha como cabeçalho
                    df = pd.DataFrame(raw_values[1:], columns=raw_values[0])
                    
                    # Normalização rigorosa das colunas para evitar o erro 'Nome'
                    df.columns = [str(c).strip().replace('"', '').capitalize() for c in df.columns]
                    
                    # Interface de busca
                    termo = st.text_input("🔍 Localizar Pet:", placeholder="Digite o nome para pesquisar...")
                    
                    if termo:
                        # Busca na primeira coluna (geralmente Nome) ignorando Case
                        col_busca = df.columns[0]
                        df_res = df[df[col_busca].astype(str).str.contains(termo, case=False, na=False)]
                    else:
                        df_res = df

                    st.write(f"Exibindo **{len(df_res)}** pets encontrados:")
                    
                    # Verifica quais colunas realmente existem para não dar erro de KeyError
                    colunas_desejadas = ['Nome', 'Espécie', 'Idade', 'Raça', 'Saúde', 'Whatsapp']
                    colunas_para_exibir = [c for c in colunas_desejadas if c in df_res.columns]
                    
                    # Se não encontrar as colunas normalizadas, mostra o DF bruto para debug
                    if not colunas_para_exibir:
                        st.dataframe(df_res, width="stretch", hide_index=True)
                    else:
                        # Exibe a tabela formatada
                        # width="stretch" corrige o aviso de 2025/2026 no terminal
                        st.dataframe(df_res[colunas_para_exibir], width="stretch", hide_index=True)
                else:
                    st.info("A planilha está vazia ou contém apenas o cabeçalho.")
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")
                # Mostra as colunas detectadas para ajudar no diagnóstico de ADS
                if 'df' in locals():
                    st.write("Colunas detectadas:", list(df.columns))

# ==============================================================================
# 6. RODAPÉ INSTITUCIONAL
# ==============================================================================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 12px;">
        © 2026 | Projeto de Extensão - ADS Anhembi Morumbi<br>
        Desenvolvido por <b>Carlos Magno</b> - Penha, São Paulo/SP<br>
        Tecnologias: Python, Streamlit, Google Sheets API
    </div>
    """, unsafe_allow_html=True)