import asyncio
import csv
import logging
import json
import os
from datetime import datetime, timedelta

import cv2
import dlib
import face_recognition
import numpy as np
import websockets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "face_data.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "registros.csv")
LATE_FILE = os.path.join(BASE_DIR, "atrasos.csv")
UNKNOWN_DIR = os.path.join(BASE_DIR, "rostos_nao_cadastrados")
EVIDENCE_DIR = os.path.join(BASE_DIR, "registros")
PREDICTOR_FILE = os.path.join(BASE_DIR, "shape_predictor_68_face_landmarks.dat")
FACE_MODEL_FILE = os.path.join(BASE_DIR, "dlib_face_recognition_resnet_model_v1.dat")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "reconhecimento.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "manha_inicio": "07:30",
    "manha_atraso": "07:30",
    "manha_fim": "12:30",
    "tarde_inicio": "13:30",
    "tarde_atraso": "13:30",
    "tarde_fim": "17:25",
    "cooldown_minutos": 60,
    "tolerancia": 0.5,
    "unknown_cooldown_minutos": 5,
}

for model_file in (PREDICTOR_FILE, FACE_MODEL_FILE):
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"Modelo facial ausente: {model_file}")


def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def salvar_json(caminho, dados):
    temporario = f"{caminho}.tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)
    os.replace(temporario, caminho)


if not os.path.exists(CONFIG_FILE):
    salvar_json(CONFIG_FILE, DEFAULT_CONFIG)


def carregar_pessoas():
    dados = carregar_json(DATA_FILE, [])
    pessoas = []
    for pessoa in dados:
        encoding = pessoa.get("encoding", [])
        if len(encoding) != 128:
            continue
        pessoas.append({
            "id": pessoa.get("id", pessoa.get("nome", "")),
            "nome": pessoa.get("nome", ""),
            "idade": pessoa.get("idade", ""),
            "turma": pessoa.get("turma", pessoa.get("profissao", "")),
            "tipo_pessoa": pessoa.get("tipo_pessoa", "Aluno"),
            "encoding": np.array(encoding),
        })
    return pessoas


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_FILE)
face_rec_model = dlib.face_recognition_model_v1(FACE_MODEL_FILE)
known_people = carregar_pessoas()
data_file_mtime = os.path.getmtime(DATA_FILE)
last_logged = {}
last_unknown = []


def config_atual():
    configuracao = DEFAULT_CONFIG.copy()
    configuracao.update(carregar_json(CONFIG_FILE, {}))
    return configuracao


def hora_minutos(valor):
    hora, minuto = map(int, valor.split(":")[:2])
    return hora * 60 + minuto


def status_horario(agora, configuracao):
    minutos = agora.hour * 60 + agora.minute
    turnos = (
        ("manha", "manha_inicio", "manha_atraso", "manha_fim"),
        ("tarde", "tarde_inicio", "tarde_atraso", "tarde_fim"),
    )
    for turno, inicio, atraso, fim in turnos:
        inicio_min = hora_minutos(configuracao[inicio])
        atraso_min = hora_minutos(configuracao[atraso])
        fim_min = hora_minutos(configuracao[fim])
        if inicio_min <= minutos <= fim_min:
            return turno, minutos >= atraso_min
    return None, False


