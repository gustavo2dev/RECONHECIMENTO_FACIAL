from flask import Flask, jsonify, request, send_from_directory, send_file
import csv
import io
import json
import logging
import os
import re
import shutil
import tempfile
import face_recognition
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# O admin e o reconhecimento devem trabalhar com a mesma base de usuários.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RECORDS_DIR = os.path.join(BASE_DIR, "records")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RECORDS_DIR, exist_ok=True)


def migrar_dado(nome):
    destino = os.path.join(DATA_DIR, nome)
    legado = os.path.join(BASE_DIR, nome)
    if not os.path.exists(destino) and os.path.exists(legado):
        shutil.copy2(legado, destino)
    return destino


DATA_FILE = migrar_dado("face_data.json")
ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_PHOTO_DIR = os.path.join(os.path.dirname(DATA_FILE), "face_data")
LOG_FILE = migrar_dado("registros.csv")
LATE_FILE = migrar_dado("atrasos.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "admin.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)
CONFIG_FILE = migrar_dado("config.json")
DEFAULT_CONFIG = {
    "manha_inicio": "07:30", "manha_atraso": "07:30", "manha_fim": "12:30",
    "tarde_inicio": "13:30", "tarde_atraso": "13:30", "tarde_fim": "17:25",
    "cooldown_minutos": 60, "tolerancia": 0.5,
}


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
                print(f"✅ face_data.json carregado: {len(dados)} pessoa(s)")
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
        pasta = os.path.dirname(DATA_FILE)
        arquivo_temporario = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=pasta, delete=False
        )
        with arquivo_temporario as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(arquivo_temporario.name, DATA_FILE)
        logger.info("Base de pessoas salva: %s pessoa(s)", len(dados))
        return True
    except Exception as e:
        logger.exception("Erro ao salvar JSON")
        if "arquivo_temporario" in locals() and os.path.exists(arquivo_temporario.name):
            os.remove(arquivo_temporario.name)
        return False


def ler_configuracao():
    configuracao = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as arquivo:
                configuracao.update(json.load(arquivo))
        except (json.JSONDecodeError, OSError):
            pass
    return configuracao


