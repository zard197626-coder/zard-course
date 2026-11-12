@echo off
setlocal EnableExtensions
chcp 65001 >nul
title 校园集 - 一键启动
cd /d "%~dp0"

set "URL=http://127.0.0.1:8000/"
set "VENV_PY=%CD%\.venv\Scripts\python.exe"
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"

echo ==========================================
echo    校园集 · 校园二手交易平台
echo ==========================================
echo.

REM 如果本项目已经启动，直接打开浏览器，避免端口冲突。
curl.exe -s --max-time 2 "http://127.0.0.1:8000/api/health" 2>nul | findstr /C:"campus-market" >nul
if not errorlevel 1 (
    echo [信息] 服务已经在运行，正在打开浏览器...
    start "" "%URL%"
    ping 127.0.0.1 -n 3 >nul
    exit /b 0
)

REM 检查现有虚拟环境是否可用；损坏则重建。
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [提示] 现有 .venv 无法运行，将重新创建...
        rmdir /s /q ".venv"
    )
)

if not exist "%VENV_PY%" (
    echo [1/3] 未找到虚拟环境，正在创建...
    call :find_python
    if errorlevel 1 goto :no_python
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :venv_error
)

if not exist "%VENV_PY%" goto :venv_error

"%VENV_PY%" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [2/3] 正在安装项目依赖...
    "%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 goto :install_error
) else (
    echo [2/3] 项目依赖已安装
)

if not exist "backend\data\campus_market.db" (
    echo [3/3] 首次运行，正在初始化数据库...
    "%VENV_PY%" -m backend.seed
    if errorlevel 1 goto :seed_error
    echo.
    echo [重要] 请记住上方显示的初始管理员和演示账号密码。
    echo.
) else (
    echo [3/3] 数据库已存在，跳过初始化
)

echo.
echo 启动后浏览器会自动打开：
echo   %URL%
echo.
echo 停止服务：按 Ctrl+C，或直接关闭本窗口。
echo ==========================================
echo.

REM 延迟打开浏览器，给 Uvicorn 留出启动时间。
start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process '%URL%'"

"%VENV_PY%" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
echo.
echo 服务已停止。
pause
exit /b 0

:find_python
set "PYTHON_CMD="
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD exit /b 1
exit /b 0

:no_python
echo.
echo [错误] 未找到 Python。
echo        请安装 Python 3.10 或更高版本，安装时勾选 "Add Python to PATH"，
echo        然后重新双击本脚本。
echo.
pause
exit /b 1

:venv_error
echo.
echo [错误] 创建虚拟环境失败。
echo        请确认 Python 安装完整，并且当前目录有写入权限。
echo.
pause
exit /b 1

:install_error
echo.
echo [错误] 依赖安装失败。
echo        请检查网络连接，然后在此窗口手动执行：
echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
pause
exit /b 1

:seed_error
echo.
echo [错误] 数据库初始化失败。
echo        请查看上方错误信息，或删除 backend\data 后重试。
echo.
pause
exit /b 1
