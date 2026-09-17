@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo Python nao foi encontrado. Instale Python 3.10 ou 3.11 e marque "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual Python...
    py -3 -m venv .venv
    if errorlevel 1 goto :erro
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install dlib-bin
python -m pip install -r "backend\requirements.txt" --no-deps
python -m pip install opencv-python numpy websockets Flask flask-cors face-recognition-models click Pillow
if errorlevel 1 goto :erro

where npm >nul 2>&1
if errorlevel 1 (
    echo Node.js/npm nao foi encontrado. Instale a versao LTS em https://nodejs.org/.
    pause
    exit /b 1
)

call npm install --prefix "frontend"
if errorlevel 1 goto :erro

if not exist "backend\shape_predictor_68_face_landmarks.dat" (
    echo Baixando modelo de pontos faciais...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2' -OutFile 'backend\shape_predictor_68_face_landmarks.dat.bz2'"
    if errorlevel 1 goto :erro
    python -c "import bz2,pathlib; p=pathlib.Path('backend/shape_predictor_68_face_landmarks.dat.bz2'); pathlib.Path('backend/shape_predictor_68_face_landmarks.dat').write_bytes(bz2.open(p, 'rb').read()); p.unlink()"
    if errorlevel 1 goto :erro
)

if not exist "backend\dlib_face_recognition_resnet_model_v1.dat" (
    echo Baixando modelo de reconhecimento facial...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2' -OutFile 'backend\dlib_face_recognition_resnet_model_v1.dat.bz2'"
    if errorlevel 1 goto :erro
    python -c "import bz2,pathlib; p=pathlib.Path('backend/dlib_face_recognition_resnet_model_v1.dat.bz2'); pathlib.Path('backend/dlib_face_recognition_resnet_model_v1.dat').write_bytes(bz2.open(p, 'rb').read()); p.unlink()"
    if errorlevel 1 goto :erro
)

echo.
echo Instalacao concluida.
echo Os modelos faciais estao instalados em backend.
pause
exit /b 0

:erro
echo.
echo A instalacao falhou. Confira a mensagem acima.
pause
exit /b 1