def ler_csv(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def usuario_publico(usuario):
    return {
        "nome": usuario.get("nome", ""),
        "nome_original": usuario.get("nome", ""),
        "idade": usuario.get("idade", ""),
        "profissao": usuario.get("profissao", ""),
        "turma": usuario.get("turma", usuario.get("profissao", "")),
        "tipo_pessoa": usuario.get("tipo_pessoa", "Aluno"),
        "identificacao": usuario.get("id", usuario.get("nome", "")),
    }

# Retorna os usuários para o frontend
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    dados = ler_dados()
    usuarios_simplificados = [usuario_publico(u) for u in dados if u.get("nome")]
    print(f"🔁 Enviando {len(usuarios_simplificados)} pessoa(s) para o frontend")
    return jsonify(usuarios_simplificados)

# Atualiza os dados dos usuários
@app.route("/usuarios", methods=["POST"])
def atualizar_usuarios():
    novos_dados = request.get_json(silent=True)
    if not isinstance(novos_dados, list):
        return jsonify({"erro": "Envie uma lista de usuarios."}), 400
    atualizados = ler_dados()
    for novo in novos_dados:
        nome_original = novo.get("nome_original", novo.get("nome"))
        existente = next((x for x in atualizados if x.get("nome") == nome_original), None)
        if existente:
            existente["nome"] = novo.get("nome", nome_original).strip()
            existente["idade"] = novo.get("idade", "")
            existente["turma"] = novo.get("turma", novo.get("profissao", ""))
            existente["profissao"] = existente["turma"]
            existente["tipo_pessoa"] = novo.get("tipo_pessoa", "Aluno")
            existente["id"] = novo.get("identificacao", existente.get("id", existente["nome"]))
            continue
        elif novo.get("nome"):
            return jsonify({"erro": "Pessoa nova precisa ser adicionada com uma foto facial."}), 400

    if not salvar_dados(atualizados):
        return jsonify({"erro": "Nao foi possivel salvar a base de pessoas."}), 500
    return jsonify({"mensagem": "Salvo com sucesso!"})


@app.route("/usuarios/adicionar", methods=["POST"])
def adicionar_usuario():
    nome = request.form.get("nome", "").strip()
    idade = request.form.get("idade", "").strip()
    turma = request.form.get("turma", request.form.get("profissao", "")).strip()
    tipo_pessoa = request.form.get("tipo_pessoa", "Aluno").strip()
    identificacao = request.form.get("identificacao", nome).strip()
    imagem = request.files.get("imagem")

    if not nome or not imagem:
        return jsonify({"erro": "Nome e uma imagem com um rosto sao obrigatorios."}), 400

    dados = ler_dados()
    if any(u.get("nome", "").casefold() == nome.casefold() for u in dados):
        return jsonify({"erro": "Ja existe um usuario com esse nome."}), 409

    try:
        imagem_bytes = imagem.read()
        imagem_rgb = face_recognition.load_image_file(io.BytesIO(imagem_bytes))
        localizacoes = face_recognition.face_locations(imagem_rgb)
        if len(localizacoes) != 1:
            return jsonify({"erro": "A imagem precisa ter exatamente um rosto."}), 400
        encoding = face_recognition.face_encodings(imagem_rgb, localizacoes)[0].tolist()
    except Exception as erro:
        return jsonify({"erro": f"Nao foi possivel processar a imagem: {erro}"}), 400

    os.makedirs(FACE_PHOTO_DIR, exist_ok=True)
    identificacao_segura = re.sub(r"[^A-Za-z0-9_-]+", "_", identificacao).strip("_") or "pessoa"
    foto_relativa = os.path.join("face_data", f"{identificacao_segura}.jpg")
    with open(os.path.join(os.path.dirname(DATA_FILE), foto_relativa), "wb") as arquivo:
        arquivo.write(imagem_bytes)

    dados.append({
        "nome": nome,
        "idade": idade,
        "turma": turma,
        "profissao": turma,
        "tipo_pessoa": tipo_pessoa,
        "id": identificacao,
        "foto": foto_relativa,
        "encoding": encoding,
    })
    if not salvar_dados(dados):
        return jsonify({"erro": "Nao foi possivel salvar a base de pessoas."}), 500
    return jsonify({"mensagem": "Rosto adicionado com sucesso!", "usuario": usuario_publico(dados[-1])}), 201


@app.route("/usuarios/<path:nome_original>", methods=["DELETE"])
def excluir_usuario(nome_original):
    dados = ler_dados()
    restantes = [u for u in dados if u.get("nome") != nome_original]
    if len(restantes) == len(dados):
        return jsonify({"erro": "Usuario nao encontrado."}), 404
    if not salvar_dados(restantes):
        return jsonify({"erro": "Nao foi possivel salvar a base de pessoas."}), 500
    return jsonify({"mensagem": "Usuario removido com sucesso!"})


@app.route("/registros", methods=["GET"])
def listar_registros():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    return jsonify(ler_csv(LOG_FILE))


@app.route("/atrasos", methods=["GET"])
def listar_atrasos():
    return jsonify(ler_csv(LATE_FILE))


@app.route("/atrasos/<int:indice>", methods=["DELETE"])
def excluir_atraso(indice):
    registros = ler_csv(LATE_FILE)
    if indice < 0 or indice >= len(registros):
        return jsonify({"erro": "Atraso nao encontrado."}), 404
    registros.pop(indice)
    cabecalho = ["Data", "Horario", "Nome", "Turma", "Tipo", "Status", "Identificacao", "Evidencia"]
    with open(LATE_FILE, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=cabecalho, delimiter=";")
        escritor.writeheader()
        escritor.writerows(registros)
    return jsonify({"mensagem": "Atraso excluido."})


@app.route("/atrasos/<int:indice>", methods=["PUT"])
def editar_atraso(indice):
    registros = ler_csv(LATE_FILE)
    if indice < 0 or indice >= len(registros):
        return jsonify({"erro": "Atraso nao encontrado."}), 404
    alteracoes = request.get_json(silent=True) or {}
    for chave in ("Data", "Horario", "Nome", "Turma", "Status"):
        if chave in alteracoes:
            registros[indice][chave] = str(alteracoes[chave]).strip()
    cabecalho = ["Data", "Horario", "Nome", "Turma", "Tipo", "Status", "Identificacao", "Evidencia"]
    with open(LATE_FILE, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=cabecalho, delimiter=";")
        escritor.writeheader()
        escritor.writerows(registros)
    return jsonify({"mensagem": "Atraso atualizado."})


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if request.method == "GET":
        return jsonify(ler_configuracao())
    novos = request.get_json(silent=True)
    if not isinstance(novos, dict):
        return jsonify({"erro": "Configuracao invalida."}), 400
    configuracao = ler_configuracao()
    for chave in DEFAULT_CONFIG:
        if chave in novos:
            configuracao[chave] = novos[chave]
    arquivo_temporario = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=os.path.dirname(CONFIG_FILE), delete=False
    )
    with arquivo_temporario as arquivo:
        json.dump(configuracao, arquivo, indent=2, ensure_ascii=False)
        arquivo.flush()
        os.fsync(arquivo.fileno())
    os.replace(arquivo_temporario.name, CONFIG_FILE)
    return jsonify(configuracao)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    registros = ler_csv(LOG_FILE)
    atrasos = ler_csv(LATE_FILE)
    hoje = __import__("datetime").datetime.now().strftime("%d/%m/%Y")
    do_dia = [r for r in registros if r.get("Data") == hoje]
    return jsonify({
        "alunos_reconhecidos": len({r.get("Identificacao") for r in do_dia if r.get("Tipo") == "Aluno"}),
        "atrasos": len([r for r in atrasos if r.get("Data") == hoje]),
        "professores": len([r for r in do_dia if r.get("Tipo") == "Professor"]),
        "funcionarios": len([r for r in do_dia if r.get("Tipo") == "Funcionario"]),
        "ultimas_entradas": do_dia[-10:][::-1],
    })


@app.route("/registros.csv", methods=["GET"])
def baixar_registros():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as arquivo:
            csv.writer(arquivo, delimiter=";").writerow(["Data", "Horario", "Nome", "Idade", "Profissao"])
    return send_file(LOG_FILE, as_attachment=True, download_name="registros_reconhecimento.csv")


@app.route("/atrasos.csv", methods=["GET"])
def baixar_atrasos():
    if not os.path.exists(LATE_FILE):
        with open(LATE_FILE, "w", newline="", encoding="utf-8-sig") as arquivo:
            csv.writer(arquivo, delimiter=";").writerow(["Data", "Horario", "Nome", "Turma", "Tipo", "Status", "Identificacao", "Evidencia"])
    return send_file(LATE_FILE, as_attachment=True, download_name="historico_atrasos.csv")


if __name__ == "__main__":
    print(f"🚀 Servidor iniciado. Lendo dados de: {DATA_FILE}")
    app.run(port=5000)
