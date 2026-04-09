from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import database

# --- CONFIGURAÇÃO INICIAL (NÃO PODE APAGAR!) ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Cria a tabela no banco Neon ao iniciar
database.criar_tabela()

# --- ROTAS DO SISTEMA ---

@app.get("/")
def listar_pets(request: Request):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pets")
    pets = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"pets": pets}
    )

@app.get("/cadastrar")
def form_cadastro(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="cadastro.html"
    )

@app.post("/cadastrar")
def salvar_pet(nome: str = Form(...), especie: str = Form(...), idade: int = Form(...)):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO pets (nome, especie, idade) VALUES (%s, %s, %s)", (nome, especie, idade))
    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url="/", status_code=303)