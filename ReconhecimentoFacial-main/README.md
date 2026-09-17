# Sistema escolar de registro de entrada e atrasos

Sistema de reconhecimento facial em tempo real com visual corporativo, ideal para controle de acesso, demonstrações de IA ou estudos em visão computacional.

## 🎯 Funcionalidades

- 📸 Câmera exibida dentro do monitor Electron, sem janela OpenCV separada
- 🔍 Reconhecimento de alunos, professores e funcionários
- 🟢 Caixa verde para cadastrados e vermelha para rostos não cadastrados
- ⏰ Regras de atraso configuráveis para manhã e tarde
- 📊 Dashboard com histórico, filtros, exportação CSV e configurações
- 🌐 Comunicação de frames via WebSocket e logs em arquivo

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
│   ├── salvar_rosto.py         # Cadastro opcional de novos rostos
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

### 4. Inicie o sistema

Dê duplo clique em `iniciar_windows.bat`. Ele inicia os serviços minimizados e abre a tela de monitoramento com a câmera dentro da aplicação.
Os rostos que já estiverem em `backend\face_data.json` são aceitos automaticamente; não é necessário fazer outro cadastro.

O arquivo `salvar_rosto.py` existe apenas para cadastro manual alternativo. O cadastro normal pode ser feito no painel administrativo.

### 5. Use o painel e a planilha

O painel administrativo abre automaticamente em [http://localhost:5000](http://localhost:5000). Ele usa o mesmo `backend\face_data.json` do reconhecimento.

Quando um aluno autorizado for reconhecido no horário de atraso, o registro é salvo em `backend\atrasos.csv` e aparece no histórico. Passagens gerais ficam em `backend\registros.csv`.

Rostos desconhecidos são salvos com cooldown em `backend\rostos_nao_cadastrados\AAAA-MM-DD`. Evidências de atrasos ficam em `backend\registros\AAAA-MM-DD`. Logs ficam em `backend\logs\reconhecimento.log`.

### Regras padrão

- Manhã: 07:30 até 12:30, atraso a partir de 07:30.
- Tarde: 13:30 até 17:25, atraso a partir de 13:30.
- Cooldown padrão por pessoa: 60 minutos.

Esses valores podem ser alterados na aba **Configurações** do painel em [http://localhost:5000](http://localhost:5000). Apenas pessoas do tipo **Aluno** geram atraso escolar; professores e funcionários apenas aparecem nas passagens.

---

## 🧪 Exemplo de Interface

📷 O rosto é detectado com um quadrado animado, e as informações aparecem em um balão com destaque. A barra superior exibe o status do acesso.

---

## 📌 Sobre os Dados

Os usuários são armazenados no arquivo `face_data.json` com:

- Nome
- Idade
- Turma
- Tipo de pessoa
- Identificação
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
