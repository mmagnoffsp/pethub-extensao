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

# --- CONEXÃO COM O BANCO ---
try:
    URL = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
except Exception:
    # Fallback caso os secrets não estejam carregados localmente
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    key = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, key)

# --- FUNÇÕES DE SEGURANÇA E UTILITÁRIOS ---
def hash_senha(senha):
    """Criptografa a senha para segurança no banco de dados."""
    return hashlib.sha256(str.encode(senha)).hexdigest()

def criar_link_whatsapp(telefone, nome_pet, pet_id):
    """Gera link direto para o WhatsApp com mensagem personalizada."""
    numero_limpo = re.sub(r'\D', '', telefone)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    
    link_site = f"https://guardiaopet-sp.streamlit.app/?id={pet_id}"
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e quero mais informações: {link_site}"
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

# --- 🎯 ROTEAMENTO PÚBLICO (VISTA DO ADOTANTE) ---
# Esta parte roda primeiro. Se houver um ID na URL, mostra apenas o pet.
query_params = st.query_params
if "id" in query_params:
    pet_id_url = query_params["id"]
    try:
        res_pet = supabase.table("pets").select("*").eq("id", pet_id_url).execute()
        if res_pet.data:
            pet = res_pet.data[0]
            if st.button("⬅️ Ver todos os pets no Mural"):
                st.query_params.clear()
                st.rerun()
                
            st.divider()
            col_img, col_info = st.columns([1, 1.2])
            
            with col_img:
                if pet.get('foto_url'):
                    st.image(pet['foto_url'], use_container_width=True)
                else:
                    st.info("Pet sem foto disponível.")
            
            with col_info:
                st.markdown(f"# 🐾 {pet['nome'].upper()}")
                st.markdown(f"**Responsável:** {pet.get('idade', 'Resgate Independente')}")
                
                status_raw = pet.get('status', '')
                info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
                
                st.write(f"📍 **Localização:** {info.get('LOCAL', 'São Paulo - SP')}")
                
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f"""
                        <a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px; text-align: center; text-decoration: none; display: block; border-radius: 8px; font-weight: bold; font-size: 18px;">
                            💬 Falar com o Protetor no WhatsApp
                        </a>
                    """, unsafe_allow_html=True)
            st.stop() # Bloqueia o restante da página para o adotante
    except Exception:
        st.error("Erro ao carregar os dados deste pet.")

# --- 🔐 SISTEMA DE ACESSO (SIDEBAR) ---
if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.title("👤 Acesso Restrito")
    if not st.session_state.user:
        opcao = st.radio("Escolha:", ["Fazer Login", "Criar Conta"])
        u_login = st.text_input("Usuário")
        u_senha = st.text_input("Senha", type="password")
        
        if opcao == "Fazer Login":
            if st.button("Entrar"):
                # VERIFICAÇÃO DO ADMINISTRADOR (VOCÊ)
                if u_login == "admin" and u_senha == "cmmf2026":
                    st.session_state.user = {"login": "admin", "tipo": "ADMIN"}
                    st.rerun()
                
                # VERIFICAÇÃO DE USUÁRIOS COMUNS (ONG/LOJISTA/PROTETOR)
                res_u = supabase.table("usuarios").select("*").eq("login", u_login).eq("senha", hash_senha(u_senha)).execute()
                if res_u.data:
                    st.session_state.user = res_u.data[0]
                    st.rerun()
                else:
                    st.error("Login ou senha inválidos.")
        else:
            u_tipo = st.selectbox("Perfil:", ["Protetor", "ONG", "Lojista"])
            if st.button("Cadastrar"):
                if u_login and u_senha:
                    try:
                        supabase.table("usuarios").insert({
                            "login": u_login, 
                            "senha": hash_senha(u_senha), 
                            "tipo": u_tipo
                        }).execute()
                        st.success("Conta criada! Agora faça o login.")
                    except:
                        st.error("Este usuário já existe.")
    else:
        st.write(f"Olá, **{st.session_state.user['login']}**")
        st.write(f"Nível: {st.session_state.user['tipo']}")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

# --- 🏠 PAINEL DE CADASTRO ---
st.title("🐾 Guardião Pet SP")

if not st.session_state.user:
    st.warning("⚠️ Use a barra lateral para fazer login e cadastrar novos pets.")
    st.info("Adotantes podem acessar as fichas diretamente via link ou QR Code.")
else:
    # FORMULÁRIO DE CADASTRO
    with st.expander("➕ Cadastrar Pet", expanded=True):
        with st.form("form_novo_pet", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome_p = st.text_input("Nome do Animal")
                foto_p = st.file_uploader("📷 Foto", type=["jpg", "png", "jpeg"])
            with c2:
                tel_p = st.text_input("WhatsApp (com DDD)")
                local_p = st.text_input("Bairro/Local")
            
            if st.form_submit_button("✅ Salvar Cadastro"):
                if nome_p and tel_p:
                    try:
                        url_img = None
                        if foto_p:
                            nome_arquivo = f"pet_{uuid.uuid4()}.jpg"
                            supabase.storage.from_("arquivos-pets").upload(nome_arquivo, foto_p.read(), {"content-type": "image/jpeg"})
                            url_img = supabase.storage.from_("arquivos-pets").get_public_url(nome_arquivo)

                        dados = {
                            "nome": nome_p,
                            "idade": f"{st.session_state.user['tipo']}: {st.session_state.user['login']}",
                            "status": f"TEL:{tel_p}|LOCAL:{local_p}|DONO:{st.session_state.user['login']}",
                            "foto_url": url_img
                        }
                        supabase.table("pets").insert(dados).execute()
                        st.success("Pet cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# --- 📋 MURAL DE PETS ---
st.divider()
st.subheader("📋 Mural de Adoção")

res_mural = supabase.table("pets").select("*").order("id", desc=True).execute()

if res_mural.data:
    for p in res_mural.data:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1.5, 3, 1.2, 0.8])
            
            # Extrair metadados do campo 'status'
            raw = p.get('status', '')
            meta = {item.split(":",1)[0]: item.split(":",1)[1] for item in raw.split("|") if ":" in item}
            dono = meta.get('DONO', '')

            with col1:
                if p.get('foto_url'):
                    st.image(p['foto_url'], use_container_width=True)
            with col2:
                st.write(f"### {p['nome'].upper()}")
                st.write(f"**Responsável:** {p['idade']}")
                st.write(f"📍 {meta.get('LOCAL', 'São Paulo')}")
            with col3:
                link_individual = f"https://guardiaopet-sp.streamlit.app/?id={p['id']}"
                st.image(qrcode.make(link_individual).tobitmap(), width=90, caption="QR Code")
            with col4:
                # PERMISSÃO PARA EXCLUIR:
                if st.session_state.user:
                    # Se for o dono OU se for você (ADMIN)
                    if st.session_state.user['login'] == dono or st.session_state.user['tipo'] == "ADMIN":
                        if st.button("🗑️", key=f"btn_del_{p['id']}"):
                            supabase.table("pets").delete().eq("id", p['id']).execute()
                            st.rerun()