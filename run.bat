@echo off
setlocal

echo ==========================================================
echo X-Booking Development Environment Setup
echo ==========================================================
echo.

echo Checking Poetry installation...
where poetry >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Poetry not found. Please install Poetry:
    echo https://python-poetry.org/docs/#installation
    exit /b 1
)
echo   [OK] Poetry found

echo Checking Bun installation...
where bun >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Bun not found. Please install Bun:
    echo https://bun.sh/
    exit /b 1
)
echo   [OK] Bun found

echo.
echo Installing Python dependencies with Poetry...
call poetry install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Python dependencies
    exit /b 1
)

echo.
echo Installing Node.js dependencies with Bun...
if exist package.json (
    call bun install
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Bun dependencies
        exit /b 1
    )
)

echo.
echo Starting development server on port 8008...
echo Press Ctrl+C to stop
echo.

call bun run dev

exit /b 0
