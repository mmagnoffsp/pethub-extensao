import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid

# --- CONEXÃO SEGURA ---
try:
    URL = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
except Exception:
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    key = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, key)

st.set_page_config(page_title="Guardião Pet SP", layout="wide", page_icon="🐾")

# Estilo para seguir as Heurísticas de Nielsen (Consistência Visual)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .stExpander { border: 1px solid #FF9800; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ATUALIZADO (Sem menção à Penha) ---
st.title("🐾 São Paulo - Brasil")
st.subheader("Plataforma de Identificação Animal")

# --- ÁREA DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Pet", expanded=True):
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Pet")
            especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
            local = st.text_input("Porte/Localização (Bairro/Cidade)")
            
            st.write("**Histórico de Saúde:**")
            c1_saude, c2_saude = st.columns(2)
            with c1_saude:
                castrado = st.checkbox("✂️ Castrado")
            with c2_saude:
                chipado = st.checkbox("💾 Chipado")
            
            opcoes_vacinas = ["V8/V10", "Antirrábica", "Gripe", "Giardíase", "V4/V5", "FeLV"]
            vacinas_sel = st.multiselect("💉 Vacinas Aplicadas", opcoes_vacinas)
        
        with col2:
            foto = st.file_uploader("📷 Foto do Pet", type=["jpg", "jpeg", "png"])
            buffer_foto_final = None
            if foto:
                img = Image.open(foto).convert("RGB")
                img.thumbnail((500, 500))
                buffer_foto_final = BytesIO()
                img.save(buffer_foto_final, format="JPEG", quality=60, optimize=True)
                st.image(buffer_foto_final.getvalue(), caption="Prévia da Foto", width=200)
        
        btn_salvar = st.form_submit_button("✅ Salvar no Guardião Pet")

    if btn_salvar and nome:
        try:
            url_publica_foto = None
            
            # 1. Upload da Foto para o Bucket: 'arquivos-pets'
            if buffer_foto_final:
                nome_arquivo = f"pet_{uuid.uuid4()}.jpg"
                supabase.storage.from_("arquivos-pets").upload(
                    path=nome_arquivo,
                    file=buffer_foto_final.getvalue(),
                    file_options={"content-type": "image/jpeg"}
                )
                url_publica_foto = supabase.storage.from_("arquivos-pets").get_public_url(nome_arquivo)

            # 2. Salvar Dados no Neon.com
            dados = {
                "nome": nome, 
                "especie": especie, 
                "idade": local,
                "castrado": "Sim" if castrado else "Não",
                "chipado": "Sim" if chipado else "Não",
                "vacinas": ", ".join(vacinas_sel),
                "url_foto": url_publica_foto,
                "status": "Disponível"
            }
            
            supabase.table("pets").insert(dados).execute()
            st.success(f"🐾 {nome} foi registrado com sucesso!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.markdown("---")

# --- MURAL DE PETS ---
st.subheader("📋 Pets Registrados")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 2, 1, 1])
            with c1:
                if pet.get('url_foto'):
                    st.image(pet['url_foto'], use_container_width=True)
                else:
                    st.info("Sem foto")
            with c2:
                st.write(f"### {pet['nome'].upper()}")
                st.write(f"📍 {pet.get('idade', 'N/A')}")
                st.caption(f"💉 Vacinas: {pet.get('vacinas', 'Nenhuma')}")
            with c3:
                link_pet = f"https://guardiao-pet-sp.streamlit.app/?id={pet['id']}"
                qr = qrcode.make(link_pet)
                buf_qr = BytesIO()
                qr.save(buf_qr, format="PNG")
                st.image(buf_qr.getvalue(), width=100)
                st.download_button("💾 QR", buf_qr.getvalue(), f"qr_{pet['id']}.png", key=f"q_{pet['id']}")
            with c4:
                if st.button("🗑️ Deletar", key=f"d_{pet['id']}", type="primary"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()
else:
    st.info("Nenhum pet no mural.")