import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import urllib.parse

# ==============================================================================
# 1. CONFIGURAÇÕES GLOBAIS (ADS 2026 - ANHEMBI MORUMBI)
# ==============================================================================
st.set_page_config(
    page_title="Guardião Pet SP - ADS 2026", 
    page_icon="🐾", 
    layout="centered"
)

# Estilização CSS personalizada (IHC - Foco em Usabilidade e Feedback)
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #2E7D32 !important; color: white !important; 
        font-weight: bold; font-size: 18px !important; 
    }
    .ods-tag {
        display: inline-block; padding: 3px 10px; border-radius: 5px;
        color: white; font-size: 11px; font-weight: bold; margin-right: 5px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #2E7D32; border-radius: 10px;
    }
    /* Legenda de auxílio IHC - Heurística de Visibilidade */
    .ihc-helper {
        font-size: 11px; color: #666; margin-top: -10px; margin-bottom: 10px;
        font-style: italic; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS (GOOGLE SHEETS API)
# ==============================================================================
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def conectar_google_sheets():
    """
    Estabelece a conexão segura com a API do Google Sheets.
    Utiliza segredos do Streamlit Cloud para proteção de credenciais.
    """
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # ID da planilha do projeto PetHub/Guardião Pet
        ID_PLANILHA = "1uiouxhZPb8jFLC4GUnSzsuqS2xKP2sEBv5IlkorCl-s"
        return client.open_by_key(ID_PLANILHA).get_worksheet(0) 
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

# Instanciando a conexão
sheet = conectar_google_sheets()

# ==============================================================================
# 3. INTERFACE LATERAL (NAVEGAÇÃO E COMPARTILHAMENTO)
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

# BOTÃO DE COMPARTILHAMENTO COM REFINAMENTO IHC (Heurística 3)
msg_share = urllib.parse.quote(f"Ajude um pet em SP! Acesse o Guardião Pet SP: {url_app}")
st.sidebar.markdown(f'''
    <a href="https://wa.me/?text={msg_share}" target="_blank">
        <button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer; font-weight:bold;">
            Divulgar App no WhatsApp 📱
        </button>
    </a>
    <p class="ihc-helper">O link abrirá o WhatsApp em uma nova aba.</p>
''', unsafe_allow_html=True)

st.sidebar.write("**Status:** 🟢 Sistema Online")
st.sidebar.write("**Desenvolvedor:** Carlos Magno")
st.sidebar.write("**Localização:** São Paulo - SP")
st.sidebar.write("**Versão:** ADS.2026.V11_FULL_CLICKABLE")

# ==============================================================================
# 4. CABEÇALHO E ALINHAMENTO ODS (REQUISITO TRILHA ACADÊMICA)
# ==============================================================================
st.title("🐾 Guardião Pet SP")
st.subheader("Sistema PetHub - Gestão de Adoção e Tutoria")

with st.expander("🌍 Conexão com os Objetivos de Desenvolvimento Sustentável (ODS)"):
    st.markdown("""
    Este projeto de extensão universitária mitiga problemas reais em São Paulo - SP:
    - **ODS 3 (Saúde):** Controle sanitário urbano e prevenção de zoonoses.
    - **ODS 11 (Cidades):** Rede de apoio e proteção animal urbana.
    - **ODS 15 (Vida Terrestre):** Combate ao abandono de espécies domésticas.
    """)

# ==============================================================================
# 5. MÓDULO DE CADASTRO
# ==============================================================================
if aba_selecionada == "📝 Cadastrar Novo Pet":
    st.markdown("---")
    
    if sheet:
        with st.form("form_registro_pet", clear_on_submit=True):
            st.write("### 📝 1. Dados do Animal e Responsável")
            col_1, col_2 = st.columns(2)
            
            with col_1:
                nome_pet = st.text_input("Nome do Pet*", placeholder="Ex: Mel")
                especie = st.selectbox("Espécie*", ["Cão", "Gato", "Ave", "Outro"])
                t_resp = st.selectbox("Tipo de Responsável*", ["ONG", "Petshop (Feira)", "Tutor Individual"])
            
            with col_2:
                raca = st.text_input("Raça", placeholder="Ex: SRD")
                idade = st.number_input("Idade Estimada (Anos)", 0, 30, 0)
                whatsapp = st.text_input("WhatsApp (DDD + Número)*", placeholder="11941507706")
            
            st.write("---")
            st.write("### 💉 2. Protocolo de Saúde (ODS 3)")
            
            # Dinâmica de vacinas por espécie
            if especie == "Cão":
                op_vax = ["Antirrábica", "V8 (Octovalente)", "V10 (Decavalente)", "Gripe", "Giárdia"]
            elif especie == "Gato":
                op_vax = ["Antirrábica", "V3 (Tríplice)", "V4 (Quádrupla)", "V5 (Quíntupla)"]
            else:
                op_vax = ["Vermifugado", "Check-up Geral"]
            
            vax_sel = st.multiselect("Selecione as vacinas aplicadas:", op_vax)
            saude_obs = st.text_input("Notas adicionais de saúde", placeholder="Ex: Castrado, idoso...")
            
            # Submissão dos Dados
            if st.form_submit_button("✅ PUBLICAR FICHA DE ADOÇÃO"):
                if nome_pet and whatsapp:
                    with st.spinner("Sincronizando com a base de dados..."):
                        # Tratamento para evitar duplicidade do código do país (55)
                        num_limpo = "".join(filter(str.isdigit, whatsapp))
                        num_final = num_limpo if num_limpo.startswith("55") else f"55{num_limpo}"
                        
                        v_txt = ", ".join(vax_sel) if vax_sel else "Não informada"
                        status_f = f"[{t_resp}] Vacinas: {v_txt} | Obs: {saude_obs}"
                        
                        # Link do WhatsApp formatado para clique direto
                        msg_int = urllib.parse.quote(f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e gostaria de mais informações.")
                        link_w = f"https://wa.me/{num_final}?text={msg_int}"
                        
                        try:
                            sheet.append_row([nome_pet, especie, idade, raca, status_f, whatsapp, link_w])
                            st.balloons()
                            st.success(f"Ficha do(a) {nome_pet} publicada com sucesso!")
                            time.sleep(1)
                        except Exception as e:
                            st.error(f"Erro ao salvar na planilha: {e}")
                else:
                    st.warning("Atenção: Os campos Nome e WhatsApp são obrigatórios.")

# ==============================================================================
# 6. MÓDULO DE CONSULTA (REFRESH E CONTATO DIRETO CLICÁVEL)
# ==============================================================================
elif aba_selecionada == "📊 Consultar Base de Dados":
    st.markdown("---")
    
    if sheet:
        with st.spinner("Consultando base de dados em tempo real..."):
            try:
                dados = sheet.get_all_values()
                if len(dados) > 1:
                    df = pd.DataFrame(dados[1:], columns=dados[0])
                    # Padronização de nomes de colunas para IHC
                    df.columns = [str(c).strip().replace('"', '').capitalize() for c in df.columns]
                    
                    # Filtros de Busca (Heurística 7 - Eficiência)
                    c_f, c_b = st.columns([1, 2])
                    with c_f:
                        f_tipo = st.selectbox("Responsável:", ["Todos", "ONG", "Petshop", "Tutor"])
                    with c_b:
                        busca = st.text_input("🔍 Nome do Pet:", placeholder="Buscar por nome...")
                    
                    # Lógica de Filtragem do DataFrame
                    df_f = df
                    if f_tipo != "Todos":
                        df_f = df[df[df.columns[4]].str.contains(f_tipo, case=False, na=False)]
                    if busca:
                        df_f = df_f[df_f[df_f.columns[0]].str.contains(busca, case=False, na=False)]

                    # Exibição dos Resultados (IHC - Controle e Liberdade)
                    if df_f.empty:
                        st.warning(f"🔍 Nenhum pet encontrado para: '{busca}'.")
                        if st.button("🔄 Limpar Filtros e Ver Todos"):
                            st.rerun()
                    else:
                        st.info(f"Foram localizadas **{len(df_f)}** fichas em São Paulo.")
                        
                        # --- SOLUÇÃO PARA O LINK CLICÁVEL ---
                        # Usamos column_config para que o Streamlit trate a URL como link real
                        # O nome da coluna deve ser o mesmo da sua planilha (ajuste se necessário)
                        st.dataframe(
                            df_f, 
                            column_config={
                                df_f.columns[6]: st.column_config.LinkColumn(
                                    "Contato Direto 🐾", 
                                    display_text="Chamar no WhatsApp 💬",
                                    help="Clique para abrir o chat sem copiar nada!"
                                )
                            },
                            width="stretch", 
                            hide_index=True
                        )
                        st.caption("✅ Dica de Usabilidade: Clique no texto 'Chamar no WhatsApp' para contato direto.")
                else:
                    st.warning("A base de dados ainda está vazia.")
            except Exception as e:
                st.error(f"Erro na consulta: {e}")

# ==============================================================================
# 7. RODAPÉ INSTITUCIONAL (ADS ANHEMBI MORUMBI)
# ==============================================================================
st.markdown("---")
st.caption("© 2026 | Projeto de Extensão Universitária | ADS Anhembi Morumbi | São Paulo - SP")
st.markdown("""<div style="text-align: right;"><span class="ods-tag" style="background-color: #4C9F38;">ODS 3</span>
<span class="ods-tag" style="background-color: #FD9D24;">ODS 11</span>
<span class="ods-tag" style="background-color: #56C02B;">ODS 15</span></div>""", unsafe_allow_html=True)

# FINAL DO CÓDIGO FONTE - SISTEMA PETHUB VERSÃO 2026.V11
# ==============================================================================