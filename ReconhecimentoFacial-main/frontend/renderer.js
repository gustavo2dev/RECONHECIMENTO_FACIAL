const video = document.getElementById("webcam");
const canvas = document.getElementById("overlay");
const context = canvas.getContext("2d");
const frameCanvas = document.createElement("canvas");
const frameContext = frameCanvas.getContext("2d");

let socket = null;
let stream = null;
let envioAtivo = false;
let ultimaNotificacao = "";

function atualizarRelogio() {
  const agora = new Date();
  document.getElementById("dataAtual").textContent =
    agora.toLocaleDateString("pt-BR");
  document.getElementById("horaAtual").textContent =
    agora.toLocaleTimeString("pt-BR");
}

function statusCamera(online, texto) {
  const indicador = document.getElementById("statusCamera");
  indicador.className = `status-dot ${online ? "online" : "offline"}`;
  document.getElementById("statusCameraTexto").textContent = texto;
}

function desenharRostos(rostos) {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  context.clearRect(0, 0, canvas.width, canvas.height);
  for (const rosto of rostos) {
    const cor = rosto.reconhecido ? "#38d996" : "#ff756d";
    context.strokeStyle = cor;
    context.lineWidth = 4;
    context.strokeRect(
      rosto.left,
      rosto.top,
      rosto.right - rosto.left,
      rosto.bottom - rosto.top,
    );
    context.font = "bold 18px Segoe UI";
    context.fillStyle = cor;
    context.fillText(
      rosto.reconhecido ? rosto.nome : "Rosto não cadastrado",
      rosto.left,
      Math.max(24, rosto.top - 12),
    );
  }
}

function mostrarDeteccao(rostos) {
  const area = document.getElementById("ultimaDeteccao");
  const rosto = rostos[0];
  if (!rosto) {
    area.className = "empty-state";
    area.textContent = "Aguardando reconhecimento...";
    document.getElementById("statusReconhecimento").textContent =
      "Aguardando rosto";
    return;
  }
  area.className = `person-card ${rosto.reconhecido ? "known" : "unknown"}`;
  area.innerHTML = rosto.reconhecido
    ? `<strong>${rosto.nome}</strong><span>${rosto.tipo_pessoa === "Aluno" ? `${rosto.idade} anos · ${rosto.turma || "Turma não informada"}` : rosto.tipo_pessoa}</span>`
    : `<strong>Rosto não cadastrado</strong><span>A imagem foi salva para análise.</span>`;
  document.getElementById("statusReconhecimento").textContent =
    rosto.reconhecido ? `${rosto.nome} identificado` : "Rosto não cadastrado";
  if (
    rosto.novo_registro &&
    rosto.novo_registro.atraso &&
    rosto.novo_registro.nome !== ultimaNotificacao
  ) {
    ultimaNotificacao = rosto.novo_registro.nome;
    const notificacao = document.getElementById("notificacao");
    notificacao.textContent = `Atraso registrado: ${rosto.novo_registro.nome} — ${rosto.novo_registro.horario}`;
    notificacao.hidden = false;
    document.getElementById("ultimoRegistro").textContent =
      `${rosto.novo_registro.nome} · ${rosto.novo_registro.horario}`;
    setTimeout(() => {
      notificacao.hidden = true;
    }, 6000);
    atualizarDashboard();
  }
}

async function iniciarCamera() {
  if (stream) return;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();
    statusCamera(true, "Câmera funcionando");
    document.getElementById("cameraError").hidden = true;
    iniciarEnvioFrames();
  } catch (erro) {
    statusCamera(false, "Câmera desconectada");
    document.getElementById("cameraError").hidden = false;
    console.error("Falha na câmera", erro);
  }
}

function iniciarEnvioFrames() {
  if (envioAtivo) return;
  envioAtivo = true;
  const enviar = () => {
    if (
      video.readyState >= 2 &&
      socket &&
      socket.readyState === WebSocket.OPEN
    ) {
      frameCanvas.width = video.videoWidth;
      frameCanvas.height = video.videoHeight;
      frameContext.drawImage(video, 0, 0);
      frameCanvas.toBlob(
        (blob) =>
          blob &&
          socket &&
          socket.readyState === WebSocket.OPEN &&
          socket.send(blob),
        "image/jpeg",
        0.72,
      );
    }
    setTimeout(enviar, 250);
  };
  enviar();
}

function conectarReconhecimento() {
  socket = new WebSocket("ws://localhost:8765");
  socket.onopen = () => {
    statusCamera(true, "Câmera e reconhecimento conectados");
    iniciarCamera();
  };
  socket.onmessage = (evento) => {
    const dados = JSON.parse(evento.data);
    desenharRostos(dados.rostos || []);
    mostrarDeteccao(dados.rostos || []);
  };
  socket.onerror = () =>
    statusCamera(false, "Servidor de reconhecimento indisponível");
  socket.onclose = () => {
    statusCamera(false, "Reconhecimento desconectado");
    setTimeout(conectarReconhecimento, 3000);
  };
}

async function atualizarDashboard() {
  try {
    const resposta = await fetch("http://localhost:5000/dashboard");
    const dados = await resposta.json();
    document.getElementById("statAlunos").textContent =
      dados.alunos_reconhecidos;
    document.getElementById("statAtrasos").textContent = dados.atrasos;
    document.getElementById("statProfessores").textContent = dados.professores;
    document.getElementById("statFuncionarios").textContent =
      dados.funcionarios;
  } catch (erro) {
    console.warn("Dashboard indisponível", erro);
  }
}

setInterval(atualizarRelogio, 1000);
setInterval(atualizarDashboard, 10000);
atualizarRelogio();
atualizarDashboard();
conectarReconhecimento();