def anexar_csv(caminho, cabecalho, linha):
    novo = not os.path.exists(caminho) or os.path.getsize(caminho) == 0
    with open(caminho, "a", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        if novo:
            escritor.writerow(cabecalho)
        escritor.writerow(linha)


def salvar_imagem(caminho, frame, box):
    top, right, bottom, left = box
    altura, largura = frame.shape[:2]
    margem = 35
    recorte = frame[max(0, top - margem):min(altura, bottom + margem), max(0, left - margem):min(largura, right + margem)]
    if recorte.size:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        cv2.imwrite(caminho, recorte)


def registrar_passagem(pessoa, frame, box):
    agora = datetime.now()
    configuracao = config_atual()
    chave = pessoa["id"]
    ultimo = last_logged.get(chave)
    cooldown = timedelta(minutes=float(configuracao["cooldown_minutos"]))
    if ultimo and agora - ultimo < cooldown:
        return None

    turno, em_atraso = status_horario(agora, configuracao)
    data = agora.strftime("%d/%m/%Y")
    horario = agora.strftime("%H:%M:%S")
    tipo = pessoa["tipo_pessoa"]
    evidencia = ""
    if tipo == "Aluno" and em_atraso:
        pasta = os.path.join(EVIDENCE_DIR, agora.strftime("%Y-%m-%d"))
        nome_arquivo = f"{agora.strftime('%H-%M-%S')}_{pessoa['nome'].replace(' ', '_')}.jpg"
        evidencia = os.path.join(pasta, nome_arquivo)
        salvar_imagem(evidencia, frame, box)
        anexar_csv(LATE_FILE, ["Data", "Horario", "Nome", "Turma", "Tipo", "Status", "Identificacao", "Evidencia"], [data, horario, pessoa["nome"], pessoa["turma"], tipo, "Atrasado", chave, evidencia])

    anexar_csv(LOG_FILE, ["Data", "Horario", "Nome", "Idade", "Turma", "Tipo", "Turno", "Atrasado", "Identificacao", "Evidencia"], [data, horario, pessoa["nome"], pessoa["idade"], pessoa["turma"], tipo, turno or "fora_do_turno", "Sim" if em_atraso and tipo == "Aluno" else "Nao", chave, evidencia])
    last_logged[chave] = agora
    logger.info("Passagem reconhecida: %s (%s), atraso=%s", pessoa["nome"], tipo, em_atraso and tipo == "Aluno")
    return {"atraso": bool(em_atraso and tipo == "Aluno"), "horario": horario, "nome": pessoa["nome"]}


def salvar_desconhecido(frame, box, encoding):
    global last_unknown
    agora = datetime.now()
    configuracao = config_atual()
    limite = timedelta(minutes=float(configuracao["unknown_cooldown_minutos"]))
    last_unknown = [(momento, item) for momento, item in last_unknown if agora - momento < limite]
    if any(face_recognition.compare_faces([item], encoding, tolerance=0.48)[0] for _, item in last_unknown):
        return False
    pasta = os.path.join(UNKNOWN_DIR, agora.strftime("%Y-%m-%d"))
    caminho = os.path.join(pasta, f"{agora.strftime('%H-%M-%S')}.jpg")
    salvar_imagem(caminho, frame, box)
    last_unknown.append((agora, encoding))
    logger.info("Rosto nao cadastrado salvo: %s", caminho)
    return True


def recarregar_se_necessario():
    global known_people, data_file_mtime
    atual = os.path.getmtime(DATA_FILE)
    if atual != data_file_mtime:
        known_people = carregar_pessoas()
        data_file_mtime = atual


def processar_frame(frame):
    recarregar_se_necessario()
    pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB)
    rostos = []
    faces = detector(rgb)
    conhecido = [np.array(pessoa["encoding"]) for pessoa in known_people]
    tolerancia = float(config_atual()["tolerancia"])
    for face in faces:
        shape = predictor(rgb, face)
        encoding = np.array(face_rec_model.compute_face_descriptor(rgb, shape))
        top, right, bottom, left = face.top() * 4, face.right() * 4, face.bottom() * 4, face.left() * 4
        pessoa = None
        if conhecido:
            matches = face_recognition.compare_faces(conhecido, encoding, tolerance=tolerancia)
            if True in matches:
                pessoa = known_people[matches.index(True)]
        box = [top, right, bottom, left]
        if pessoa:
            registro = registrar_passagem(pessoa, frame, box)
            rostos.append({"top": top, "right": right, "bottom": bottom, "left": left, "nome": pessoa["nome"], "idade": pessoa["idade"], "turma": pessoa["turma"], "tipo_pessoa": pessoa["tipo_pessoa"], "reconhecido": True, "atraso": bool(registro and registro["atraso"]), "novo_registro": registro})
        else:
            salvou = salvar_desconhecido(frame, box, encoding)
            rostos.append({"top": top, "right": right, "bottom": bottom, "left": left, "nome": "Rosto nao cadastrado", "idade": "", "turma": "", "tipo_pessoa": "", "reconhecido": False, "atraso": False, "novo_registro": None, "imagem_salva": salvou})
    return rostos


async def handler(websocket):
    logger.info("Cliente de camera conectado")
    try:
        async for mensagem in websocket:
            if not isinstance(mensagem, bytes):
                continue
            frame = cv2.imdecode(np.frombuffer(mensagem, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue
            resultado = processar_frame(frame)
            await websocket.send(json.dumps({"rostos": resultado, "verificado": bool(resultado)}))
    except websockets.exceptions.ConnectionClosed:
        logger.info("Cliente de camera desconectado")
    except Exception:
        logger.exception("Falha no processamento do frame")


async def main():
    logger.info("Servidor WebSocket iniciado em ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765, max_size=4 * 1024 * 1024):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
