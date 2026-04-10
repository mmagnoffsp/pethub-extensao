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

# --- UTILITÁRIOS ---
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
                st.markdown(f"**Espécie:** {pet.get('especie', 'Não informada')} | **Raça:** {pet.get('raca', 'SRD')}")
                st.markdown(f"**Porte:** {pet.get('porte', 'Não informado')} | **Cor:** {pet.get('cor', 'Não informada')}")
                st.markdown(f"**Idade:** {pet.get('idade_animal', 'Não informada')}")
                st.markdown(f"💉 **Vacinas:** {pet.get('vacinas', 'Não informadas')}")
                st.markdown(f"🏠 **Local de Resgate:** {pet.get('local_resgate', 'Não informado')}")
                st.markdown(f"📍 **Onde está:** {pet.get('bairro', 'Não informado')} - {pet.get('cidade', 'São Paulo')}/{pet.get('uf', 'SP')}")
                
                status_raw = pet.get('status', '')
                info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px; text-align: center; text-decoration: none; display: block; border-radius: 8px; font-weight: bold; font-size: 18px;">💬 Falar com o Protetor no WhatsApp</a>', unsafe_allow_html=True)
            st.stop() 
    except Exception:
        st.error("Erro ao carregar os dados.")

# --- 🔐 SISTEMA DE ACESSO ---
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
        c_esp, c_raca_col = st.columns([1, 1])
        with c_esp:
            especie_p = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
        with c_raca_col:
            raca_p = st.text_input("Raça", placeholder="Ex: SRD, Poodle, Siamês...")
        
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
                resgate_p = st.text_input("Local de Resgate (Onde foi achado?)")
                bairro_p = st.text_input("Bairro Atual")
                c_cidade, c_uf = st.columns([3, 1])
                cidade_p = c_cidade.text_input("Cidade", value="São Paulo")
                uf_p = c_uf.text_input("UF", value="SP")
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
                            "nome": nome_p, "especie": especie_p, "raca": raca_p, "porte": porte_p,
                            "idade_animal": idade_p, "cor": cor_p, "vacinas": vacinas_p,
                            "local_resgate": resgate_p, "bairro": bairro_p, "cidade": cidade_p, "uf": uf_p,
                            "idade": f"{st.session_state.user['tipo']}: {st.session_state.user['login']}",
                            "status": f"TEL:{tel_p}|LOCAL:{bairro_p}|DONO:{st.session_state.user['login']}",
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
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                            en = st.text_input("Nome", value=p['nome'])
                            er = st.text_input("Raça", value=p.get('raca', ''))
                            ei = st.text_input("Idade", value=p.get('idade_animal', ''))
                            ecor = st.text_input("Cor", value=p.get('cor', ''))
                            ev = st.text_area("Vacinas", value=p.get('vacinas', ''))
                        with e_col2:
                            elr = st.text_input("Local Resgate", value=p.get('local_resgate', ''))
                            eb = st.text_input("Bairro", value=p.get('bairro', ''))
                            ec = st.text_input("Cidade", value=p.get('cidade', ''))
                            euf = st.text_input("UF", value=p.get('uf', ''))
                            estatus = st.text_input("Status (Meta)", value=p.get('status', ''))
                        
                        if st.form_submit_button("💾 Salvar Alterações"):
                            upd = {
                                "nome":en, "raca":er, "idade_animal":ei, "cor":ecor, 
                                "vacinas":ev, "local_resgate":elr, "bairro":eb, 
                                "cidade":ec, "uf":euf, "status":estatus
                            }
                            supabase.table("pets").update(upd).eq("id", p['id']).execute()
                            st.session_state.edit_pet_id = None
                            st.rerun()
                        if st.form_submit_button("❌ Cancelar"):
                            st.session_state.edit_pet_id = None
                            st.rerun()
                else:
                    col1, col2, col3, col4 = st.columns([1.5, 3, 1.2, 0.8])
                    meta = {item.split(":",1)[0]: item.split(":",1)[1] for item in p.get('status','').split("|") if ":" in item}
                    dono = meta.get('DONO', '')

                    with col1:
                        if p.get('foto_url'): st.image(p['foto_url'], use_container_width=True)
                    with col2:
                        st.write(f"### {p['nome'].upper()}")
                        st.write(f"🧬 **Raça:** {p.get('raca', 'SRD')} | 🐾 **{p.get('especie', 'PET')}** ({p.get('porte', 'Não informado')})")
                        st.write(f"🎨 **Cor:** {p.get('cor', 'Não informada')} | 🎂 **Idade:** {p.get('idade_animal', 'Não informada')}")
                        st.write(f"💉 **Vacinas:** {p.get('vacinas', 'Não informadas')}")
                        st.write(f"🏠 **Resgate:** {p.get('local_resgate', 'Não informado')}")
                        st.write(f"📍 **Bairro:** {p.get('bairro', 'Não informado')} ({p.get('cidade', 'SP')}/{p.get('uf', 'SP')})")
                    with col3:
                        qr = qrcode.make(f"https://guardiaopet-sp.streamlit.app/?id={p['id']}")
                        buf = BytesIO(); qr.save(buf, format="PNG")
                        st.image(buf.getvalue(), width=90, caption="Ficha do Pet")
                    with col4:
                        if st.session_state.user and (st.session_state.user['login'] == dono or st.session_state.user.get('tipo') == "ADMIN"):
                            if st.button("📝", key=f"btn_edit_{p['id']}"):
                                st.session_state.edit_pet_id = p['id']
                                st.rerun()
                            if st.button("🗑️", key=f"btn_del_{p['id']}"):
                                supabase.table("pets").delete().eq("id", p['id']).execute()
                                st.rerun()
    else:
        st.info("Nenhum pet cadastrado.")
except Exception as e:
    st.error(f"Erro no mural: {e}")