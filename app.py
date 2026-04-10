import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid
import urllib.parse
import re

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
    
    # O link que o interessado vai clicar
    link_site = f"https://guardiao-pet-sp.streamlit.app/?id={pet_id}"
    
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP ({link_site}) e gostaria de mais informações."
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

st.set_page_config(page_title="Guardião Pet SP", layout="wide", page_icon="🐾")

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .whatsapp-btn {
        background-color: #25D366; color: white; padding: 12px;
        text-align: center; text-decoration: none; display: block;
        border-radius: 8px; font-weight: bold; margin-top: 10px;
    }
    .badge-perfil {
        padding: 4px 8px; border-radius: 4px; font-size: 12px;
        font-weight: bold; color: white; background-color: #FF9800;
        margin-bottom: 5px; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🎯 LÓGICA DE ROTEAMENTO (SOLUÇÃO PARA O CLIENTE) ---
# Esta parte intercepta o link do WhatsApp e mostra a ficha do pet
query_params = st.query_params
if "id" in query_params:
    pet_id_url = query_params["id"]
    res_pet = supabase.table("pets").select("*").eq("id", pet_id_url).execute()
    
    if res_pet.data:
        pet = res_pet.data[0]
        # Botão para voltar ao site principal
        if st.button("⬅️ Ver todos os pets disponíveis"):
            st.query_params.clear()
            st.rerun()
            
        st.divider()
        col_img, col_info = st.columns([1, 1.2])
        
        with col_img:
            if pet.get('foto_url'):
                st.image(pet['foto_url'], use_container_width=True)
            else:
                st.info("Este pet ainda não possui foto.")
        
        with col_info:
            st.markdown(f"# 🐾 Conheça o {pet['nome'].upper()}")
            st.markdown(f"**Responsável:** {pet.get('idade', 'Resgate Independente')}")
            
            # Extração de dados da string 'status'
            status_raw = pet.get('status', '')
            info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}
            
            st.write(f"📍 **Localização:** {info.get('LOCAL', 'Não informado')}")
            st.write(f"🩺 **Saúde:** {info.get('SAUDE', 'N/A').replace(',', ' | ')}")
            
            tel = info.get('TEL', '')
            if tel:
                link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">💬 Quero adotar / Saber mais</a>', unsafe_allow_html=True)
            
            if info.get('INSTA'):
                insta = info['INSTA'].replace('@', '')
                st.markdown(f"📸 [Instagram do Responsável](https://instagram.com/{insta})")
        
        st.stop() # Mata a execução aqui para o cliente não ver a tela de cadastro

# --- 🏠 TELA PRINCIPAL (ADMIN / CADASTRO) ---
st.title("🐾 Guardião Pet SP")
st.subheader("Plataforma de Identificação e Adoção")

st.info("Escolha seu perfil para realizar um novo cadastro:")
aba_protetor, aba_ong, aba_lojista = st.tabs(["🦸 Protetor Independente", "🏢 ONG", "🏪 Lojista Parceiro"])

# Função de Cadastro Genérica
def processar_cadastro(perfil_nome, entidade_nome):
    with st.form(f"form_{perfil_nome}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 🐕 Dados do Pet")
            p_nome = st.text_input("Nome/Apelido do Pet")
            p_especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"], key=f"esp_{perfil_nome}")
            st.write("**Saúde:**")
            c_saude, c_chip = st.columns(2)
            with c_saude: p_castrado = st.checkbox("✂️ Castrado", key=f"cast_{perfil_nome}")
            with c_chip: p_chipado = st.checkbox("💾 Chipado", key=f"chip_{perfil_nome}")
            p_vacinas = st.multiselect("💉 Vacinas", ["V8/V10", "Antirrábica", "Gripe", "V4/V5"], key=f"vac_{perfil_nome}")
            p_foto = st.file_uploader("📷 Foto do Pet", type=["jpg", "png", "jpeg"], key=f"foto_{perfil_nome}")
        
        with col2:
            st.write("### 👤 Dados de Contato")
            nome_resp = st.text_input("Nome do Responsável")
            p_local = st.text_input("🏠 Bairro/Cidade onde o Pet está")
            p_tel = st.text_input("📞 WhatsApp (com DDD)")
            p_insta = st.text_input("📸 Instagram (ex: @usuario)")
            p_email = st.text_input("📧 E-mail")
            
        btn = st.form_submit_button(f"✅ Salvar Registro")
        
        if btn and p_nome and p_tel:
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
                st.success("✅ Pet cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

with aba_protetor:
    processar_cadastro("Protetor", "")
with aba_ong:
    ong_nome = st.text_input("Nome da ONG/Instituição")
    processar_cadastro("ONG", ong_nome)
with aba_lojista:
    loja_nome = st.text_input("Nome do Estabelecimento")
    processar_cadastro("Lojista", loja_nome)

st.divider()

# --- MURAL DE PETS ---
st.subheader("📋 Pets Registrados no Sistema")
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
                st.write(f"📍 {info.get('LOCAL', 'N/A')}")
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">💬 Contato WhatsApp</a>', unsafe_allow_html=True)
            with c3:
                link_p = f"https://guardiao-pet-sp.streamlit.app/?id={pet['id']}"
                qr_img = qrcode.make(link_p)
                buf_qr = BytesIO()
                qr_img.save(buf_qr, format="PNG")
                st.image(buf_qr.getvalue(), width=110)
            with c4:
                if st.button("🗑️", key=f"del_{pet['id']}"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()
else:
    st.info("Nenhum pet cadastrado no momento.")