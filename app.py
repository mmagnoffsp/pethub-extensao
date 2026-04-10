import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid
import urllib.parse
import re

# --- FUNÇÃO AUXILIAR PARA WHATSAPP (AGORA COM LINK DO SITE) ---
def criar_link_whatsapp(telefone, nome_pet, pet_id):
    # Remove tudo que não for número
    numero_limpo = re.sub(r'\D', '', telefone)
    # Garante que tem o código do país (Brasil = 55)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    
    # URL do seu sistema para este pet específico
    link_site = f"https://guardiao-pet-sp.streamlit.app/?id={pet_id}"
    
    # Mensagem personalizada incluindo o link
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP ({link_site}) e gostaria de entrar em contato."
    mensagem_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_url}"

# --- CONEXÃO SEGURA ---
try:
    URL = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
except Exception:
    URL = "https://bqawbkibffppaswlwsgr.supabase.co"
    key = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(URL, key)

st.set_page_config(page_title="Guardião Pet SP", layout="wide", page_icon="🐾")

# --- ESTILIZAÇÃO CUSTOMIZADA ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .stExpander { border: 1px solid #FF9800; }
    .whatsapp-btn {
        background-color: #25D366;
        color: white;
        padding: 10px;
        text-align: center;
        text-decoration: none;
        display: block;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 5px;
    }
    .badge-perfil {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        color: white;
        background-color: #FF9800;
        margin-bottom: 5px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 São Paulo - Brasil")
st.subheader("Plataforma de Identificação e Adoção")

# --- SELEÇÃO DE PERFIL ---
st.info("Escolha seu perfil abaixo para abrir o formulário correto.")
aba_protetor, aba_ong, aba_lojista = st.tabs([
    "🦸 Protetor Independente", 
    "🏢 ONG / Instituição", 
    "🏪 Lojista Parceiro"
])

# Função para processar o cadastro
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
            p_foto = st.file_uploader("📷 Foto", type=["jpg", "png", "jpeg"], key=f"foto_{perfil_nome}")
        
        with col2:
            st.write("### 👤 Dados de Contato")
            if perfil_nome == "Protetor Independente":
                nome_responsavel = st.text_input("Seu Nome")
            else:
                nome_responsavel = st.text_input("Nome do Responsável / Contato")
            
            p_local = st.text_input("🏠 Endereço/Bairro onde o Pet está")
            p_tel = st.text_input("📞 WhatsApp (com DDD)")
            p_insta = st.text_input("📸 Instagram (ex: @usuario)")
            p_email = st.text_input("📧 E-mail")
            
        btn = st.form_submit_button(f"✅ Cadastrar como {perfil_nome}")
        
        if btn and p_nome:
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
                    "idade": f"{perfil_nome}: {entidade_nome if entidade_nome else nome_responsavel}",
                    "status": f"TEL:{p_tel}|INSTA:{p_insta}|EMAIL:{p_email}|LOCAL:{p_local}|SAUDE:Castrado:{p_castrado},Chip:{p_chipado},Vacinas:{','.join(p_vacinas)}",
                    "foto_url": url_foto
                }
                supabase.table("pets").insert(dados).execute()
                st.success("Cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# Renderização das Abas
with aba_protetor:
    st.write("Para quem resgatou um pet e busca um lar.")
    processar_cadastro("Protetor Independente", "")

with aba_ong:
    nome_da_ong = st.text_input("Nome da ONG/Instituição", placeholder="Ex: Patinhas Unidas")
    processar_cadastro("ONG", nome_da_ong)

with aba_lojista:
    nome_da_loja = st.text_input("Nome do Pet Shop / Clínica", placeholder="Ex: Pet Shop da Praça")
    processar_cadastro("Lojista Parceiro", nome_da_loja)

st.markdown("---")

# --- MURAL ---
st.subheader("📋 Mural de Adoção e Identificação")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 3, 1.2, 0.8])
            
            # Extração de dados
            status_raw = pet.get('status', '')
            info = {p.split(":",1)[0]: p.split(":",1)[1] for p in status_raw.split("|") if ":" in p}

            with c1:
                if pet.get('foto_url'): st.image(pet['foto_url'], use_container_width=True)
                else: st.info("Sem foto")
            
            with c2:
                st.markdown(f'<div class="badge-perfil">{pet.get("idade", "Resgate")}</div>', unsafe_allow_html=True)
                st.write(f"### {pet['nome'].upper()} ({pet['especie']})")
                st.write(f"🏠 **Onde está:** {info.get('LOCAL', 'N/A')}")
                
                if info.get('INSTA'):
                    insta_limpo = info['INSTA'].replace('@', '')
                    st.markdown(f"📸 [Instagram @{insta_limpo}](https://instagram.com/{insta_limpo})")
                
                tel = info.get('TEL', '')
                if tel:
                    # AGORA ENVIANDO O ID PARA INCLUIR NO LINK DO WHATSAPP
                    link_wa = criar_link_whatsapp(tel, pet['nome'], pet['id'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">💬 Falar com Responsável</a>', unsafe_allow_html=True)

            with c3:
                link_pet = f"https://guardiao-pet-sp.streamlit.app/?id={pet['id']}"
                qr = qrcode.make(link_pet)
                buf_qr = BytesIO()
                qr.save(buf_qr, format="PNG")
                st.image(buf_qr.getvalue(), width=110, caption="QR Code do Pet")
                st.download_button("💾 Baixar", buf_qr.getvalue(), f"qr_{pet['id']}.png", key=f"q_{pet['id']}")
            
            with c4:
                if st.button("🗑️", key=f"d_{pet['id']}", help="Remover"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()
else:
    st.info("Nenhum pet cadastrado.")