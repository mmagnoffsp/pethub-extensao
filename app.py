import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client

# Configurações de Conexão (Suas chaves oficiais)
URL = "https://bqawbkibffppaswlwsgr.supabase.co"
KEY = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"
supabase: Client = create_client(URL, KEY)

# Configuração visual da página
st.set_page_config(page_title="Guardião Pet SP", page_icon="🐾")

st.title("🐾 Painel Guardião Pet SP")
st.markdown("---")

# --- BARRA LATERAL (CADASTRO) ---
st.sidebar.header("📝 Cadastrar Novo Pet")
with st.sidebar.form("form_pet"):
    nome = st.text_input("Nome do Pet")
    especie = st.selectbox("Espécie", ["Cachorro", "Gato", "Outro"])
    idade = st.text_input("Idade (ex: 2 anos)")
    enviar = st.form_submit_button("Salvar e Gerar QR Code")

if enviar and nome:
    try:
        # 1. Salvar no Banco de Dados Supabase
        dados = {"nome": nome, "especie": especie, "idade": idade}
        supabase.table("pets").insert(dados).execute()
        
        # 2. Gerar QR Code para exibir na tela
        conteudo = f"Guardião Pet SP\nPet: {nome}\nEspécie: {especie}\nIdade: {idade}\nStatus: Disponível"
        qr_img = qrcode.make(conteudo)
        
        # Converte a imagem para o Streamlit mostrar
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        
        st.sidebar.success(f"✅ {nome} cadastrado!")
        st.sidebar.image(buf, caption=f"QR Code de {nome}")
    except Exception as e:
        st.sidebar.error(f"Erro: {e}")

# --- LISTAGEM DE PETS (Centro da Tela) ---
st.subheader("📋 Animais em Busca de um Lar")
try:
    resposta = supabase.table("pets").select("*").execute()
    if resposta.data:
        for pet in resposta.data:
            with st.expander(f"🐾 {pet['nome'].upper()} - {pet['especie']}"):
                st.write(f"**Idade:** {pet['idade']}")
                st.write("📍 Localização: Vila Esperança / Penha")
    else:
        st.info("Nenhum pet cadastrado ainda.")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")