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
    # Fallback para desenvolvimento local
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    KEY = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Guardião Pet Brasil", layout="wide", page_icon="🐾")

# --- INTERFACE: ABAS ---
aba_gestao, aba_vacinas = st.tabs(["🏠 Gestão de Pets", "💉 Guia de Saúde Animal"])

with aba_gestao:
    st.title("🐾 Guardião Pet Brasil")
    st.subheader("Plataforma Nacional de Identificação e Proteção Animal")
    
    with st.expander("➕ Cadastrar Novo Pet", expanded=True):
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Pet")
                especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
                info_adicional = st.text_input("Porte/Localização (Cidade/UF)")
                
                # --- NOVOS BOTÕES DE SAÚDE ---
                st.write("**Histórico de Saúde:**")
                c1_saude, c2_saude = st.columns(2)
                with c1_saude:
                    castrado = st.checkbox("✂️ Castrado")
                with c2_saude:
                    chipado = st.checkbox("💾 Chipado")
                
                # --- SELEÇÃO REAL DE VACINAS ---
                opcoes_vacinas = [
                    "V8/V10 (Polivalente)", "Antirrábica", "Gripe Canina", 
                    "Giardíase", "V4/V5 (Felina)", "FeLV"
                ]
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
            # Organizando dados para o Neon
            dados = {
                "nome": nome,
                "especie": especie,
                "idade": info_adicional,
                "castrado": "Sim" if castrado else "Não",
                "chipado": "Sim" if chipado else "Não",
                "vacinas": ", ".join(vacinas_sel)
            }
            try:
                supabase.table("pets").insert(dados).execute()
                st.success(f"{nome} cadastrado com sucesso no sistema nacional!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    
    # --- LISTAGEM COM QR CODE ---
    st.subheader("📋 Pets Registrados")
    res = supabase.table("pets").select("*").order("created_at", desc=True).execute()
    
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

with aba_vacinas:
    st.title("💉 Guia de Vacinação Brasil")
    st.markdown("Protocolo recomendado para cães e gatos em território nacional.")
    col_dog, col_cat = st.columns(2)
    with col_dog:
        st.subheader("🐕 Cães")
        st.write("- V8/V10: Polivalente essencial.\n- Antirrábica: Obrigatória.\n- Gripe/Giardíase: Recomendadas.")
    with col_cat:
        st.subheader("🐈 Gatos")
        st.write("- V4/V5: Proteção básica/FeLV.\n- Antirrábica: Obrigatória.\n- FeLV: Crucial para gatos com acesso à rua.")