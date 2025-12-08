# Doppler Setup Complete - Session 25

**Date:** 2025-12-04  
**Status:** ✅ READY FOR TESTING

---

## ✅ Что Настроено

### 1. Doppler CLI
- ✅ Установлен
- ✅ Авторизован (logged in)

### 2. Проект
- **Название:** `security-workstation`
- **Окружения:** dev, staging, production

### 3. Секреты
- **Источник:** `.env` файл
- **Окружение:** dev (по умолчанию)

---

## 🚀 Быстрый Старт

### Запустить Backend с Doppler

```powershell
# Перейти в backend
cd C:\Workstation\backend

# Запустить с Doppler
doppler run -- uvicorn app.main:app --reload
```

**Ожидаемый результат:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Проверить:**
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/health - Health check
- http://localhost:8000/config - Configuration info

---

## 🔧 Полезные Команды

### Просмотр Секретов

```powershell
# Все секреты (значения скрыты)
doppler secrets

# Конкретный секрет
doppler secrets get DATABASE_URL

# Скачать в .env.local (для инструментов без Doppler)
doppler secrets download --no-file --format env > .env.local
```

### Управление Секретами

```powershell
# Добавить/изменить секрет
doppler secrets set KEY="value"

# Удалить секрет
doppler secrets delete KEY

# Импортировать из файла
doppler secrets upload .env
```

### Переключение Окружений

```powershell
# Переключиться на staging
doppler setup --config staging

# Переключиться обратно на dev
doppler setup --config dev

# Посмотреть текущее окружение
doppler configure get
```

---

## 🐳 Docker Integration

### Генерация Service Token

```powershell
# Для локальной разработки
doppler configs tokens create local-dev --project security-workstation --config dev

# Сохранить токен (показывается только один раз!)
# Пример: dp.st.dev.xxxxxxxxxxxxxxxxxxxx
```

### Использование с Podman

```powershell
# Установить токен в переменную окружения
$env:DOPPLER_TOKEN="dp.st.dev.xxxxxxxxxxxxxxxxxxxx"

# Запустить с podman-compose
cd backend
podman-compose up -d

# Проверить логи
podman-compose logs -f api
```

---

## 📊 Мониторинг

### Audit Logs

```powershell
# Посмотреть активность
doppler activity

# Активность конкретного окружения
doppler activity --config production
```

### Dashboard

Откройте: https://dashboard.doppler.com

**Что можно делать:**
- Просматривать секреты
- Управлять токенами
- Настраивать интеграции (Slack, email)
- Просматривать audit logs
- Управлять доступом команды

---

## 🧪 Тестирование

### Test 1: Local Development

```powershell
cd C:\Workstation\backend
doppler run -- uvicorn app.main:app --reload
```

**Проверить:**
```powershell
# В другом терминале
curl http://localhost:8000/health
curl http://localhost:8000/config
```

### Test 2: Configuration Loading

```powershell
# Проверить, что settings загружаются из Doppler
doppler run -- python -c "from app.config import settings; print(f'Database: {settings.database_url}'); print(f'App: {settings.app_name}')"
```

### Test 3: Docker with Doppler

```powershell
# Сгенерировать токен
$token = doppler configs tokens create test-token --project security-workstation --config dev --plain

# Установить токен
$env:DOPPLER_TOKEN=$token

# Запустить контейнер
cd backend
podman-compose up -d

# Проверить
curl http://localhost:8000/health
```

---

## 🔄 Staging & Production Setup

### Staging Environment

```powershell
# Переключиться на staging
doppler setup --config staging

# Скопировать секреты из dev (опционально)
doppler secrets download --config dev --format env | doppler secrets upload --config staging

# Или установить вручную
doppler secrets set DATABASE_URL="postgresql://user:pass@staging-db:5432/db" --config staging
doppler secrets set ALLOWED_ORIGINS="https://staging.securityworkstation.ai" --config staging
```

### Production Environment

```powershell
# Переключиться на production
doppler setup --config production

# ВАЖНО: НЕ копировать из dev! Установить вручную
doppler secrets set DATABASE_URL="postgresql://user:pass@prod-db:5432/db" --config production
doppler secrets set ALLOWED_ORIGINS="https://securityworkstation.ai" --config production
doppler secrets set OPENAI_API_KEY="sk-prod-..." --config production
# ... установить все production секреты

# Сгенерировать production service token
doppler configs tokens create production-api --project security-workstation --config production
```

---

## 🔐 Security Best Practices

### 1. Service Tokens

```powershell
# Для каждого окружения - отдельный токен
doppler configs tokens create dev-local --config dev
doppler configs tokens create staging-deploy --config staging
doppler configs tokens create prod-deploy --config production

# Для CI/CD - read-only токен (если возможно)
doppler configs tokens create github-actions --config production
```

### 2. Audit Logs

```powershell
# Регулярно проверять активность
doppler activity

# Настроить уведомления в Dashboard:
# https://dashboard.doppler.com → Settings → Integrations
```

### 3. Access Control

В Dashboard:
- Settings → Team Members
- Настроить роли (Admin, Developer, Viewer)
- Ограничить доступ к production

---

## 📝 Troubleshooting

### "Not logged in"

```powershell
doppler logout
doppler login
```

### "Project not found"

```powershell
# Проверить список проектов
doppler projects

# Создать проект
doppler projects create security-workstation
```

### "Secrets not loading"

```powershell
# Проверить текущую конфигурацию
doppler configure get

# Переустановить
doppler setup --project security-workstation --config dev
```

### "Invalid token" в Docker

```powershell
# Проверить токен
echo $env:DOPPLER_TOKEN

# Сгенерировать новый
doppler configs tokens create new-token --config dev
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [DOPPLER_QUICK_START.md](DOPPLER_QUICK_START.md) | 5-минутная установка |
| [DOPPLER_MIGRATION_GUIDE.md](DOPPLER_MIGRATION_GUIDE.md) | Полное руководство |
| [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) | Security fixes |
| [SESSION_25_COMPLETE.md](SESSION_25_COMPLETE.md) | Полная сводка сессии |

---

## ✅ Checklist

- [x] Doppler CLI установлен
- [x] Авторизован в Doppler
- [x] Проект создан
- [x] Окружения созданы (dev/staging/production)
- [x] Секреты импортированы в dev
- [ ] Backend протестирован с Doppler
- [ ] Service token сгенерирован
- [ ] Docker протестирован с Doppler
- [ ] Staging environment настроен
- [ ] Production environment настроен
- [ ] CI/CD интеграция настроена

---

## 🎯 Next Steps

1. **Тестирование** (10 минут)
   ```powershell
   cd backend
   doppler run -- uvicorn app.main:app --reload
   ```

2. **Docker Integration** (15 минут)
   - Сгенерировать service token
   - Протестировать с podman-compose

3. **Staging Setup** (30 минут)
   - Настроить staging окружение
   - Установить staging секреты

4. **Production Setup** (1 час)
   - Настроить production окружение
   - Установить production секреты
   - Сгенерировать production tokens

5. **CI/CD Integration** (1 час)
   - Добавить DOPPLER_TOKEN в GitHub Secrets
   - Обновить .github/workflows

---

**Status:** ✅ Ready for Testing

**Next:** Run `cd backend && doppler run -- uvicorn app.main:app --reload`
