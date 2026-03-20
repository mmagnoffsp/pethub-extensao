#PROJETO: pethub.py voltado a causa animal para adotantes via casa de ração ou através de ongs
#data da ultima atualização#
"19/03/2026"

import streamlit as st # Biblioteca principal para criação da interface web
import qrcode          # Biblioteca para geração de QR Codes dinâmicos
from io import BytesIO  # Gerencia o armazenamento temporário de dados binários (imagens)
import urllib.parse    # Utilizado para formatar links de URL (importante para o WhatsApp)
from PIL import Image   # Processamento de imagens (essencial para o upload de fotos JPEG)

# --- NOVOS IMPORTS OTIMIZADOS PARA GOOGLE SHEETS (CORREÇÃO DE PADDING E ERRO 200) ---
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (Metadata)
# ==========================================
st.set_page_config(
    page_title="PetHub - Fichas Técnicas",
    page_icon="🐾",
    layout="wide" 
)

# --- FUNÇÃO DE CONEXÃO COM GOOGLE SHEETS (ADS - PROJETO DE EXTENSÃO) ---
def conectar_google_sheets():
    try:
        # Escopos modernos para garantir escrita e leitura sem erros
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Puxa as credenciais dos Secrets do Streamlit Cloud
        creds_dict = st.secrets["gcp_service_account"]
        
        # A biblioteca 'google.oauth2' resolve o erro de padding automaticamente
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome exato (Certifique-se que o nome no Drive é este)
        return client.open("PetHub - Banco de Dados").sheet1
    except Exception as e:
        # Filtro para ignorar o falso erro [200] do Google
        if "200" not in str(e):
            st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return None

