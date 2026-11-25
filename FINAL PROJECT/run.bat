@echo off
setlocal enabledelayedexpansion
title Adaptive Logistics Intelligence System

echo ===============================================================================
echo        ADAPTIVE LOGISTICS INTELLIGENCE SYSTEM - AUTOMATIC LAUNCHER
echo ===============================================================================

:: 1. Identify Project Root Directory
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"
echo [*] Working Directory: %PROJECT_DIR%

:: 2. Detect Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] ERROR: Python 3 was not found in PATH.
        echo [*] Please install Python 3.9+ from https://www.python.org/
        pause
        exit /b 1
    ) else (
        set "PYTHON_EXE=py"
    )
) else (
    set "PYTHON_EXE=python"
)
echo [*] Python executable detected: %PYTHON_EXE%

:: 3. Check / Setup Virtual Environment
if not exist "%PROJECT_DIR%.venv\Scripts\activate.bat" (
    echo [*] Initial setup: Creating Python virtual environment in .venv...
    %PYTHON_EXE% -m venv "%PROJECT_DIR%.venv"
    if %errorlevel% neq 0 (
        echo [!] Virtual environment creation failed. Falling back to system Python.
        set "ACTUAL_PYTHON=%PYTHON_EXE%"
    ) else (
        call "%PROJECT_DIR%.venv\Scripts\activate.bat"
        set "ACTUAL_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
    )
) else (
    call "%PROJECT_DIR%.venv\Scripts\activate.bat"
    set "ACTUAL_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
)

:: 4. Verify Python Dependencies
echo [*] Verifying required Python packages...
"%ACTUAL_PYTHON%" -c "import streamlit, pandas, matplotlib, networkx, pytest" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing / updating required packages into virtual environment...
    "%ACTUAL_PYTHON%" -m pip install -r "%PROJECT_DIR%requirements.txt"
    if %errorlevel% neq 0 (
        echo [!] Warning: Online pip install failed. Checking offline packages directory...
        if exist "%PROJECT_DIR%offline_packages\*.whl" (
            echo [*] Installing from offline wheel cache...
            "%ACTUAL_PYTHON%" -m pip install --no-index --find-links="%PROJECT_DIR%offline_packages" -r "%PROJECT_DIR%requirements.txt"
        )
    )
) else (
    echo [*] All required Python packages are installed and ready.
)

:: 5. Verify C Shared Library
if not exist "%PROJECT_DIR%bin\logistics_c.dll" (
    echo [*] Compiled C library not found. Attempting automatic compilation with GCC...
    where gcc >nul 2>&1
    if %errorlevel% equ 0 (
        echo [*] GCC detected. Compiling C source files...
        if not exist "%PROJECT_DIR%bin" mkdir "%PROJECT_DIR%bin"
        pushd "%PROJECT_DIR%c_algorithms"
        gcc -O3 -shared -o ..\bin\logistics_c.dll linked_list.c stack.c queue.c priority_queue.c min_heap.c bst.c avl_tree.c red_black_tree.c b_tree.c splay_tree.c hash_table.c finite_state_machine.c quick_sort.c merge_sort.c heap_sort.c graph.c bfs.c dfs.c dijkstra.c prim.c kruskal.c
        popd
        if exist "%PROJECT_DIR%bin\logistics_c.dll" (
            echo [*] C library successfully compiled: bin\logistics_c.dll
        ) else (
            echo [!] C compilation failed.
        )
    ) else (
        echo [!] Warning: GCC not detected. Please ensure pre-compiled bin\logistics_c.dll is present.
    )
) else (
    echo [*] C Shared Library verified: bin\logistics_c.dll
)

:: 6. Initialize Database & Seed Data if Not Present
echo [*] Checking database integrity...
"%ACTUAL_PYTHON%" -c "import sys; sys.path.insert(0, r'%PROJECT_DIR%'); from backend.database import init_db, seed_sample_data; init_db(); seed_sample_data()"

:: 7. Dynamic Port Detection Starting at 8502 (avoiding occupied 8501)
echo [*] Scanning for available application port starting from 8502...
for /f "tokens=*" %%p in ('"%ACTUAL_PYTHON%" "%PROJECT_DIR%tools\find_port.py" 8502') do (
    set "APP_PORT=%%p"
)

if "%APP_PORT%"=="" (
    set "APP_PORT=8502"
)

echo [*] Dynamic Port Selected: %APP_PORT%
echo [*] Application URL: http://localhost:%APP_PORT%

:: 8. Start Streamlit Server (Streamlit automatically opens browser once listening)
echo ===============================================================================
echo  Application is running on Port %APP_PORT%
echo  Opening browser and starting server...
echo  Press Ctrl+C in this terminal window to stop the server.
echo ===============================================================================
"%ACTUAL_PYTHON%" -m streamlit run "%PROJECT_DIR%app.py" --server.port %APP_PORT% --server.headless false --server.runOnSave true

if %errorlevel% neq 0 (
    echo.
    echo [!] Server stopped or encountered an error.
    pause
)
