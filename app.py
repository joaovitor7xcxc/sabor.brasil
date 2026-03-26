import json
import os
from flask import Flask, render_template, request, jsonify, session
from bcrypt import hashpw, checkpw, gensalt

app = Flask(__name__)
app.secret_key = "chave_segura_123"

ARQUIVO_DADOS = "usuarios.json"


def ler_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return {
            "usuarios": [],
            "receitas": [],
            "proximo_comentario_id": 1,
            "proximo_usuario_id": 1,
            "proximo_receita_id": 1
        }

    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def gerar_hash(senha):
    return hashpw(senha.encode("utf-8"), gensalt()).decode("utf-8")


def conferir_senha(senha, senha_hash):
    return checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def pode_editar(user_id, autor_id):
    dados = ler_dados()
    for u in dados["usuarios"]:
        if u["id"] == user_id:
            return u["perfil"] == "admin" or user_id == autor_id
    return False


@app.route("/")
def home():
    dados = ler_dados()
    return render_template("index.html", receitas=dados["receitas"], usuario=session.get("usuario"))


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    data = request.get_json()
    nick = data.get("nickname", "").strip()
    senha = data.get("senha", "").strip()

    if not nick or not senha:
        return jsonify({"erro": "Preencha tudo"}), 400

    dados = ler_dados()

    for u in dados["usuarios"]:
        if u["nickname"].lower() == nick.lower():
            return jsonify({"erro": "Já existe"}), 409

    novo = {
        "id": dados["proximo_usuario_id"],
        "nickname": nick,
        "senha": gerar_hash(senha),
        "perfil": "comum"
    }

    dados["usuarios"].append(novo)
    dados["proximo_usuario_id"] += 1

    salvar_dados(dados)

    return jsonify({"mensagem": "Cadastrado"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    nick = data.get("nickname", "").strip()
    senha = data.get("senha", "").strip()

    if not nick or not senha:
        return jsonify({"erro": "Preencha tudo"}), 400

    dados = ler_dados()
    user = None

    for u in dados["usuarios"]:
        if u["nickname"].lower() == nick.lower():
            user = u
            break

    if not user:
        return jsonify({"erro": "Login inválido"}), 401

    if not conferir_senha(senha, user["senha"]):
        return jsonify({"erro": "Login inválido"}), 401

    session["usuario"] = {
        "id": user["id"],
        "nickname": user["nickname"],
        "perfil": user["perfil"]
    }

    return jsonify({"usuario": session["usuario"]})


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"msg": "Saiu"})


@app.route("/curtir/<int:id>", methods=["POST"])
def curtir(id):
    user = session.get("usuario")
    if not user:
        return jsonify({"erro": "Login necessário"}), 401

    dados = ler_dados()

    for r in dados["receitas"]:
        if r["id"] == id:
            nome = user["nickname"]

            if nome in r["curtidas"]:
                r["curtidas"].remove(nome)
            else:
                r["curtidas"].append(nome)

            salvar_dados(dados)

            return jsonify({
                "total_curtidas": len(r["curtidas"]),
                "curtiu": nome in r["curtidas"]
            })

    return jsonify({"erro": "Não encontrado"}), 404


@app.route("/comentar/<int:id>", methods=["POST"])
def comentar(id):
    user = session.get("usuario")
    if not user:
        return jsonify({"erro": "Login necessário"}), 401

    data = request.get_json()
    texto = data.get("texto", "").strip()

    if not texto:
        return jsonify({"erro": "Vazio"}), 400

    dados = ler_dados()

    for r in dados["receitas"]:
        if r["id"] == id:
            novo = {
                "id": dados["proximo_comentario_id"],
                "autor_id": user["id"],
                "autor_nickname": user["nickname"],
                "texto": texto
            }

            r["comentarios"].append(novo)
            dados["proximo_comentario_id"] += 1

            salvar_dados(dados)

            return jsonify({"comentario": novo})

    return jsonify({"erro": "Não encontrado"}), 404


