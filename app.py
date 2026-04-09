import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image  # Biblioteca para tratar a foto

# --- CONEXÃO SEGURA ---
# O try/except garante que funcione tanto no seu PC quanto na Internet (Nuvem)
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # Caso rode localmente no VS Code, ele usa estas chaves:
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    KEY = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Guardião Pet SP", layout="wide", page_icon="🐾")

# --- INTERFACE: ABAS ---
aba_gestao, aba_vacinas = st.tabs(["🏠 Gestão de Pets", "💉 Cartão de Vacinas"])

with aba_gestao:
    st.title("🐾 Painel de Controle - Guardião Pet SP")
    
    with st.expander("➕ Cadastrar Novo Pet", expanded=True):
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Pet")
                especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
                idade = st.text_input("Idade/Porte")
            
            with col2:
                foto = st.file_uploader("📷 Subir JPG (Celular ou PC)", type=["jpg", "jpeg", "png"])
                
                # --- LÓGICA DE COMPRESSÃO E PRÉVIA ---
                if foto is not None:
                    img = Image.open(foto)
                    img = img.convert("RGB") # Garante compatibilidade
                    img.thumbnail((500, 500)) # Redimensiona para ocupar pouca memória
                    
                    # Salva na memória com qualidade reduzida (otimização para o banco)
                    buffer = BytesIO()
                    img.save(buffer, format="JPEG", quality=60, optimize=True)
                    st.image(buffer, caption="Prévia Otimizada (Leve)", width=200)
            
            btn_cadastrar = st.form_submit_button("✅ Salvar Pet e Gerar QR")

        if btn_cadastrar and nome:
            try:
                supabase.table("pets").insert({"nome": nome, "especie": especie, "idade": idade}).execute()
                st.success(f"Cadastro de {nome} realizado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")

    st.markdown("---")
    
    # --- LISTAGEM E DELETAR ---
    st.subheader("📋 Pets Cadastrados")
    res = supabase.table("pets").select("*").execute()
    
    if res.data:
        for pet in res.data:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"**{pet['nome'].upper()}** - {pet['especie']} ({pet['idade']})")
                with c2:
                    if st.button(f"🔍 Ver QR", key=f"qr_{pet['id']}"):
                        st.info(f"QR Code para {pet['nome']} pronto para impressão!")
                with c3:
                    if st.button(f"🗑️ Deletar", key=f"del_{pet['id']}", type="primary"):
                        try:
                            supabase.table("pets").delete().eq("id", pet['id']).execute()
                            st.rerun()
                        except Exception as e:
                            st.error("Erro ao deletar.")
    else:
        st.info("Nenhum pet cadastrado na região da Penha ainda.")

# --- ABA 2: VACINAS (ESTRUTURA INICIAL) ---
with aba_vacinas:
    st.title("💉 Controle de Vacinação")
    st.write("Área destinada ao histórico de vacinas e clínicas parceiras.")
    if res.data:
        pet_vacinado = st.selectbox("Selecione o Pet para Vacinar", [p['nome'] for p in res.data])
        st.date_input("Data da Vacina")
        st.text_input("Nome da Vacina (ex: V10, Antirrábica)")
        if st.button("Registrar Vacina"):
            st.success("Dados de vacina preparados para o banco!")
    else:
        st.warning("Cadastre um pet primeiro para gerenciar as vacinas.")