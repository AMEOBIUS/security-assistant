# 🔧 Podman CLI Not Found - Fix

## Проблема
```
podman: The term 'podman' is not recognized...
```

Podman Desktop установлен, но CLI нет в PATH.

---

## ✅ Решение 1: Установить Podman CLI

### Через winget (Проще всего):
```powershell
# Windows 11 или Windows 10 с winget
winget install RedHat.Podman

# Перезапусти PowerShell
# Проверь
podman --version
```

### Через Chocolatey:
```powershell
# Установи Chocolatey (если нет)
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Установи Podman
choco install podman-cli -y

# Перезапусти PowerShell
podman --version
```

### Вручную:
```powershell
# 1. Скачай installer
# https://github.com/containers/podman/releases/latest
# Файл: podman-v5.x.x-setup.exe

# 2. Запусти installer
# 3. Перезапусти PowerShell
# 4. Проверь
podman --version
```

---

## ✅ Решение 2: Использовать Podman Desktop GUI

**Без CLI!** Всё через интерфейс:

### 1. Открой Podman Desktop

### 2. Create Machine:
- **Settings** → **Resources**
- **Create new machine**
- **Provider:** Hyper-V
- **Click:** Create

### 3. Import Compose File:
- **Containers** → **Play Kubernetes YAML**
- Или: **Import** → `podman-compose.yml`

### 4. Start Containers:
- Click **Start** на каждом контейнере

---

## ✅ Решение 3: Docker Desktop (Альтернатива)

Если Podman сложно:

```powershell
# 1. Скачай Docker Desktop
# https://www.docker.com/products/docker-desktop/

# 2. Установи (выбери Hyper-V backend)

# 3. Переименуй compose file
cd C:\Workstation\backend
ren podman-compose.yml docker-compose.yml

# 4. Запусти
docker-compose up -d
```

---

## 🎯 Моя Рекомендация

**Попробуй по порядку:**

### 1. winget (30 секунд):
```powershell
winget install RedHat.Podman
# Перезапусти PowerShell
podman --version
```

### 2. Podman Desktop GUI (2 минуты):
- Открой Podman Desktop
- Create machine через GUI
- Import compose file

### 3. Docker Desktop (5 минут):
- Скачай и установи
- Переименуй compose file
- Работает сразу

---

## ⚡ Самый Быстрый Путь

**Если хочешь продолжить СЕЙЧАС:**

```powershell
# Установи Docker Desktop
# https://www.docker.com/products/docker-desktop/

# После установки:
cd C:\Workstation\backend
ren podman-compose.yml docker-compose.yml
docker-compose up -d
```

**Все файлы совместимы, никаких изменений не нужно!**

---

## 🤔 Что Делаешь?

**A)** Установить Podman CLI (winget/choco)  
**B)** Использовать Podman Desktop GUI  
**C)** Переключиться на Docker Desktop  

Скажи, и я дам точную инструкцию! 🎯
