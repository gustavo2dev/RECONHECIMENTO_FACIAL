@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Execute instalar_windows.bat primeiro.
    pause
    exit /b 1
)

if not exist "frontend\node_modules\electron\cli.js" (
    echo Dependencias do frontend nao encontradas. Execute instalar_windows.bat primeiro.
    pause
    exit /b 1
)

if not exist "backend\shape_predictor_68_face_landmarks.dat" (
    echo Modelo ausente: backend\shape_predictor_68_face_landmarks.dat
    pause
    exit /b 1
)

if not exist "backend\dlib_face_recognition_resnet_model_v1.dat" (
    echo Modelo ausente: backend\dlib_face_recognition_resnet_model_v1.dat
    pause
    exit /b 1
)

start "Reconhecimento facial" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" server.py
start "Painel administrativo" /D "%~dp0backend\admin" "%~dp0.venv\Scripts\python.exe" admin_server.py
timeout /t 2 /nobreak >nul
start "Painel administrativo no navegador" http://localhost:5000
start "Aplicacao Electron" /D "%~dp0frontend" cmd /k npm start

echo Servicos iniciados. Feche as janelas dos processos para encerrar o projeto.
exit /b 0