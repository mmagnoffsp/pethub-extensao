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
    # Backup para testes locais
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
                foto = st.file_uploader("📷 Subir Foto", type=["jpg", "jpeg", "png"])
                
                if foto is not None:
                    img = Image.open(foto)
                    img = img.convert("RGB")
                    img.thumbnail((500, 500))
                    
                    buffer_img = BytesIO()
                    img.save(buffer_img, format="JPEG", quality=60, optimize=True)
                    st.image(buffer_img, caption="Prévia", width=200)
            
            btn_cadastrar = st.form_submit_button("✅ Salvar Pet")

        if btn_cadastrar and nome:
            try:
                supabase.table("pets").insert({"nome": nome, "especie": especie, "idade": idade}).execute()
                st.success(f"Cadastro de {nome} realizado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    
    # --- LISTAGEM COM QR CODE ---
    st.subheader("📋 Pets Cadastrados")
    res = supabase.table("pets").select("*").execute()
    
    if res.data:
        for pet in res.data:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                
                with c1:
                    st.write(f"### {pet['nome'].upper()}")
                    st.write(f"**Espécie:** {pet['especie']} | **Idade:** {pet['idade']}")
                
                with c2:
                    link_pet = f"https://guardiao-pet-sp-cmmf2026.streamlit.app/?id={pet['id']}"
                    qr = qrcode.make(link_pet)
                    buf_qr = BytesIO()
                    qr.save(buf_qr, format="PNG")
                    st.image(buf_qr.getvalue(), caption="QR Code", width=110)
                    st.download_button("💾 Baixar", buf_qr.getvalue(), f"qr_{pet['nome']}.png", "image/png", key=f"dl_{pet['id']}")
                
                with c3:
                    if st.button(f"🗑️ Deletar", key=f"del_{pet['id']}", type="primary"):
                        supabase.table("pets").delete().eq("id", pet['id']).execute()
                        st.rerun()
    else:
        st.info("Nenhum pet cadastrado.")

with aba_vacinas:
    st.title("💉 Guia de Vacinação Essencial")
    st.write("Informações importantes para a saúde dos pets na Vila Esperança e região.")

    col_dog, col_cat = st.columns(2)

    with col_dog:
        st.subheader("🐕 Calendário Canino")
        with st.container(border=True):
            st.markdown("""
            - **V8 ou V10 (Polivalente):** Protege contra Cinomose, Parvovirose e Leptospirose. (3 doses iniciais + reforço anual).
            - **Antirrábica:** Protege contra a Raiva. (Dose única anual).
            - **Gripe Canina:** Previne tosse e infecções respiratórias. (Anual).
            - **Giardíase:** Protege contra o protozoário Giardia. (Reforço anual).
            """)

    with col_cat:
        st.subheader("🐈 Calendário Felino")
        with st.container(border=True):
            st.markdown("""
            - **V4 ou V5 (Polivalente):** Protege contra Rinotraqueíte, Calicivirose e Panleucopenia (V5 inclui FeLV).
            - **Antirrábica:** Protege contra a Raiva. (Dose única anual).
            - **FeLV (Leucemia Felina):** Essencial para gatos com acesso à rua ou convívio com outros gatos.
            """)
    
    st.info("💡 Lembre-se: O acompanhamento de um médico veterinário é indispensável.")