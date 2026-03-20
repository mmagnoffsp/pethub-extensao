import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configura o acesso usando o arquivo que está no seu C:
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('pethub_key.json', scope)
client = gspread.authorize(creds)

# 2. Abre a sua planilha (Mude para o nome EXATO da sua planilha)
nome_da_planilha = "PetHub - Banco de Dados" 
planilha = client.open(nome_da_planilha).sheet1

# 3. Tenta escrever um dado de teste
planilha.append_row(["18/03/2026", "Rex", "Cachorro", "Vira-lata", "Carlos"])

print(f"✅ SUCESSO! O pet 'Rex' foi cadastrado na planilha '{nome_da_planilha}'.")