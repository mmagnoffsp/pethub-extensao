import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
from PIL import Image
import uuid
import urllib.parse
import re

# --- FUNÇÃO AUXILIAR PARA WHATSAPP ---
def criar_link_whatsapp(telefone, nome_pet):
    # Remove tudo que não for número
    numero_limpo = re.sub(r'\D', '', telefone)
    # Garante que tem o código do país (Brasil = 55)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
    
    mensagem = f"Olá! Vi o pet {nome_pet} no Guardião Pet SP e gostaria de entrar em contato."
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
    </style>
    """, unsafe_allow_html=True)

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
            telefone = st.text_input("📞 Telefone / WhatsApp (ex: 11999999999)")
            instagram = st.text_input("📸 Instagram (ex: @usuario)")
            
        btn_salvar = st.form_submit_button("✅ Salvar no Guardião Pet")

    if btn_salvar and nome:
        try:
            url_publica_foto = None
            
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

            # --- ORGANIZAÇÃO DOS DADOS NO BANCO ---
            # Guardamos o telefone bruto no campo status para processar no mural
            dados = {
                "nome": nome, 
                "especie": especie, 
                "idade": endereco, 
                "status": f"TEL:{telefone}|INSTA:{instagram}|EMAIL:{email}|SAUDE:Castrado:{castrado},Chip:{chipado},Vacinas:{','.join(vacinas_sel)}",
                "foto_url": url_publica_foto
            }
            
            supabase.table("pets").insert(dados).execute()
            st.success(f"🐾 {nome} cadastrado com sucesso!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

st.markdown("---")

# --- MURAL DE PETS ---
st.subheader("📋 Pets Registrados")
res = supabase.table("pets").select("*").order("id", desc=True).execute()

if res.data:
    for pet in res.data:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 3, 1.2, 0.8])
            
            # Extração de dados da string 'status'
            status_raw = pet.get('status', '')
            info = {}
            if "|" in status_raw:
                parts = status_raw.split("|")
                for p in parts:
                    if ":" in p:
                        key_val = p.split(":", 1)
                        info[key_val[0]] = key_val[1]

            with c1:
                if pet.get('foto_url'):
                    st.image(pet['foto_url'], use_container_width=True)
                else:
                    st.info("Sem foto")
            
            with c2:
                st.write(f"### {pet['nome'].upper()} ({pet['especie']})")
                st.write(f"🏠 **Local:** {pet.get('idade', 'N/A')}")
                
                # Exibição do Instagram clicável
                insta = info.get('INSTA', '').replace('@', '')
                if insta:
                    st.markdown(f"📸 **Instagram:** [@{insta}](https://instagram.com/{insta})")
                
                # BOTÃO WHATSAPP DIRETO
                tel = info.get('TEL', '')
                if tel:
                    link_wa = criar_link_whatsapp(tel, pet['nome'])
                    st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">💬 Chamar no WhatsApp</a>', unsafe_allow_html=True)
                
                # Informações de Saúde compactas
                saude = info.get('SAUDE', 'N/A')
                with st.expander("🩺 Ver Detalhes de Saúde"):
                    st.write(saude.replace(',', ' | '))

            with c3:
                link_pet = f"https://guardiao-pet-sp.streamlit.app/?id={pet['id']}"
                qr = qrcode.make(link_pet)
                buf_qr = BytesIO()
                qr.save(buf_qr, format="PNG")
                st.image(buf_qr.getvalue(), width=120, caption="QR Code ID")
                st.download_button("💾 Baixar QR", buf_qr.getvalue(), f"qr_{pet['id']}.png", key=f"q_{pet['id']}")
            
            with c4:
                st.write("---")
                if st.button("🗑️", key=f"d_{pet['id']}", help="Deletar Registro"):
                    supabase.table("pets").delete().eq("id", pet['id']).execute()
                    st.rerun()
else:
    st.info("Nenhum pet no mural.")