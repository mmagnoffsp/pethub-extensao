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

# --- CONEXÃO COM O BANCO (SEGURA) ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["connections"]["supabase"]["url"]
        key = st.secrets["connections"]["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        st.error("⚠️ Erro de Configuração: Chaves de conexão não encontradas no Secrets.")
        st.stop()

supabase = init_connection()

# --- FUNÇÕES DE SEGURANÇA E UTILITÁRIOS ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def criar_link_whatsapp(telefone, nome_pet, pet_id):
    numero_limpo = re.sub(r'\D', '', telefone)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    link_site = f"https://guardiaopet-sp.streamlit.app/?id={pet_id}"
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e quero mais informações: {link_site}"
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

# --- 🎯 ROTEAMENTO PÚBLICO (VISTA DO ADOTANTE) ---
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
            with col_info:
                st.markdown(f"# 🐾 {pet['nome'].upper()}")
                st.markdown(f"**Espécie:** {pet.get('especie', 'Não informada')} | **Porte:** {pet.get('porte', 'Não informado')}")
                st.markdown(f"**Idade:** {pet.get('idade_animal', 'Não informada')} | **Cor:** {pet.get('cor', 'Não informada')}")
                st.markdown(f"💉 **Vacinas:** {pet.get('vacinas', 'Não informadas')}")
                st.markdown(f"**Responsável:** {pet.get('idade', 'Resgate Independente')}")
                
                status_raw = pet.get('status', '')
                info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
                
                st.write(f"📍 **Localização:** {info.get('LOCAL', 'São Paulo - SP')}")
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px; text-align: center; text-decoration: none; display: block; border-radius: 8px; font-weight: bold; font-size: 18px;">💬 Falar com o Protetor no WhatsApp</a>', unsafe_allow_html=True)
            st.stop() 
    except Exception:
        st.error("Erro ao carregar os dados.")

# --- 🔐 SISTEMA DE ACESSO (SIDEBAR) ---
if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.title("👤 Acesso Restrito")
    if not st.session_state.user:
        opcao = st.radio("Escolha:", ["Fazer Login", "Criar Conta"])
        u_login = st.text_input("Usuário").strip()
        u_senha = st.text_input("Senha", type="password")
        
        if opcao == "Fazer Login":
            if st.button("Entrar"):
                res_u = supabase.table("usuarios").select("*").eq("login", u_login).eq("senha", hash_senha(u_senha)).execute()
                if res_u.data:
                    st.session_state.user = res_u.data[0]
                    st.rerun()
                else:
                    st.error("Login ou senha inválidos.")
        else:
            u_tipo = st.selectbox("Perfil:", ["Protetor", "ONG", "Lojista"])
            if st.button("Confirmar Cadastro"):
                if u_login and u_senha:
                    try:
                        supabase.table("usuarios").insert({
                            "login": u_login, 
                            "senha": hash_senha(u_senha), 
                            "tipo": u_tipo
                        }).execute()
                        st.success("Conta criada! Mude para 'Fazer Login'.")
                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            st.error(f"O usuário '{u_login}' já está cadastrado.")
                        else:
                            st.error(f"Erro ao cadastrar: {e}")
        st.divider()
        st.markdown("### 📲 Divulgue o Projeto")
        url_site = "https://guardiaopet-sp.streamlit.app"
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={url_site}"
        st.image(qr_api_url, use_container_width=True)
    else:
        st.write(f"Olá, **{st.session_state.user['login']}**")
        if st.button("Sair"):
            st.session_state.user = None
            st.rerun()

# --- 🏠 PAINEL DE CADASTRO ---
st.title("🐾 Guardião Pet SP")

if not st.session_state.user:
    st.warning("⚠️ Use a barra lateral para fazer login ou criar conta.")
else:
    v_caes = "V8/V10, Raiva, Gripe, Giárdia"
    v_gatos = "V3/V4/V5, Raiva"

    with st.expander("➕ Cadastrar Pet", expanded=True):
        c_esp, c_blank = st.columns([1, 1])
        with c_esp:
            especie_p = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
        
        sugestao = v_caes if especie_p == "Cachorro" else v_gatos if especie_p == "Gato" else ""

        with st.form("form_novo_pet", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome_p = st.text_input("Nome do Animal")
                idade_p = st.text_input("Idade (ex: 2 anos, filhote)")
                cor_p = st.text_input("Cor/Pelagem")
                porte_p = st.selectbox("Porte", ["Pequeno", "Médio", "Grande"])
                foto_p = st.file_uploader("📷 Foto", type=["jpg", "png", "jpeg"])
            with c2:
                tel_p = st.text_input("WhatsApp (com DDD)")
                local_p = st.text_input("Bairro/Local")
                vacinas_p = st.text_area("Vacinas", value=sugestao)
            
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
                            "especie": especie_p,
                            "porte": porte_p,
                            "idade_animal": idade_p,
                            "cor": cor_p,
                            "vacinas": vacinas_p,
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

if "edit_pet_id" not in st.session_state:
    st.session_state.edit_pet_id = None

try:
    res_mural = supabase.table("pets").select("*").order("id", desc=True).execute()

    if res_mural.data:
        for p in res_mural.data:
            with st.container(border=True):
                if st.session_state.edit_pet_id == p['id']:
                    st.markdown(f"### 📝 Editando: {p['nome']}")
                    with st.form(key=f"edit_form_{p['id']}"):
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            edit_nome = st.text_input("Nome", value=p['nome'])
                            edit_idade_animal = st.text_input("Idade", value=p.get('idade_animal', ''))
                            edit_cor = st.text_input("Cor", value=p.get('cor', ''))
                            edit_especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"], 
                                                      index=["Cachorro", "Gato", "Outro"].index(p.get('especie', 'Cachorro')))
                            edit_porte = st.selectbox("Porte", ["Pequeno", "Médio", "Grande"],
                                                     index=["Pequeno", "Médio", "Grande"].index(p.get('porte', 'Médio')))
                        with col_ed2:
                            edit_vacinas = st.text_area("Vacinas", value=p.get('vacinas', ''))
                            edit_status = st.text_input("Status (Metadados)", value=p.get('status', ''))
                        
                        b_col1, b_col2 = st.columns(2)
                        if b_col1.form_submit_button("💾 Salvar Alterações"):
                            dados_update = {
                                "nome": edit_nome,
                                "especie": edit_especie,
                                "porte": edit_porte,
                                "idade_animal": edit_idade_animal,
                                "cor": edit_cor,
                                "vacinas": edit_vacinas,
                                "status": edit_status
                            }
                            supabase.table("pets").update(dados_update).eq("id", p['id']).execute()
                            st.session_state.edit_pet_id = None
                            st.success("Pet atualizado!")
                            st.rerun()
                        if b_col2.form_submit_button("❌ Cancelar"):
                            st.session_state.edit_pet_id = None
                            st.rerun()
                else:
                    col1, col2, col3, col4 = st.columns([1.5, 3, 1.2, 0.8])
                    raw = p.get('status', '')
                    meta = {item.split(":",1)[0]: item.split(":",1)[1] for item in raw.split("|") if ":" in item}
                    dono = meta.get('DONO', '')

                    with col1:
                        if p.get('foto_url'): 
                            st.image(p['foto_url'], use_container_width=True)
                    with col2:
                        st.write(f"### {p['nome'].upper()}")
                        st.write(f"🐾 **{p.get('especie', 'PET')}** ({p.get('porte', 'Não informado')})")
                        st.write(f"🎨 **Cor:** {p.get('cor', 'Não informada')} | 🎂 **Idade:** {p.get('idade_animal', 'Não informada')}")
                        st.write(f"💉 **Vacinas:** {p.get('vacinas', 'Não informadas')}")
                        st.write(f"📍 {meta.get('LOCAL', 'São Paulo')}")
                    with col3:
                        link_ind = f"https://guardiaopet-sp.streamlit.app/?id={p['id']}"
                        qr = qrcode.make(link_ind)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        st.image(buf.getvalue(), width=90, caption="Ficha do Pet")
                    with col4:
                        if st.session_state.user:
                            if st.session_state.user['login'] == dono or st.session_state.user['tipo'] == "ADMIN":
                                if st.button("📝", key=f"btn_edit_{p['id']}"):
                                    st.session_state.edit_pet_id = p['id']
                                    st.rerun()
                                if st.button("🗑️", key=f"btn_del_{p['id']}"):
                                    supabase.table("pets").delete().eq("id", p['id']).execute()
                                    st.rerun()
    else:
        st.info("Nenhum pet cadastrado no momento.")
except Exception as e:
    st.error(f"Erro ao carregar o mural: {e}")