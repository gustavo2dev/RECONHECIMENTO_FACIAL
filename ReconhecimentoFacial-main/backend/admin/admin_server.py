from flask import Flask, jsonify, request, send_from_directory, send_file
import csv
import json
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# O admin e o reconhecimento devem trabalhar com a mesma base de usuários.
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_data.json")
ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(os.path.dirname(DATA_FILE), "registros.csv")


@app.route("/")
def pagina_inicial():
    return send_from_directory(ADMIN_DIR, "index.html")


@app.route("/styles.css")
def estilos():
    return send_from_directory(ADMIN_DIR, "styles.css")

# Lê os dados do arquivo JSON
def ler_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                print("✅ face_data.json carregado:", dados)
                return dados
        except Exception as e:
            print("❌ Erro ao ler JSON:", e)
            return []
    else:
        print("⚠️ Arquivo face_data.json não encontrado!")
    return []

# Salva os dados no arquivo JSON
def salvar_dados(dados):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2)
            print("💾 Dados salvos com sucesso.")
    except Exception as e:
        print("❌ Erro ao salvar JSON:", e)

# Retorna os usuários para o frontend
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    dados = ler_dados()
    usuarios_simplificados = [
        {
            "nome": u.get("nome", ""),
            "nome_original": u.get("nome", ""),
            "idade": u.get("idade", ""),
            "profissao": u.get("profissao", "")
        } for u in dados if "nome" in u
    ]
    print("🔁 Enviando para o frontend:", usuarios_simplificados)
    return jsonify(usuarios_simplificados)

# Atualiza os dados dos usuários
@app.route("/usuarios", methods=["POST"])
def atualizar_usuarios():
    novos_dados = request.get_json(silent=True)
    if not isinstance(novos_dados, list):
        return jsonify({"erro": "Envie uma lista de usuarios."}), 400
    antigos = ler_dados()

    atualizados = []
    for novo in novos_dados:
        nome_original = novo.get("nome_original", novo.get("nome"))
        existente = next((x for x in antigos if x.get("nome") == nome_original), None)
        if existente:
            existente["idade"] = novo.get("idade", "")
            existente["profissao"] = novo.get("profissao", "")
            atualizados.append(existente)
        elif novo.get("nome"):
            atualizados.append({
                "nome": novo["nome"],
                "idade": novo.get("idade", ""),
                "profissao": novo.get("profissao", ""),
                "encoding": [],
            })

    salvar_dados(atualizados)
    return jsonify({"mensagem": "Salvo com sucesso!"})


@app.route("/registros", methods=["GET"])
def listar_registros():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    with open(LOG_FILE, "r", encoding="utf-8-sig", newline="") as arquivo:
        return jsonify(list(csv.DictReader(arquivo, delimiter=";")))


@app.route("/registros.csv", methods=["GET"])
def baixar_registros():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as arquivo:
            csv.writer(arquivo, delimiter=";").writerow(["Data", "Horario", "Nome", "Idade", "Profissao"])
    return send_file(LOG_FILE, as_attachment=True, download_name="registros_reconhecimento.csv")


if __name__ == "__main__":
    print(f"🚀 Servidor iniciado. Lendo dados de: {DATA_FILE}")
    app.run(port=5000)
