# 🧠 Reconhecimento Facial com Dashboard Interativo

Sistema de reconhecimento facial em tempo real com visual corporativo, ideal para controle de acesso, demonstrações de IA ou estudos em visão computacional.

## 🎯 Funcionalidades

- 📸 Detecção facial em tempo real pela webcam
- 🔍 Reconhecimento de usuários cadastrados
- 🧱 Interface com estilo dashboard:
  - Borda animada no rosto (verde, vermelho ou azul)
  - Balão com informações do usuário (nome, idade, profissão)
  - Status visual no topo (✔ Acesso Liberado | ✖ Acesso Bloqueado | 🔎 Analisando)
- 🌐 Comunicação com WebSocket
- 🛠 Painel administrativo via navegador para editar/remover usuários

---

## 🧰 Tecnologias Usadas

- Python 3.8+
- OpenCV
- dlib
- face_recognition
- asyncio + websockets
- Flask (admin dashboard)

---

## 📂 Estrutura do Projeto

```
camera-ia-app/
├── backend/
│   ├── server.py                # Reconhecimento facial em tempo real
│   ├── salvar_rosto.py         # Cadastro de novos rostos
│   ├── face_data.json          # Dados dos usuários com encoding facial
│   ├── shape_predictor_68_face_landmarks.dat
│   ├── dlib_face_recognition_resnet_model_v1.dat
│   └── admin/
│       ├── admin_server.py     # API Flask para gerenciar os usuários
│       ├── index.html          # Interface de gerenciamento
│       └── styles.css
└── README.md
```

---

## 🚀 Como Executar no Windows

### 1. Instale os programas necessários

Instale:

- Python 3.10 ou 3.11 (marque **Add Python to PATH** durante a instalação)
- Node.js LTS
- Os drivers da sua webcam

### 2. Instale as dependências

Na pasta `ReconhecimentoFacial-main`, dê duplo clique em `instalar_windows.bat`.
Esse arquivo cria o ambiente virtual `.venv`, instala o backend e instala o Electron.

> Se o `dlib` falhar, confirme que está usando Python 3.10 ou 3.11. O `face-recognition` depende dele.

### 3. Modelos obrigatórios

O `instalar_windows.bat` baixa e extrai automaticamente os dois modelos para `backend/`.
É necessário ter conexão com a internet durante a instalação.

### 4. Cadastre seu rosto

`python backend\salvar_rosto.py`

Digite suas informações, posicione o rosto na câmera e pressione `c` para capturar.

### 5. Inicie o reconhecimento facial

Depois, dê duplo clique em `iniciar_windows.bat`. Ele abre o reconhecimento, o painel administrativo e a aplicação Electron.

### 6. (Opcional) Use o painel de gerenciamento

O painel administrativo abre automaticamente em [http://localhost:5000](http://localhost:5000). Ele usa o mesmo `backend\face_data.json` do reconhecimento.

Abra [http://localhost:5000](http://localhost:5000) no navegador.

---

## 🧪 Exemplo de Interface

📷 O rosto é detectado com um quadrado animado, e as informações aparecem em um balão com destaque. A barra superior exibe o status do acesso.

---

## 📌 Sobre os Dados

Os usuários são armazenados no arquivo `face_data.json` com:

- Nome
- Idade
- Profissão
- Encoding facial

---

## 💡 Possíveis Melhorias

- Armazenamento com banco de dados
- Login e permissões por usuário
- Deploy com Docker ou serverless
- Integração com APIs de segurança/controle de entrada

---

## 👨‍💻 Autor

Feito com 💻 e dedicação por **Allison Joanine de Araujo Ribeiro**  
📧 allisonjoanine@gmail.com  
🔗 [LinkedIn](https://linkedin.com/in/allisonjoanine) • [GitHub](https://github.com/AllisonJoanine)

---

## 📄 Licença

Este projeto é de uso livre para fins educacionais e experimentais.

```

---

# by Allison Joanine de Araujo Ribeiro
```