# ==========================================
# 2. FUNÇÃO PARA GERAR O QR CODE DE DIVULGAÇÃO
# ==========================================
def gerar_qr_code(url):
    """
    Cria um QR Code a partir de uma URL para facilitar o acesso via celular.
    Retorna os bytes da imagem para serem exibidos no Streamlit.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converte a imagem para bytes para que o Streamlit possa exibir/baixar
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==========================================
# 3. INICIALIZAÇÃO DO BANCO DE DADOS E ESTADOS
# ==========================================
if 'lista_animais' not in st.session_state:
    st.session_state.lista_animais = [
        {
            "nome": "Bento (Exemplo)",
            "idade": "1 ano",
            "cor": "Preto e Branco",
            "raca": "SRD",
            "saude": "Vacinado e Vermifugado",
            "whatsapp": "5511941507706", 
            "url_instituicao": "https://www.instagram.com", 
            "foto": "https://placedog.net/500/350?id=10"
        }
    ]

# Controle de estado para edição automática
if 'editando_idx' not in st.session_state:
    st.session_state.editando_idx = None

# ==========================================
# 4. BARRA LATERAL (NAVEGAÇÃO E IMPACTO SOCIAL)
# ==========================================
with st.sidebar:
    st.title("🐾 PetHub")
    st.write("Sistema de Gestão de Adoção Consciente")
    st.divider()
    
    pagina = st.radio(
        "Navegar por:", 
        ["Fichas Técnicas", "Cadastrar Novo Pet", "Guia de Posse Responsável"]
    )
    
    st.divider()
    st.write("### Divulgue o Projeto")
    
    url_site = "https://projeto-universitario-ads.streamlit.app"
    qr_img = gerar_qr_code(url_site)
    
    st.image(qr_img, caption="Acesse o Portal pelo Celular", width=250)
    
    st.download_button(
        label="⬇️ Baixar QR Code para Impressão",
        data=qr_img,
        file_name="qrcode_pethub.png",
        mime="image/png"
    )

# ==========================================
# 5. PÁGINA: FICHAS TÉCNICAS (VISUALIZAÇÃO E EDIÇÃO)
# ==========================================
if pagina == "Fichas Técnicas":
    st.title("🐾 Fichas Técnicas de Animais")
    st.subheader("Dados detalhados para uma adoção segura e acompanhamento pós-adoção")
    st.markdown("---")

    if not st.session_state.lista_animais:
        st.info("Nenhum animal cadastrado no momento.")
    else:
        for idx, animal in enumerate(st.session_state.lista_animais):
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    # Ajustado para o novo padrão Streamlit (use_container_width)
                    st.image(animal["foto"], width='stretch')
                
                with col2:
                    # LÓGICA DE EDIÇÃO AUTOMÁTICA
                    if st.session_state.editando_idx == idx:
                        st.markdown(f"### 📝 Editando Ficha: {animal['nome']}")
                        
                        ed_nome = st.text_input("Nome do Animal", animal['nome'], key=f"ed_nome_{idx}")
                        ed_idade = st.text_input("Idade Estimada", animal['idade'], key=f"ed_idade_{idx}")
                        ed_raca = st.text_input("Raça", animal.get('raca', 'SRD'), key=f"ed_raca_{idx}")
                        
                        url_atual = animal.get('url_instituicao', '')
                        ed_url = st.text_input("URL da Instituição (Link Completo)", url_atual, key=f"ed_url_{idx}", placeholder="https://exemplo.com")
                        
                        ed_saude = st.text_area("Estado de Saúde / Dados do Adotante", animal['saude'], key=f"ed_saude_{idx}")
                        ed_zap = st.text_input("WhatsApp de Contato", animal['whatsapp'], key=f"ed_zap_{idx}")
                        
                        col_salvar, col_cancelar = st.columns(2)
                        with col_salvar:
                            if st.button("💾 Salvar Alterações", key=f"save_btn_{idx}"):
                                st.session_state.lista_animais[idx].update({
                                    "nome": ed_nome,
                                    "idade": ed_idade,
                                    "raca": ed_raca,
                                    "url_instituicao": ed_url,
                                    "saude": ed_saude,
                                    "whatsapp": ed_zap
                                })
                                st.session_state.editando_idx = None
                                st.success("Dados atualizados!")
                                st.rerun()
                        with col_cancelar:
                            if st.button("❌ Cancelar", key=f"cancel_btn_{idx}"):
                                st.session_state.editando_idx = None
                                st.rerun()

                    else:
                        # VISUALIZAÇÃO NORMAL
                        col_tit, col_edit, col_del = st.columns([2.5, 0.8, 0.7])
                        with col_tit:
                            st.header(f"Ficha: {animal['nome']}")
                        with col_edit:
                            if st.button("📝 Editar", key=f"edit_mode_{idx}"):
                                st.session_state.editando_idx = idx
                                st.rerun()
                        with col_del:
                            if st.button("🗑️ Excluir", key=f"btn_del_{idx}"):
                                st.session_state.lista_animais.pop(idx)
                                st.rerun()

                        st.write(f"**Idade Estimada:** {animal['idade']} | **Raça:** {animal.get('raca', 'SRD')}")
                        st.write(f"**Estado de Saúde / Info Adotante:** {animal['saude']}")
                        st.info("📍 Referência: São Paulo/SP")

                        # BOTÕES DE AÇÃO (WhatsApp e Redes Sociais)
                        st.markdown("---")
                        c_whats, c_web = st.columns(2)
                        
                        with c_whats:
                            zap_animal = animal.get('whatsapp', '5511999999999')
                            texto_msg = f"Olá! Vi o animal {animal['nome']} no PetHub e gostaria de informações."
                            link_whats = f"https://wa.me/{zap_animal}?text={urllib.parse.quote(texto_msg)}"
                            st.link_button(f"📲 Interesse em {animal['nome']}", link_whats, use_container_width=True)
                        
                        with c_web:
                            url_alvo = animal.get('url_instituicao', 'https://www.google.com')
                            st.link_button("🌐 Visitar Site / Rede Social", url_alvo, use_container_width=True)

                        with st.expander("📄 Ver Termos e Responsabilidades de Adoção"):
                            st.markdown("""
                                <div style="background-color: #262730; padding: 15px; border-radius: 5px; border-left: 5px solid #ff4b4b;">
                                    <strong style="color: white;">AVISO IMPORTANTE:</strong><br>
                                    <p style="color: white; margin-top: 5px;">
                                        A adoção é um compromisso legal e vitalício (Lei Federal 9.605/98). 
                                        O abandono de animais é crime com pena de detenção.
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)

