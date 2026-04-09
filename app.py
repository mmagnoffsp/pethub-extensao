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

st.set_page_config(page_title="Guardião Pet Brasil", layout="wide", page_icon="🐾")

# --- INTERFACE: ABAS ---
aba_gestao, aba_vacinas = st.tabs(["🏠 Gestão de Pets", "💉 Guia de Saúde Animal"])

with aba_gestao:
    st.title("🐾 Guardião Pet Brasil")
    st.subheader("Conectando e protegendo animais em todo o território nacional")
    
    with st.expander("➕ Cadastrar Novo Pet", expanded=True):
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Pet")
                especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
                # Mudamos 'idade' para algo mais completo, já que é Brasil todo
                info_adicional = st.text_input("Porte, Idade ou Localização (Cidade/UF)")
            
            with col2:
                foto = st.file_uploader("📷 Foto do Pet", type=["jpg", "jpeg", "png"])
                
                if foto is not None:
                    img = Image.open(foto)
                    img = img.convert("RGB")
                    img.thumbnail((500, 500))
                    
                    buffer_img = BytesIO()
                    img.save(buffer_img, format="JPEG", quality=60, optimize=True)
                    st.image(buffer_img, caption="Prévia da Foto", width=200)
            
            btn_cadastrar = st.form_submit_button("✅ Cadastrar no Sistema Nacional")

        if btn_cadastrar and nome:
            try:
                # Salvando no banco de dados nacional
                supabase.table("pets").insert({"nome": nome, "especie": especie, "idade": info_adicional}).execute()
                st.success(f"O pet {nome} foi registrado com sucesso na rede nacional!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao conectar com o servidor: {e}")

    st.markdown("---")
    
    # --- LISTAGEM NACIONAL COM QR CODE ---
    st.subheader("📋 Mural de Pets Registrados")
    res = supabase.table("pets").select("*").execute()
    
    if res.data:
        for pet in res.data:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                
                with c1:
                    st.write(f"### {pet['nome'].upper()}")
                    st.write(f"**Espécie:** {pet['especie']}")
                    st.write(f"**Detalhes/Local:** {pet['idade']}")
                
                with c2:
                    # O link agora leva para o domínio nacional
                    link_pet = f"https://guardiao-pet-sp-cmmf2026.streamlit.app/?id={pet['id']}"
                    qr = qrcode.make(link_pet)
                    buf_qr = BytesIO()
                    qr.save(buf_qr, format="PNG")
                    st.image(buf_qr.getvalue(), caption="QR Identificador Nacional", width=110)
                    st.download_button("💾 Baixar QR", buf_qr.getvalue(), f"qr_{pet['nome']}.png", "image/png", key=f"dl_{pet['id']}")
                
                with c3:
                    if st.button(f"🗑️ Remover", key=f"del_{pet['id']}", type="primary"):
                        supabase.table("pets").delete().eq("id", pet['id']).execute()
                        st.rerun()
    else:
        st.info("Aguardando o primeiro registro de pet nesta rede nacional.")

with aba_vacinas:
    st.title("💉 Guia de Vacinação Brasil")
    st.write("Protocolo vacinal recomendado pelas principais associações veterinárias do país.")

    col_dog, col_cat = st.columns(2)

    with col_dog:
        st.subheader("🐕 Calendário Canino Nacional")
        with st.container(border=True):
            st.markdown("""
            - **Polivalente (V8/V10):** Essencial em todos os estados contra viroses graves.
            - **Antirrábica:** Obrigatória em todo o Brasil (Dose anual).
            - **Leishmaniose:** Crucial em regiões endêmicas do Brasil.
            - **Gripe e Giardíase:** Recomendadas para pets com convívio social.
            """)

    with col_cat:
        st.subheader("🐈 Calendário Felino Nacional")
        with st.container(border=True):
            st.markdown("""
            - **Polivalente (V4 ou V5):** Base da saúde felina no país.
            - **Antirrábica:** Obrigatória nacionalmente.
            - **FeLV:** Testagem e vacinação recomendada para gatos de todas as regiões.
            """)
    
    st.info("💡 Este guia segue as diretrizes nacionais. Consulte sempre um veterinário local.")