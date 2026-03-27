import json
import os
from flask import Flask, render_template, request, jsonify, session
import bcrypt

app = Flask(__name__)
app.secret_key = "sabor_do_brasil_chave_secreta_2024"

ARQUIVO_DADOS = "usuarios.json"

def ler_dados():
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)

# ================= HASH =================
def hash_senha(senha_texto_puro):
    senha_bytes = senha_texto_puro.encode("utf-8")
    senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
    return senha_hash.decode("utf-8")

def verificar_senha(senha_texto_puro, senha_hash):
    return bcrypt.checkpw(
        senha_texto_puro.encode("utf-8"),
        senha_hash.encode("utf-8")
    )

# ================= PERFIL =================
def usuario_pode_editar(id_usuario_acao, id_autor_comentario):
    dados = ler_dados()
    for usuario in dados["usuarios"]:
        if usuario["id"] == id_usuario_acao:
            return usuario["perfil"] == "admin" or id_usuario_acao == id_autor_comentario
    return False

# ================= ROTAS =================
@app.route("/")
def index():
    dados = ler_dados()
    return render_template("index.html", receitas=dados["receitas"], usuario=session.get("usuario"))

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    corpo = request.get_json()
    nickname = corpo.get("nickname", "").strip()
    senha = corpo.get("senha", "").strip()

    if not nickname or not senha:
        return jsonify({"erro": "Preencha todos os campos"}), 400

    dados = ler_dados()

    for u in dados["usuarios"]:
        if u["nickname"].lower() == nickname.lower():
            return jsonify({"erro": "Nickname já está em uso"}), 409

    novo_usuario = {
        "id": dados["proximo_usuario_id"],
        "nickname": nickname,
        "senha": hash_senha(senha),
        "perfil": "comum"
    }

    dados["usuarios"].append(novo_usuario)
    dados["proximo_usuario_id"] += 1

    salvar_dados(dados)
    return jsonify({"mensagem": "Cadastro realizado com sucesso!"})

@app.route("/login", methods=["POST"])
def login():
    corpo = request.get_json()
    nickname = corpo.get("nickname", "").strip()
    senha = corpo.get("senha", "").strip()

    dados = ler_dados()

    usuario = next((u for u in dados["usuarios"] if u["nickname"].lower() == nickname.lower()), None)

    if not usuario or not verificar_senha(senha, usuario["senha"]):
        return jsonify({"erro": "Usuário ou senha incorreto"}), 401

    session["usuario"] = {
        "id": usuario["id"],
        "nickname": usuario["nickname"],
        "perfil": usuario["perfil"]
    }

    return jsonify({"mensagem": "Login realizado!", "usuario": session["usuario"]})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"mensagem": "Logout realizado!"})

@app.route("/curtir/<int:id>", methods=["POST"])
def curtir(id):
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Login necessário"}), 401

    dados = ler_dados()

    for r in dados["receitas"]:
        if r["id"] == id:
            if usuario["nickname"] in r["curtidas"]:
                r["curtidas"].remove(usuario["nickname"])
            else:
                r["curtidas"].append(usuario["nickname"])

            salvar_dados(dados)

            return jsonify({
                "total_curtidas": len(r["curtidas"]),
                "curtiu": usuario["nickname"] in r["curtidas"]
            })

@app.route("/comentar/<int:id>", methods=["POST"])
def comentar(id):
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Login necessário"}), 401

    texto = request.get_json().get("texto", "").strip()

    dados = ler_dados()

    for r in dados["receitas"]:
        if r["id"] == id:
            comentario = {
                "id": dados["proximo_comentario_id"],
                "autor_id": usuario["id"],
                "autor_nickname": usuario["nickname"],
                "texto": texto
            }

            r["comentarios"].append(comentario)
            dados["proximo_comentario_id"] += 1

            salvar_dados(dados)
            return jsonify({"comentario": comentario})

@app.route("/comentario/<int:id>", methods=["DELETE"])
def excluir(id):
    usuario = session.get("usuario")

    dados = ler_dados()

    for r in dados["receitas"]:
        for c in r["comentarios"]:
            if c["id"] == id:
                if not usuario_pode_editar(usuario["id"], c["autor_id"]):
                    return jsonify({"erro": "Sem permissão"}), 403

                r["comentarios"].remove(c)
                salvar_dados(dados)
                return jsonify({"mensagem": "Excluído"})

if __name__ == "__main__":
    app.run(debug=True)
