# ================================================================
# ⚙️ Full-Stack Dev Launcher for Mini Project (Backend + Frontend)
# ================================================================

# 🧠 Adjust these paths according to your folder structure
$backendPath = "C:\Users\aryan\Downloads\mini-project-main\Backend"
$frontendPath = "C:\Users\aryan\Downloads\mini-project-main\Frontend"

# ================================================================
# 🧹 Step 1: Backend Setup
# ================================================================
Write-Host "`n🧹 Cleaning and preparing backend environment..." -ForegroundColor Cyan
cd $backendPath

# Remove old venv if exists
if (Test-Path "venv") {
    Write-Host "Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

# Create a new virtual environment
Write-Host "Creating new Python virtual environment..." -ForegroundColor Cyan
python -m venv venv

# Temporarily bypass execution policy
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1

# Upgrade pip and install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install fastapi uvicorn pymongo python-dotenv certifi google-generativeai rapidfuzz

# Verify uvicorn path
Write-Host "Checking uvicorn path..." -ForegroundColor DarkCyan
where.exe uvicorn

# ================================================================
# 🚀 Step 2: Start Backend Server in a NEW window
# ================================================================
Write-Host "`n🚀 Starting FastAPI backend server in a new PowerShell window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "cd `"$backendPath`"; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload" -WindowStyle Normal

# ================================================================
# 🧱 Step 3: Frontend Setup
# ================================================================
Write-Host " Setting up frontend (Vite + React)..." -ForegroundColor Cyan
cd $frontendPath

# Clean old build
if (Test-Path "node_modules") {
    Write-Host "Removing old node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "node_modules"
}
if (Test-Path "dist") {
    Write-Host "Removing old dist..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}

# Check for npm installation
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm not found! Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit
}

# Install frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
npm install

# Optional: build project (you can skip for dev)
# Write-Host "Building frontend..." -ForegroundColor Cyan
# npm run build

# ================================================================
# 🌐 Step 4: Start Frontend (Vite)
# ================================================================
Write-Host "`n🌐 Starting Vite development server..." -ForegroundColor Green
npm run dev

Write-Host "`n✅ All systems running! Backend on http://127.0.0.1:8000, Frontend on http://localhost:5173" -ForegroundColor Green
