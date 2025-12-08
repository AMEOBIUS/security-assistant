# Windows 11 Migration Plan - Session 28

## 🔍 Current State Analysis

### Environment
- **OS**: Windows 11 (upgraded from Windows 10)
- **System Disk**: Changed (old files remain on previous disk)
- **Python**: 3.12.7 ✅
- **Node.js**: NOT FOUND ❌
- **npm**: NOT FOUND ❌

### Critical Issues Found

#### 1. Python Environment Corruption
**Errors:**
```
ModuleNotFoundError: No module named '_distutils_hack'
ModuleNotFoundError: No module named 'pywin32_bootstrap'
```

**Missing Core Dependencies (from pip check):**
- pydantic (required by 10+ packages)
- python-dotenv (required by agentrouter)
- pyyaml (required by bandit, huggingface-hub, optuna)
- requests (required by dash, docker, google-api-core)
- sqlalchemy (required by alembic, optuna)
- typing-extensions (required by 20+ packages)
- pywin32 (required by docker, mcp)
- rich (required by agentrouter, bandit)
- tenacity (required by agentrouter)
- And 50+ more...

#### 2. Node.js/npm Missing
- Frontend dependencies cannot be installed
- MCP servers cannot run
- Build scripts unavailable

#### 3. Frontend Structure
- `frontend/package.json` - NOT FOUND
- Only `frontend/landing/` directory exists
- Root `package.json` has MCP dependencies

## 🎯 Migration Strategy

### Phase 1: Python Environment Fix (PRIORITY 1)
1. **Fix setuptools/distutils**
   ```bash
   python -m pip install --upgrade --force-reinstall setuptools
   python -m pip install --upgrade --force-reinstall pip
   ```

2. **Fix pywin32**
   ```bash
   python -m pip install --upgrade --force-reinstall pywin32
   python Scripts/pywin32_postinstall.py -install
   ```

3. **Reinstall all requirements**
   ```bash
   python -m pip install --upgrade --force-reinstall -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python -m pip check
   pytest --version
   ```

### Phase 2: Node.js Installation (PRIORITY 1)
1. **Download Node.js LTS**
   - URL: https://nodejs.org/
   - Version: Latest LTS (20.x recommended)
   - Installer: Windows x64 MSI

2. **Install Node.js**
   - Add to PATH automatically
   - Include npm package manager
   - Include necessary tools for native modules

3. **Verify installation**
   ```bash
   node --version
   npm --version
   ```

4. **Install project dependencies**
   ```bash
   npm install
   ```

### Phase 3: Frontend Dependencies (PRIORITY 2)
1. **Check frontend/landing structure**
   ```bash
   cd frontend/landing
   npm install
   ```

2. **Verify Vercel deployment config**
   - Check `.vercel/` directory
   - Verify build settings

### Phase 4: Testing & Validation (PRIORITY 2)
1. **Run Python tests**
   ```bash
   pytest tests/ -v
   python scripts/checkpoint_manager.py validate --all
   ```

2. **Test backend**
   ```bash
   python backend/app.py
   ```

3. **Test MCP servers**
   ```bash
   npm run check:mcp
   ```

### Phase 5: Old Disk Migration (PRIORITY 3)
1. **Identify critical files on old disk**
   - Configuration files (.env, secrets)
   - Database files
   - Logs and reports
   - Custom scripts

2. **Copy to new location**
3. **Update paths in configs**
4. **Verify functionality**

## 📋 Execution Checklist

- [ ] Fix Python setuptools/distutils
- [ ] Fix pywin32
- [ ] Reinstall requirements.txt
- [ ] Verify pip check (no errors)
- [ ] Install Node.js LTS
- [ ] Verify node/npm versions
- [ ] Install root npm dependencies
- [ ] Check frontend/landing dependencies
- [ ] Run pytest suite
- [ ] Validate checkpoints
- [ ] Test backend startup
- [ ] Test MCP servers
- [ ] Document old disk files
- [ ] Migrate critical files
- [ ] Update checkpoint with results

## 🚨 Critical Notes

1. **DO NOT** delete old disk files until migration is verified
2. **BACKUP** current working directory before major changes
3. **TEST** each phase before proceeding to next
4. **DOCUMENT** all path changes in checkpoint