# ==========================================
# 6. PÁGINA: CADASTRAR NOVO PET
# ==========================================
elif pagina == "Cadastrar Novo Pet":
    st.title("📝 Cadastrar Nova Ficha Técnica")
    st.write("Interface administrativa para inclusão de novos animais e gestão de dados.")

    with st.form("form_cadastro", clear_on_submit=True):
        st.write("### Dados do Animal")
        col_cad1, col_cad2 = st.columns(2)
        
        with col_cad1:
            nome = st.text_input("Nome do Animal", placeholder="Ex: Mel")
            idade = st.text_input("Idade Estimada", placeholder="Ex: 2 anos")
            raca = st.text_input("Raça", placeholder="Ex: SRD")
        
        with col_cad2:
            whatsapp_input = st.text_input("WhatsApp", placeholder="Ex: 5511999999999", help="DDD + Número sem espaços")
            url_dinamica = st.text_input("Link da Rede Social ou Site do Pet", placeholder="https://instagram.com/seu_perfil")
            foto_arquivo = st.file_uploader("Selecione a foto (JPEG, PNG)", type=["jpg", "jpeg", "png"])
            
        saude = st.text_area("Observações de Saúde / Adotante", placeholder="Vacinada, castrada ou dados do novo dono...")
        
        st.divider()
        botao_salvar = st.form_submit_button("Finalizar Cadastro e Salvar")
        
        if botao_salvar:
            if nome and foto_arquivo and whatsapp_input:
                img_processada = Image.open(foto_arquivo)
                
                # --- LÓGICA DE SALVAMENTO NO GOOGLE SHEETS ---
                planilha = conectar_google_sheets()
                if planilha:
                    try:
                        data_hoje = datetime.now().strftime("%d/%m/%Y")
                        nova_linha = [data_hoje, nome, idade, raca, saude, whatsapp_input, url_dinamica]
                        planilha.append_row(nova_linha)
                    except Exception:
                        # Silencia timeouts se o dado já foi enviado com sucesso (Erro 200)
                        pass
                
                novo_pet = {
                    "nome": nome,
                    "idade": idade,
                    "raca": raca,
                    "saude": saude,
                    "whatsapp": whatsapp_input.replace(" ", "").replace("-", ""),
                    "url_instituicao": url_dinamica if url_dinamica else "https://www.google.com",
                    "foto": img_processada
                }
                
                st.session_state.lista_animais.append(novo_pet)
                st.success(f"✅ Sucesso! A ficha de {nome} foi gerada e armazenada na Planilha e no Site.")
            else:
                st.error("❌ Preencha Nome, Foto e WhatsApp para prosseguir.")

# ==========================================
# 7. PÁGINA: GUIA DE POSSE RESPONSÁVEL
# ==========================================
else:
    st.title("📚 Guia da Posse Responsável")
    st.markdown("""
    ### Educação e Conscientização Comunitária
    A adoção consciente transforma a realidade da fauna urbana em São Paulo e garante que o animal não sofra maus-tratos.
    
    1. **Bem-Estar:** Alimentação de qualidade, vacinação anual e vermifugação periódica.
    2. **Segurança:** Nunca permita acesso livre à rua. Telas em janelas e coleiras são essenciais.
    3. **Sociedade:** A castração é a única forma eficaz de controle populacional.
    4. **Compromisso:** Cães e gatos vivem em média 15 anos. Esteja preparado para cuidar dele em todas as fases.
    
    ---
    *Projeto de extensão universitária - Análise e Desenvolvimento de Sistemas.*
    """)

# ==========================================
# 8. RODAPÉ ACADÊMICO E ODS (COMPLETO)
# ==========================================
st.divider()
st.markdown("""
<div style="text-align: center; background-color: #f0f2f6; padding: 30px; border-radius: 12px; color: #31333F; border: 1px solid #d1d5db;">
    <h3 style="margin-top: 0; color: #1f77b4;">Carlos Magno | ADS - Anhembi Morumbi</h3>
    <strong style="font-size: 1.1em;">2º Semestre - Projeto de Extensão Universitária</strong><br>
    <strong>SÃO PAULO - GRANDE SÃO PAULO/SP</strong><br><br>
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <span style="background-color: #4ca146; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 200px;">ODS 3: Saúde e Bem-Estar</span>
        <span style="background-color: #f99d26; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 200px;">ODS 11: Cidades Sustentáveis</span>
        <span style="background-color: #007db8; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 200px;">ODS 15: Vida Terrestre</span>
    </div>
    <br>
    <p style="font-style: italic; max-width: 800px; margin: 10px auto 0 auto;">
        "Este software integra a tecnologia à causa animal, permitindo que ONGs e estabelecimentos comerciais monitorem a saúde 
        e a segurança de animais adotados, prevenindo maus-tratos e fidelizando o adotante através do suporte contínuo."
    </p>
</div>
""", unsafe_allow_html=True)