@app.route("/comentario/<int:id>", methods=["DELETE"])
def deletar(id):
    user = session.get("usuario")
    if not user:
        return jsonify({"erro": "Login necessário"}), 401

    dados = ler_dados()

    for r in dados["receitas"]:
        for c in r["comentarios"]:
            if c["id"] == id:

                if not pode_editar(user["id"], c["autor_id"]):
                    return jsonify({"erro": "Sem permissão"}), 403

                r["comentarios"].remove(c)
                salvar_dados(dados)

                return jsonify({"msg": "Removido"})

    return jsonify({"erro": "Não encontrado"}), 404


@app.route("/status")
def status():
    return jsonify({"user": session.get("usuario")})


@app.route("/adicionar_receita", methods=["POST"])
def adicionar_receita():
    user = session.get("usuario")
    if not user:
        return jsonify({"erro": "Login necessário"}), 401

    if user["perfil"] != "admin":
        return jsonify({"erro": "Apenas administradores podem adicionar receitas"}), 403

    data = request.get_json()
    titulo = data.get("titulo", "").strip()
    descricao = data.get("descricao", "").strip()
    imagem = data.get("imagem", "").strip()

    if not titulo or not descricao:
        return jsonify({"erro": "Título e descrição são obrigatórios"}), 400

    dados = ler_dados()

    nova_receita = {
        "id": dados["proximo_receita_id"],
        "titulo": titulo,
        "descricao": descricao,
        "imagem": imagem or "🍽️",
        "curtidas": [],
        "comentarios": []
    }

    dados["receitas"].append(nova_receita)
    dados["proximo_receita_id"] += 1

    salvar_dados(dados)

    return jsonify({"receita": nova_receita})


@app.route("/deletar_receita/<int:id>", methods=["DELETE"])
def deletar_receita(id):
    user = session.get("usuario")
    if not user:
        return jsonify({"erro": "Login necessário"}), 401

    if user["perfil"] != "admin":
        return jsonify({"erro": "Apenas administradores podem deletar receitas"}), 403

    dados = ler_dados()

    for i, r in enumerate(dados["receitas"]):
        if r["id"] == id:
            dados["receitas"].pop(i)
            salvar_dados(dados)
            return jsonify({"msg": "Receita removida"})

    return jsonify({"erro": "Receita não encontrada"}), 404


if __name__ == "__main__":
    PORTA = 8000

    if not os.path.exists(ARQUIVO_DADOS):
        print("Criando arquivo inicial...")
        dados_iniciais = {
            "usuarios": [
                {
                    "id": 1,
                    "nickname": "admin",
                    "senha": gerar_hash("admin123"),
                    "perfil": "admin"
                }
            ],
            "receitas": [
                {
                    "id": 1,
                    "titulo": "Feijoada Completa",
                    "descricao": "A mais tradicional feijoada brasileira, com feijão preto, carnes defumadas e acompanhamentos clássicos.",
                    "imagem": "🍲",
                    "curtidas": [],
                    "comentarios": []
                },
                {
                    "id": 2,
                    "titulo": "Coxinha Crocante",
                    "descricao": "Salgado recheado com frango desfiado temperado, empanado e frito até a perfeição dourada.",
                    "imagem": "🍗",
                    "curtidas": [],
                    "comentarios": []
                },
                {
                    "id": 3,
                    "titulo": "Brigadeiro Gourmet",
                    "descricao": "O clássico docinho brasileiro em versão premium, com chocolate belga e cobertura artesanal.",
                    "imagem": "🍫",
                    "curtidas": [],
                    "comentarios": []
                }
            ],
            "proximo_comentario_id": 1,
            "proximo_usuario_id": 2,
            "proximo_receita_id": 4
        }
        salvar_dados(dados_iniciais)

    print(f"Servidor rodando em http://127.0.0.1:{PORTA}")
    app.run(debug=True, port=PORTA)