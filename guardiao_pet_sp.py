# PROJETO: guardiao_pet_sp.py voltado a causa animal para adotantes via casa de ração ou através de ongs
# Projeto de Extensão Universitária - Análise e Desenvolvimento de Sistemas
# SÃO PAULO - PENHA / VILA ESPERANÇA
# Data da última atualização: "21/03/2026"

import streamlit as st # Biblioteca principal para criação da interface web
import qrcode          # Biblioteca para geração de QR Codes dinâmicos
from io import BytesIO  # Gerencia o armazenamento temporário de dados binários (imagens)
import urllib.parse    # Utilizado para formatar links de URL (importante para o WhatsApp)
from PIL import Image   # Processamento de imagens (essencial para o upload de fotos JPEG)
import gspread         # Biblioteca para integração com Google Sheets
from google.oauth2.service_account import Credentials # Gestão de credenciais GCP
from datetime import datetime # Para registro de data nos cadastros

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (Metadata)
# ==========================================
st.set_page_config(
    page_title="Projeto Guardião Pet SP - Fichas Técnicas",
    page_icon="🛡️",
    layout="wide" 
)

# --- FUNÇÃO DE CONEXÃO COM GOOGLE SHEETS (VERSÃO CORRIGIDA ADS) ---
def conectar_google_sheets():
    try:
        # Escopos para garantir escrita e leitura
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # 1. Busca nos Secrets usando a sua estrutura [connections.gsheets.json_key]
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_info = dict(st.secrets["connections"]["gsheets"]["json_key"])
        else:
            st.error("❌ A estrutura de segredos 'connections.gsheets.json_key' não foi encontrada.")
            return None
        
        # 2. Limpeza da Private Key (essencial para evitar erro de formatação)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()

        # 3. Autorização
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)

        # 4. Abertura da planilha via URL salva nos Secrets
        url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
        return client.open_by_url(url_planilha).sheet1
        
    except Exception as e:
        # Silencia erros de checklist do Streamlit (código 200) e foca em erros reais
        if "200" not in str(e):
            st.error(f"Erro de conexão real: {e}")
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
            "raca": "SRD",
            "saude": "Vacinado e Vermifugado",
            "whatsapp": "5511941507706", 
            "url_instituicao": "https://www.instagram.com", 
            "foto": "https://placedog.net/500/350?id=10"
        }
    ]

# Controle de estado para edição dinâmica de fichas
if 'editando_idx' not in st.session_state:
    st.session_state.editando_idx = None

# ==========================================
# 4. BARRA LATERAL (NAVEGAÇÃO E IMPACTO SOCIAL)
# ==========================================
with st.sidebar:
    st.title("🛡️ Guardião Pet SP")
    st.write("Sistema de Gestão de Adoção Consciente")
    st.divider()
    
    pagina = st.radio(
        "Navegar por:", 
        ["Fichas Técnicas", "Cadastrar Novo Pet", "Guia de Posse Responsável"]
    )
    
    st.divider()
    st.write("### Divulgue o Projeto")
    
    # URL do projeto hospedado
    url_site = "https://guardiao-pet-sp.streamlit.app"
    qr_img = gerar_qr_code(url_site)
    
    st.image(qr_img, caption="Acesse o Portal pelo Celular", width=250)
    
    st.download_button(
        label="⬇️ Baixar QR Code para Impressão",
        data=qr_img,
        file_name="qrcode_guardiao_pet_sp.png",
        mime="image/png"
    )
    
