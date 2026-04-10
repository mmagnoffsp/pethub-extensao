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

# --- CABEÇALHO ---
st.title("🐾 São Paulo - Brasil")
st.subheader("Plataforma de Identificação Animal")

# --- ÁREA DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Pet e Tutor", expanded=True):
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🐕 Informações do Pet")
            nome = st.text_input("Nome do Pet")
            especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
            
            st.write("**Histórico de Saúde:**")
            c1_saude, c2_saude = st.columns(2)
            with c1_saude:
                castrado = st.checkbox("✂️ Castrado")
            with c2_saude:
                chipado = st.checkbox("💾 Chipado")
            
            opcoes_vacinas = ["V8/V10", "Antirrábica", "Gripe", "Giardíase", "V4/V5", "FeLV"]
            vacinas_sel = st.multiselect("💉 Vacinas Aplicadas", opcoes_vacinas)
            
            foto = st.file_uploader("📷 Foto do Pet", type=["jpg", "jpeg", "png"])

        with col2:
            st.write("### 👤 Informações de Contato (Tutor)")
            endereco = st.text_input("🏠 Endereço Completo")
            email = st.text_input("📧 E-mail de Contato")
            telefone = st.text_input("📞 Telefone / WhatsApp (com DDD)")
            instagram = st.text_input("📸 Instagram (ex: @usuario)")
            
        btn_salvar = st.form_submit_button("✅ Salvar no Guardião Pet")

    if btn_salvar and nome:
        try:
            url_publica_foto = None
            
            # Processamento da Foto
            if foto:
                img = Image.open(foto).convert("RGB")
                img.thumbnail((500, 500))
                buffer_foto_final = BytesIO()
                img.save(buffer_foto_final, format="JPEG", quality=60, optimize=True)
                
                nome_arquivo = f"pet_{uuid.uuid4()}.jpg"
                supabase.storage.from_("arquivos-pets").upload(
                    path=nome_arquivo,
                    file=buffer_foto_final.getvalue(),
                    file_options={"content-type": "image/jpeg"}
                )
                url_publica_foto = supabase.storage.from_("arquivos-pets").get_public_url(nome_arquivo)

            # 2. Salvar Dados (Incluindo os novos campos)
            # Nota: Certifique-se que estas colunas existam na sua tabela 'pets' no Neon/Supabase
            dados = {
                "nome": nome, 
                "especie": especie, 
                "idade": endereco, # Usando o campo 'idade' existente para endereço por enquanto, ou ajuste no banco
                "castrado": "Sim" if castrado else "Não",
                "chipado": "Sim" if chipado else "Não",
                "vacinas": ", ".join(vacinas_sel),
                "url_foto": url_publica_foto,
                "status": f"Tel: {telefone} | Insta: {instagram} | Email: {email}" # Agrupando contatos no status para teste rápido
            }
            
            supabase.table("pets").insert(dados).execute()
            st.success(f"🐾 {nome} e seus dados de contato foram registrados!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.markdown("---")

# --- MURAL DE PETS ---
st.subheader("📋 Pets Registrados e Contatos")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 2.5, 1, 1])
            with c1:
                if pet.get('url_foto'):
                    st.image(pet['url_foto'], use_container_width=True)
                else:
                    st.info("Sem foto")
            with c2:
                st.write(f"### {pet['nome'].upper()}")
                st.write(f"🏠 **Endereço:** {pet.get('idade', 'Não informado')}")
                st.write(f"📞 **Contatos:** {pet.get('status', 'Não informado')}")
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