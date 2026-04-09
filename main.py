import qrcode
from supabase import create_client, Client

# Configurações do Guardião Pet SP
SUPABASE_URL = "https://bqawbkibffppaswlwsgr.supabase.co"
SUPABASE_KEY = "sb_publishable_3R_hLe9JN_2kD89rv9dzCQ_-rWznngn"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def gerar_qr_code(nome, especie, idade):
    # Criando o texto que o QR Code vai conter
    conteudo = f"Guardião Pet SP\nPet: {nome}\nEspécie: {especie}\nIdade: {idade}\nStatus: Disponível para Adoção"
    
    # Gerando a imagem
    img = qrcode.make(conteudo)
    
    # Nome do arquivo (ex: qrcode_bob.png)
    nome_arquivo = f"qrcode_{nome.lower().replace(' ', '_')}.png"
    img.save(nome_arquivo)
    print(f"📷 QR Code gerado com sucesso: {nome_arquivo}")

def cadastrar_pet():
    print("\n" + "="*30)
    print(" CADASTRO + QR CODE: SISTEMAPET ")
    print("="*30)
    
    nome = input("Nome do pet: ")
    especie = input("Espécie: ")
    idade = input("Idade: ")
    
    dados_pet = {"nome": nome, "especie": especie, "idade": idade}
    
    try:
        # 1. Salva no Supabase
        supabase.table("pets").insert(dados_pet).execute()
        print(f"\n✅ {nome} salvo na nuvem!")
        
        # 2. Gera o QR Code automaticamente
        gerar_qr_code(nome, especie, idade)
        
    except Exception as e:
        print(f"\n❌ Erro no processo: {e}")

def listar_pets():
    print("\n" + "="*30)
    print(" LISTA DE ADOÇÃO ATUALIZADA ")
    print("="*30)
    resposta = supabase.table("pets").select("*").execute()
    for pet in resposta.data:
        print(f"🐾 {pet['nome'].upper()} - {pet['especie']}")

if __name__ == "__main__":
    cadastrar_pet()
    listar_pets()