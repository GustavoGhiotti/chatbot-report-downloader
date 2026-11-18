@echo off
setlocal
rem =====================================================================
rem  RoboBulkChatBot - Export diario do relatorio "Campanhas (Excel)"
rem  voxi.example (D-1)  ->  \\10.0.0.72\Automacao\RELATORIOS_CAMPANHAS_CHATBOT
rem  Uso: cadastrar este .bat no Agendador de Tarefas (1x/dia).
rem =====================================================================

rem Diretorio deste .bat (raiz do projeto) e entra nele
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

rem Ativa a venv se existir; caso contrario usa o Python do sistema
if exist "%PROJECT_DIR%.venv\Scripts\activate.bat" call "%PROJECT_DIR%.venv\Scripts\activate.bat"
if exist "%PROJECT_DIR%venv\Scripts\activate.bat" call "%PROJECT_DIR%venv\Scripts\activate.bat"

rem Log do agendador (a aplicacao tambem grava seu proprio log rotativo)
set "LOG_DIR=%PROJECT_DIR%src\infrastructure\logging\log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG=%LOG_DIR%\agendador.log"

echo.>> "%LOG%"
echo ==== Inicio %date% %time% ====>> "%LOG%"

python main.py >> "%LOG%" 2>&1
set "EXITCODE=%ERRORLEVEL%"

echo ==== Fim %date% %time% (exit=%EXITCODE%) ====>> "%LOG%"

rem Propaga o codigo de saida para o Agendador (0 = sucesso)
endlocal & exit /b %EXITCODE%