# ==========================================
# 5. PÁGINA: FICHAS TÉCNICAS (VISUALIZAÇÃO E EDIÇÃO)
# ==========================================
if pagina == "Fichas Técnicas":
    st.title("🐾 Fichas de Proteção Animal")
    st.subheader("Dados detalhados para uma adoção segura e acompanhamento pós-adoção")
    st.markdown("---")

    if not st.session_state.lista_animais:
        st.info("Nenhum animal cadastrado no momento no Guardião Pet SP.")
    else:
        for idx, animal in enumerate(st.session_state.lista_animais):
            with st.container(border=True):
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.image(animal["foto"], use_container_width=True)
                
                with col2:
                    # LÓGICA DE EDIÇÃO DINÂMICA
                    if st.session_state.editando_idx == idx:
                        st.markdown(f"### 📝 Editando Ficha: {animal['nome']}")
                        
                        ed_nome = st.text_input("Nome do Animal", animal['nome'], key=f"ed_nome_{idx}")
                        ed_idade = st.text_input("Idade Estimada", animal['idade'], key=f"ed_idade_{idx}")
                        ed_raca = st.text_input("Raça", animal.get('raca', 'SRD'), key=f"ed_raca_{idx}")
                        
                        url_atual = animal.get('url_instituicao', '')
                        ed_url = st.text_input("URL da Instituição/Rede Social", url_atual, key=f"ed_url_{idx}")
                        
                        ed_saude = st.text_area("Estado de Saúde / Observações", animal['saude'], key=f"ed_saude_{idx}")
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
                                st.success("Dados atualizados com sucesso!")
                                st.rerun()
                        with col_cancelar:
                            if st.button("❌ Cancelar", key=f"cancel_btn_{idx}"):
                                st.session_state.editando_idx = None
                                st.rerun()

                    else:
                        # VISUALIZAÇÃO NORMAL DA FICHA
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
                        st.write(f"**Estado de Saúde:** {animal['saude']}")
                        st.info("📍 Localização de Referência: São Paulo/SP - Penha")

                        # BOTÕES DE INTERAÇÃO SOCIAL
                        st.markdown("---")
                        c_whats, c_web = st.columns(2)
                        
                        with c_whats:
                            zap_animal = animal.get('whatsapp', '5511999999999')
                            texto_msg = f"Olá! Vi o animal {animal['nome']} no Guardião Pet SP e gostaria de mais informações."
                            link_whats = f"https://wa.me/{zap_animal}?text={urllib.parse.quote(texto_msg)}"
                            st.link_button(f"📲 Interesse em {animal['nome']}", link_whats, use_container_width=True)
                        
                        with c_web:
                            url_alvo = animal.get('url_instituicao', 'https://www.google.com')
                            st.link_button("🌐 Visitar Site / Rede Social", url_alvo, use_container_width=True)

                        with st.expander("📄 Ver Termos e Responsabilidades de Adoção"):
                            st.markdown("""
                                <div style="background-color: #262730; padding: 15px; border-radius: 5px; border-left: 5px solid #ff4b4b;">
                                    <strong style="color: white;">AVISO LEGAL (Lei 9.605/98):</strong><br>
                                    <p style="color: white; margin-top: 5px;">
                                        A adoção é um compromisso vitalício. O abandono de animais é crime punível com detenção e multa.
                                        Certifique-se de ter recursos para alimentação e cuidados veterinários.
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)

# ==========================================
# 6. PÁGINA: CADASTRAR NOVO PET
# ==========================================
elif pagina == "Cadastrar Novo Pet":
    st.title("📝 Cadastro Guardião Pet SP")
    st.write("Interface administrativa para inclusão de novos animais no sistema sincronizado.")

    with st.form("form_cadastro", clear_on_submit=True):
        st.write("### Dados do Animal")
        col_cad1, col_cad2 = st.columns(2)
        
        with col_cad1:
            nome = st.text_input("Nome do Animal", placeholder="Ex: Mel")
            idade = st.text_input("Idade Estimada", placeholder="Ex: 2 anos")
            raca = st.text_input("Raça", placeholder="Ex: SRD")
        
        with col_cad2:
            whatsapp_input = st.text_input("WhatsApp para Contato", placeholder="Ex: 5511999999999", help="DDD + Número sem espaços")
            url_dinamica = st.text_input("Link da Rede Social (Instagram/Site)", placeholder="https://instagram.com/perfil")
            foto_arquivo = st.file_uploader("Selecione a foto (JPEG, PNG)", type=["jpg", "jpeg", "png"])
            
        saude = st.text_area("Observações de Saúde / Histórico", placeholder="Vacinada, castrada, dócil...")
        
        st.divider()
        botao_salvar = st.form_submit_button("Finalizar Cadastro e Salvar")
        
        if botao_salvar:
            if nome and foto_arquivo and whatsapp_input:
                img_processada = Image.open(foto_arquivo)
                
                # --- INTEGRAÇÃO GOOGLE SHEETS ---
                planilha = conectar_google_sheets()
                if planilha is not None:
                    try:
                        data_hoje = datetime.now().strftime("%d/%m/%Y")
                        # Ordem das colunas na planilha: Data, Nome, Idade, Raça, Saúde, WhatsApp, Link
                        nova_linha = [data_hoje, nome, idade, raca, saude, whatsapp_input, url_dinamica]
                        planilha.append_row(nova_linha)
                        
                        # Sincronização com o estado da sessão (Site)
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
                        st.success(f"✅ Sucesso! A ficha de {nome} foi salva na Planilha e no Guardião Pet SP.")
                    except Exception as e:
                        st.error(f"❌ Erro ao gravar dados: {e}")
                else:
                    st.error("❌ Falha de conexão. Verifique as credenciais no Secrets.")
            else:
                st.error("❌ Preencha os campos obrigatórios (Nome, Foto e WhatsApp).")

# ==========================================
# 7. PÁGINA: GUIA DE POSSE RESPONSÁVEL
# ==========================================
elif pagina == "Guia de Posse Responsável":
    st.title("📚 Guia do Guardião Responsável")
    st.markdown("""
    ### Educação e Conscientização Comunitária
    A adoção consciente transforma a realidade da fauna urbana e garante a segurança dos animais.
    
    1. **Bem-Estar:** Alimentação de qualidade e vacinação anual (V10/Raiva).
    2. **Segurança:** Telas em janelas para gatos e coleiras com identificação para cães.
    3. **Sociedade:** A castração é fundamental para evitar o abandono e doenças.
    4. **Compromisso:** Um animal vive em média 15 anos. Esteja preparado para todas as fases.
    
    ---
    *Projeto desenvolvido como atividade de extensão universitária.*
    """)

# ==========================================
# 8. RODAPÉ ACADÊMICO E ODS (OFICIAL ADS)
# ==========================================
st.divider()
st.markdown("""
<div style="text-align: center; background-color: #f0f2f6; padding: 30px; border-radius: 12px; color: #31333F; border: 1px solid #d1d5db;">
    <h3 style="margin-top: 0; color: #1f77b4;">Carlos Magno | ADS - Anhembi Morumbi</h3>
    <strong style="font-size: 1.1em;">2º Semestre - Projeto de Extensão Universitária</strong><br>
    <strong>SÃO PAULO - PENHA / VILA ESPERANÇA</strong><br><br>
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <span style="background-color: #4ca146; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 180px;">ODS 3: Saúde e Bem-Estar</span>
        <span style="background-color: #f99d26; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 180px;">ODS 11: Cidades Sustentáveis</span>
        <span style="background-color: #007db8; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; min-width: 180px;">ODS 15: Vida Terrestre</span>
    </div>
    <br>
    <p style="font-style: italic; max-width: 800px; margin: 10px auto 0 auto;">
        "Este software integra a tecnologia à causa animal através do Projeto Guardião Pet SP, permitindo que ONGs e estabelecimentos monitorem a saúde 
        e a segurança de animais adotados, prevenindo maus-tratos."
    </p>
</div>
""", unsafe_allow_html=True)