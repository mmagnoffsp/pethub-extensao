import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid
import urllib.parse
import re
import hashlib

# --- CONFIGURAÇÃO DA PÁGINA ---
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

# --- FUNÇÕES AUXILIARES ---
def hash_senha(senha):
    """Criptografa a senha para não salvar texto limpo no banco."""
    return hashlib.sha256(str.encode(senha)).hexdigest()

def criar_link_whatsapp(telefone, nome_pet, pet_id):
    numero_limpo = re.sub(r'\D', '', telefone)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    link_site = f"https://guardiaopet-sp.streamlit.app/?id={pet_id}"
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e quero mais informações: {link_site}"
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

# --- 🎯 ROTEAMENTO PÚBLICO (CLIENTE) ---
# Esta parte roda antes de tudo e não pede login
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
                if pet.get('foto_url'): st.image(pet['foto_url'], use_container_width=True)
            with col_info:
                st.markdown(f"# 🐾 {pet['nome'].upper()}")
                st.markdown(f"**Responsável:** {pet.get('idade', 'Resgate Independente')}")
                status_raw = pet.get('status', '')
                info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
                st.write(f"📍 **Localização:** {info.get('LOCAL', 'Não informado')}")
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px; text-align: center; text-decoration: none; display: block; border-radius: 8px; font-weight: bold; font-size: 18px;">💬 Falar com o Protetor no WhatsApp</a>', unsafe_allow_html=True)
            st.stop() # Interrompe aqui para o adotante não ver o painel de login
    except Exception:
        st.error("Erro ao carregar dados do pet.")

# --- 🔐 SISTEMA DE AUTENTICAÇÃO (SIDEBAR) ---
if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.title("👤 Área de Acesso")
    if not st.session_state.user:
        aba_auth = st.radio("Escolha uma opção:", ["Entrar", "Criar Nova Conta"])
        u_login = st.text_input("Usuário / Login")
        u_senha = st.text_input("Senha", type="password")
        
        if aba_auth == "Entrar":
            if st.button("Fazer Login"):
                # Login Especial do Administrador (Você)
                if u_login == "admin" and u_senha == "freitas2026":
                    st.session_state.user = {"login": "admin", "tipo": "ADMIN"}
                    st.success("Bem-vindo, Carlos!")
                    st.rerun()
                
                # Busca usuário comum no banco
                res_user = supabase.table("usuarios").select("*").eq("login", u_login).eq("senha", hash_senha(u_senha)).execute()
                if res_user.data:
                    st.session_state.user = res_user.data[0]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        else:
            u_tipo = st.selectbox("Tipo de Perfil", ["Protetor", "ONG", "Lojista"])
            if st.button("Confirmar Cadastro"):
                if u_login and u_senha:
                    try:
                        supabase.table("usuarios").insert({
                            "login": u_login, 
                            "senha": hash_senha(u_senha), 
                            "tipo": u_tipo
                        }).execute()
                        st.success("Conta criada! Agora mude para 'Entrar' e faça o login.")
                    except:
                        st.error("Este nome de usuário já existe.")
    else:
        st.write(f"Conectado como: **{st.session_state.user['login']}**")
        st.write(f"Perfil: **{st.session_state.user['tipo']}**")
        if st.button("Sair / Logout"):
            st.session_state.user = None
            st.rerun()

# --- 🏠 PAINEL DE CADASTRO (APENAS LOGADOS) ---
st.title("🐾 Guardião Pet SP")

if not st.session_state.user:
    st.warning("⚠️ Para cadastrar pets ou gerenciar anúncios, use a área de acesso na barra lateral esquerda.")
    st.info("O público interessado em adotar pode ver as fichas normalmente através dos links/QR Codes sem precisar de login.")
else:
    with st.expander("➕ Cadastrar Novo Pet para Adoção", expanded=True):
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_nome = st.text_input("Nome do Pet")
                p_especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
                p_foto = st.file_uploader("📷 Foto do Pet", type=["jpg", "png", "jpeg"])
            with col2:
                p_tel = st.text_input("WhatsApp para Contato")
                p_local = st.text_input("Bairro/Cidade")
            
            if st.form_submit_button("✅ Salvar Registro"):
                if p_nome and p_tel:
                    try:
                        url_foto = None
                        if p_foto:
                            nome_arq = f"pet_{uuid.uuid4()}.jpg"
                            supabase.storage.from_("arquivos-pets").upload(nome_arq, p_foto.read(), {"content-type": "image/jpeg"})
                            url_foto = supabase.storage.from_("arquivos-pets").get_public_url(nome_arq)

                        dados = {
                            "nome": p_nome,
                            "especie": p_especie,
                            "idade": f"{st.session_state.user['tipo']}: {st.session_state.user['login']}",
                            "status": f"TEL:{p_tel}|LOCAL:{p_local}|DONO:{st.session_state.user['login']}",
                            "foto_url": url_foto
                        }
                        supabase.table("pets").insert(dados).execute()
                        st.success("Pet cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- 📋 MURAL DE PETS ---
st.divider()
st.subheader("📋 Mural de Pets Registrados")
res_mural = supabase.table("pets").select("*").order("id", desc=True).execute()

if res_mural.data:
    for pet in res_mural.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 3, 1.2, 0.8])
            status_raw = pet.get('status', '')
            info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
            dono_login = info.get('DONO', '')

            with c1:
                if pet.get('foto_url'): st.image(pet['foto_url'], use_container_width=True)
            with c2:
                st.write(f"### {pet['nome'].upper()}")
                st.write(f"📌 {pet['idade']}")
                st.write(f"📍 {info.get('LOCAL', 'Não informado')}")
            with c3:
                link_p = f"https://guardiaopet-sp.streamlit.app/?id={pet['id']}"
                st.image(qrcode.make(link_p).tobitmap(), width=90, caption="QR Code")
            with c4:
                # Lógica de Permissão de Exclusão
                if st.session_state.user:
                    # Se for o dono do pet OU se for você (admin)
                    if st.session_state.user['login'] == dono_login or st.session_state.user['tipo'] == "ADMIN":
                        if st.button("🗑️", key=f"del_{pet['id']}"):
                            supabase.table("pets").delete().eq("id", pet['id']).execute()
                            st.rerun()