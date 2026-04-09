import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image

# --- CONEXÃO SEGURA ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    KEY = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Guardião Pet Brasil", layout="wide", page_icon="🐾")

st.title("🐾 Guardião Pet Brasil")
st.subheader("Plataforma Nacional de Identificação e Proteção Animal")

# --- ÁREA DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Pet", expanded=True):
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Pet")
            especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
            info_adicional = st.text_input("Porte/Localização (Cidade/UF)")
            
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
            if foto:
                img = Image.open(foto).convert("RGB")
                img.thumbnail((500, 500))
                buffer_img = BytesIO()
                img.save(buffer_img, format="JPEG", quality=60)
                st.image(buffer_img.getvalue(), caption="Prévia", width=200)
        
        btn_salvar = st.form_submit_button("✅ Cadastrar Pet")

    if btn_salvar and nome:
        dados = {
            "nome": nome, "especie": especie, "idade": info_adicional,
            "castrado": "Sim" if castrado else "Não",
            "chipado": "Sim" if chipado else "Não",
            "vacinas": ", ".join(vacinas_sel)
        }
        try:
            supabase.table("pets").insert(dados).execute()
            st.success(f"{nome} cadastrado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.markdown("---")

# --- LISTAGEM (ORDENADA POR ID) ---
st.subheader("📋 Pets Registrados")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.write(f"### {pet['nome'].upper()}")
                st.write(f"📍 **Local:** {pet['idade']}")
                st.write(f"🩺 **Saúde:** {'✂️ Castrado' if pet.get('castrado') == 'Sim' else '⭕ Não Castrado'} | "
                            f"{'💾 Chipado' if pet.get('chipado') == 'Sim' else '⭕ Sem Chip'}")
                if pet.get('vacinas'):
                    st.info(f"💉 **Vacinas:** {pet['vacinas']}")
            
            with c2:
                link_pet = f"https://guardiao-pet-sp-cmmf2026.streamlit.app/?id={pet['id']}"
                qr = qrcode.make(link_pet)
                buf_qr = BytesIO()
                qr.save(buf_qr, format="PNG")
                st.image(buf_qr.getvalue(), caption="QR Identificador", width=110)
                st.download_button("💾 Baixar QR", buf_qr.getvalue(), f"qr_{pet['id']}.png", "image/png", key=f"dl_{pet['id']}")
            
            with c3:
                if st.button("🗑️ Deletar", key=f"del_{pet['id']}", type="primary"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()
else:
    st.info("Nenhum pet registrado no momento.")