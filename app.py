import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid
import urllib.parse
import re

# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA COISA) ---
st.set_page_config(
    page_title="Guardião Pet SP", 
    layout="wide", 
    page_icon="🐾",
    initial_sidebar_state="collapsed"
)

# --- CONEXÃO SEGURA ---
try:
    URL = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
except Exception:
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    key = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, key)

# --- FUNÇÃO AUXILIAR PARA WHATSAPP ---
def criar_link_whatsapp(telefone, nome_pet, pet_id):
    numero_limpo = re.sub(r'\D', '', telefone)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    
    # URL encurtada para evitar bugs de caracteres especiais no Zap
    link_site = f"https://guardiao-pet-sp.streamlit.app/?id={pet_id}"
    
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e quero mais informações: {link_site}"
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

# --- 🎯 LÓGICA DE ROTEAMENTO (VISTA DO CLIENTE) ---
# Executamos isso no topo para interceptar o acesso antes de carregar o painel administrativo
query_params = st.query_params
if "id" in query_params:
    pet_id_url = query_params["id"]
    try:
        res_pet = supabase.table("pets").select("*").eq("id", pet_id_url).execute()
        if res_pet.data:
            pet = res_pet.data[0]
            
            if st.button("⬅️ Ver todos os pets"):
                st.query_params.clear()
                st.rerun()
                
            st.divider()
            col_img, col_info = st.columns([1, 1.2])
            
            with col_img:
                if pet.get('foto_url'):
                    st.image(pet['foto_url'], use_container_width=True)
                else:
                    st.info("Pet sem foto.")
            
            with col_info:
                st.markdown(f"# 🐾 {pet['nome'].upper()}")
                st.markdown(f"**Responsável:** {pet.get('idade', 'Resgate Independente')}")
                
                status_raw = pet.get('status', '')
                info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
                
                st.write(f"📍 **Localização:** {info.get('LOCAL', 'Não informado')}")
                st.write(f"🩺 **Saúde:** {info.get('SAUDE', 'N/A').replace(',', ' | ')}")
                
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f"""
                        <a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px; text-align: center; text-decoration: none; display: block; border-radius: 8px; font-weight: bold; font-size: 18px;">
                            💬 Falar com o Protetor no WhatsApp
                        </a>
                    """, unsafe_allow_html=True)
            
            st.stop() # IMPEDE O CARREGAMENTO DO RESTANTE DO APP PARA O CLIENTE
    except Exception:
        st.error("Erro ao carregar os dados do pet.")

# --- ESTILIZAÇÃO (SÓ CARREGA SE NÃO FOR LINK DIRETO) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .badge-perfil {
        padding: 4px 8px; border-radius: 4px; font-size: 12px;
        font-weight: bold; color: white; background-color: #FF9800;
        margin-bottom: 5px; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🏠 TELA PRINCIPAL (ADMIN / CADASTRO) ---
st.title("🐾 Guardião Pet SP")
st.subheader("Painel Administrativo")

st.info("Escolha seu perfil para realizar um novo cadastro:")
aba_protetor, aba_ong, aba_lojista = st.tabs(["🦸 Protetor", "🏢 ONG", "🏪 Lojista"])

def processar_cadastro(perfil_nome, entidade_nome):
    with st.form(f"form_{perfil_nome}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 🐕 Dados do Pet")
            p_nome = st.text_input("Nome/Apelido")
            p_especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"], key=f"esp_{perfil_nome}")
            c_saude, c_chip = st.columns(2)
            with c_saude: p_castrado = st.checkbox("✂️ Castrado", key=f"cast_{perfil_nome}")
            with c_chip: p_chipado = st.checkbox("💾 Chipado", key=f"chip_{perfil_nome}")
            p_vacinas = st.multiselect("💉 Vacinas", ["V8/V10", "Antirrábica", "Gripe", "V4/V5"], key=f"vac_{perfil_nome}")
            p_foto = st.file_uploader("📷 Foto", type=["jpg", "png", "jpeg"], key=f"foto_{perfil_nome}")
        
        with col2:
            st.write("### 👤 Contato")
            nome_resp = st.text_input("Responsável")
            p_local = st.text_input("Bairro/Cidade")
            p_tel = st.text_input("WhatsApp (DDD+Número)")
            p_insta = st.text_input("Instagram")
            p_email = st.text_input("E-mail")
            
        if st.form_submit_button("✅ Salvar Registro"):
            if p_nome and p_tel:
                try:
                    url_foto = None
                    if p_foto:
                        img = Image.open(p_foto).convert("RGB")
                        img.thumbnail((500, 500))
                        buf = BytesIO()
                        img.save(buf, format="JPEG", quality=60)
                        nome_arq = f"pet_{uuid.uuid4()}.jpg"
                        supabase.storage.from_("arquivos-pets").upload(nome_arq, buf.getvalue(), {"content-type": "image/jpeg"})
                        url_foto = supabase.storage.from_("arquivos-pets").get_public_url(nome_arq)

                    dados = {
                        "nome": p_nome,
                        "especie": p_especie,
                        "idade": f"{perfil_nome}: {entidade_nome if entidade_nome else nome_resp}",
                        "status": f"TEL:{p_tel}|INSTA:{p_insta}|EMAIL:{p_email}|LOCAL:{p_local}|SAUDE:Castrado:{p_castrado},Chip:{p_chipado},Vacinas:{','.join(p_vacinas)}",
                        "foto_url": url_foto
                    }
                    supabase.table("pets").insert(dados).execute()
                    st.success("Cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

with aba_protetor: processar_cadastro("Protetor", "")
with aba_ong: processar_cadastro("ONG", st.text_input("Nome da ONG"))
with aba_lojista: processar_cadastro("Lojista", st.text_input("Nome da Loja"))

st.divider()

# --- MURAL DE PETS ---
st.subheader("📋 Mural de Pets")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 3, 1.2, 0.8])
            status_raw = pet.get('status', '')
            info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
            with c1:
                if pet.get('foto_url'): st.image(pet['foto_url'], use_container_width=True)
            with c2:
                st.markdown(f'<div class="badge-perfil">{pet.get("idade", "Resgate")}</div>', unsafe_allow_html=True)
                st.write(f"### {pet['nome'].upper()}")
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 10px; text-decoration: none; border-radius: 5px; font-weight: bold;">💬 Testar Link Zap</a>', unsafe_allow_html=True)
            with c3:
                link_p = f"https://guardiao-pet-sp.streamlit.app/?id={pet['id']}"
                st.image(qrcode.make(link_p).tobitmap(), width=100, caption="QR Code")
            with c4:
                if st.button("🗑️", key=f"del_{pet['id']}"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()