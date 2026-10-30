@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m tools.install %*
    goto done
)
where python >nul 2>nul
if not errorlevel 1 (
    python -m tools.install %*
    goto done
)
echo Instala Python 3.10 o posterior y vuelve a ejecutar este archivo.
:done
pause
