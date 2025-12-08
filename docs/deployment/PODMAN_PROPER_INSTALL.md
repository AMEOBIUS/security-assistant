# 🐳 Podman for Windows - Правильная Установка

## Официальная Документация
https://github.com/containers/podman/blob/main/docs/tutorials/podman-for-windows.md

---

## 📋 Шаг 1: Установка Podman

### Скачай Podman Installer:
https://github.com/containers/podman/releases/latest

**Файл:** `podman-v5.x.x-setup.exe` (Windows installer)

### Установи:
1. Запусти `podman-v5.x.x-setup.exe`
2. Follow wizard
3. Finish installation
4. **Перезапусти PowerShell** (важно!)

### Проверь:
```powershell
podman --version
# Должно показать: podman version 5.x.x
```

---

## 📋 Шаг 2: Инициализация Podman Machine

### Создай машину:
```powershell
# Инициализация (создаёт WSL VM)
podman machine init

# Запуск
podman machine start

# Проверка
podman machine list
# Должно показать: running
```

### Если ошибка с WSL:
```powershell
# Установи Ubuntu в WSL
wsl --install -d Ubuntu

# Если ошибка 0x80070422, исправь Windows Update Service:
# 1. Win+R → services.msc
# 2. Найди "Windows Update"
# 3. Правый клик → Properties
# 4. Startup type: Automatic
# 5. Start service
# 6. Попробуй снова: wsl --install -d Ubuntu
```

---

## 📋 Шаг 3: Установка podman-compose

```powershell
# Установи через pip
pip install podman-compose

# Проверь
podman-compose --version
```

---

## 🚀 Шаг 4: Запуск Backend

```powershell
cd C:\Workstation\backend

# Запусти services
podman-compose up -d

# Проверь
podman ps
# Должно показать 2 контейнера: api, db

# Логи
podman-compose logs -f api

# Тест
curl http://localhost:8000/health
```

---

## 🐛 Troubleshooting

### Ошибка: "cannot connect to Podman socket"
```powershell
# Перезапусти machine
podman machine stop
podman machine start
```

### Ошибка: "WSL 2 installation is incomplete"
```powershell
# Скачай WSL kernel update:
# https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
# Установи и перезагрузись
```

### Ошибка 0x80070422 (Windows Update)
```powershell
# PowerShell as Admin:
Set-Service -Name wuauserv -StartupType Automatic
Start-Service -Name wuauserv

# Попробуй снова:
wsl --install -d Ubuntu
```

---

## 📊 Проверка Установки

```powershell
# 1. Podman CLI
podman --version
# ✅ podman version 5.x.x

# 2. Podman Machine
podman machine list
# ✅ NAME     VM TYPE  CREATED  LAST UP  CPUS  MEMORY  DISK SIZE
#    podman*  wsl      ...      running  2     2048MB  100GB

# 3. podman-compose
podman-compose --version
# ✅ podman-compose version 1.x.x

# 4. Containers
podman ps
# ✅ Shows running containers
```

---

## 🎯 Next Steps

После успешной установки:

```powershell
cd C:\Workstation\backend
podman-compose up -d
curl http://localhost:8000/health
start http://localhost:8000/docs
```

---

**Начинай с установки Podman installer!**

Download: https://github.com/containers/podman/releases/latest

Ищи файл: `podman-v5.x.x-setup.exe` 🚀
