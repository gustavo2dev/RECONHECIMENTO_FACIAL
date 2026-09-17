# Sistema escolar de reconhecimento facial

Sistema Windows para monitorar a entrada escolar, reconhecer alunos, professores e funcionários e registrar atrasos de alunos.

## Estrutura

```text
backend/
  admin/              Painel Flask e APIs
  data/               face_data.json, config.json e CSVs gerados
    face_data/        Fotos dos cadastros
  records/            Evidências de atrasos por data
  logs/               Logs do reconhecimento e do painel
  server.py           WebSocket e processamento facial
  salvar_rosto.py     Cadastro manual opcional
  *.dat               Modelos do dlib
frontend/
  index.html          Monitor da câmera
  renderer.js         Webcam, WebSocket e interface
  main.js             Janela Electron
iniciar_windows.bat
instalar_windows.bat
```

## Instalação e início

1. Instale Python 3.10/3.11 e Node.js LTS.
2. Execute `instalar_windows.bat`.
3. Execute `iniciar_windows.bat`.
4. Na tela Electron, clique em **Iniciar câmera**.
5. O painel administrativo abre em `http://localhost:5000`.

Os servidores Python são iniciados minimizados. Erros ficam em `backend/logs/`.

## Regras padrão

- Manhã: 07:30 até 12:30.
- Tarde: 13:30 até 17:25.
- Cooldown de registro por pessoa: 60 minutos.
- Tolerância facial: 0.5.

Os horários, cooldown e tolerância podem ser alterados na aba **Configurações** do painel. A configuração ativa fica em `backend/data/config.json`.

Somente pessoas do tipo **Aluno** geram atraso. Professores e funcionários podem ser reconhecidos e registrados como passagem, mas não geram atraso escolar.

## Dados

- Pessoas e encodings: `backend/data/face_data.json`.
- Fotos dos cadastros: `backend/data/face_data/`.
- Passagens: `backend/data/registros.csv`.
- Atrasos: `backend/data/atrasos.csv`.
- Evidências de atrasos: `backend/records/AAAA-MM-DD/`.
- Logs: `backend/logs/`.

Rostos não cadastrados apenas aparecem com caixa vermelha. Eles não são salvos, não geram atraso e não entram em histórico.

## Desempenho

O backend mantém configurações e encodings em memória e recarrega os arquivos somente quando mudam. A comparação escolhe o encoding mais próximo dentro da tolerância configurada. O frontend envia um novo frame somente depois da resposta anterior, evitando fila e atraso acumulado.

## Dependências principais

Python: OpenCV, dlib-bin, face-recognition, NumPy, websockets, Flask e Flask-CORS.

Frontend: Electron.
