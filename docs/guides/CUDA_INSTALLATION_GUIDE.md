# CUDA Installation Guide - Windows 11

## 📊 Current Status (Session 28)

**Completed:**
- ✅ Python 3.14 installed
- ✅ 104 Python packages installed
- ✅ Node.js v24.11.1 LTS installed
- ✅ npm 11.6.2 installed
- ✅ 270 npm packages installed

**Next:** CUDA Toolkit installation

---

## 🎯 Recommended CUDA Version

**CUDA Toolkit 12.6.3** (Latest stable as of December 2025)

### Why CUDA 12.6:
- ✅ Best performance for RTX 40xx/30xx/20xx series
- ✅ Compatible with Python 3.14
- ✅ Supports latest PyTorch, TensorFlow, CuPy
- ✅ Improved ML/AI performance
- ✅ Better memory management

---

## 📥 Download CUDA Toolkit

### Option 1: Network Installer (Recommended)
**URL:** https://developer.nvidia.com/cuda-downloads

**Steps:**
1. Select: Windows → x86_64 → 11 → exe (network)
2. Download: `cuda_12.6.3_windows_network.exe` (~3 MB)
3. Installer downloads components during installation

### Option 2: Local Installer (Offline)
**URL:** https://developer.nvidia.com/cuda-downloads

**Steps:**
1. Select: Windows → x86_64 → 11 → exe (local)
2. Download: `cuda_12.6.3_windows.exe` (~3.5 GB)
3. All components included

### Direct Links:
```
Network: https://developer.download.nvidia.com/compute/cuda/12.6.3/network_installers/cuda_12.6.3_windows_network.exe
Local: https://developer.download.nvidia.com/compute/cuda/12.6.3/local_installers/cuda_12.6.3_windows.exe
```

---

## 🔧 Installation Steps

### 1. Pre-Installation Checks

**Check GPU:**
```powershell
# Open PowerShell and run:
nvidia-smi
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 560.xx       Driver Version: 560.xx       CUDA Version: 12.6   |
|-------------------------------+----------------------+----------------------+
| GPU  Name            TCC/WDDM | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  WDDM | 00000000:01:00.0  On |                  N/A |
```

**If nvidia-smi fails:**
- Update GPU drivers first: https://www.nvidia.com/Download/index.aspx
- Reboot after driver update

### 2. Run CUDA Installer

**Launch installer:**
```powershell
# Run as Administrator
.\cuda_12.6.3_windows_network.exe
```

**Installation Options:**

**Express (Recommended):**
- ✅ CUDA Toolkit
- ✅ CUDA Samples
- ✅ CUDA Documentation
- ✅ Driver components (if needed)
- ✅ Visual Studio Integration

**Custom (Advanced):**
Select only what you need:
- ✅ CUDA Toolkit (Required)
- ✅ CUDA Runtime Libraries (Required)
- ✅ CUDA Development Libraries (Required)
- ⚠️ CUDA Samples (Optional - 500MB)
- ⚠️ CUDA Documentation (Optional - 200MB)
- ⚠️ Visual Studio Integration (Optional - only if using VS)

### 3. Installation Path

**Default (Recommended):**
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6
```

**Custom path:** Only if you have specific requirements

### 4. Environment Variables

**Installer automatically sets:**
```
CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6
CUDA_PATH_V12_6=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6
```

**Added to PATH:**
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\libnvvp
```

---

## ✅ Post-Installation Verification

### 1. Verify CUDA Installation

**Check CUDA version:**
```powershell
nvcc --version
```

**Expected output:**
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on Wed_Oct_30_01:18:48_Pacific_Daylight_Time_2024
Cuda compilation tools, release 12.6, V12.6.85
Build cuda_12.6.r12.6/compiler.35059454_0
```

### 2. Verify GPU Detection

**Check CUDA devices:**
```powershell
nvidia-smi
```

**Should show CUDA Version: 12.6**

### 3. Test CUDA with Python

**Create test script:**
```python
# test_cuda.py
import sys
print(f"Python: {sys.version}")

try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU count: {torch.cuda.device_count()}")
except ImportError:
    print("PyTorch not installed yet")
```

**Run test:**
```powershell
python test_cuda.py
```

---

## 📦 Install cuDNN (Optional but Recommended)

**cuDNN** = CUDA Deep Neural Network library (for deep learning)

### Download cuDNN

**URL:** https://developer.nvidia.com/cudnn

**Version:** cuDNN 9.x for CUDA 12.6

**Steps:**
1. Login with NVIDIA account (free)
2. Download: `cudnn-windows-x86_64-9.x.x.x_cuda12-archive.zip`
3. Extract to temporary folder

### Install cuDNN

**Copy files to CUDA directory:**
```powershell
# Extract cudnn zip, then copy:
# From: cudnn-windows-x86_64-9.x.x.x_cuda12-archive\

# Copy bin files:
Copy-Item "bin\*.dll" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\"

# Copy include files:
Copy-Item "include\*.h" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\include\"

# Copy lib files:
Copy-Item "lib\x64\*.lib" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\lib\x64\"
```

---

## 🐍 Install Python CUDA Libraries

### After CUDA installation and reboot:

**PyTorch with CUDA 12.6:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

**TensorFlow with CUDA:**
```powershell
pip install tensorflow[and-cuda]
```

**CuPy for CUDA 12.x:**
```powershell
pip install cupy-cuda12x
```

**RAPIDS (Advanced - for data science):**
```powershell
pip install cudf-cu12 cuml-cu12 cugraph-cu12
```

---

## 🔍 Troubleshooting

### Issue: "nvcc not found"

**Solution:**
```powershell
# Check PATH:
$env:PATH -split ';' | Select-String "CUDA"

# If missing, add manually:
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin", [System.EnvironmentVariableTarget]::Machine)
```

### Issue: "CUDA driver version is insufficient"

**Solution:**
- Update GPU drivers: https://www.nvidia.com/Download/index.aspx
- Minimum driver version for CUDA 12.6: **560.x or higher**

### Issue: PyTorch doesn't detect CUDA

**Solution:**
```powershell
# Uninstall CPU version:
pip uninstall torch torchvision torchaudio

# Install CUDA version:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

---

## 📋 Installation Checklist

**Before reboot:**
- [ ] CUDA Toolkit 12.6.3 installed
- [ ] `nvcc --version` works
- [ ] `nvidia-smi` shows CUDA 12.6
- [ ] cuDNN copied (optional)
- [ ] Environment variables set

**After reboot:**
- [ ] `nvcc --version` still works
- [ ] Install PyTorch with CUDA
- [ ] Test `torch.cuda.is_available()`
- [ ] Run project tests
- [ ] Update checkpoint

---

## 🎯 Estimated Time

- **Download:** 5-10 minutes (network) or 15-30 minutes (local)
- **Installation:** 10-15 minutes
- **cuDNN setup:** 5 minutes
- **Verification:** 5 minutes
- **Total:** ~30-60 minutes

---

## 🚀 After Installation

**Reboot Windows 11** to ensure:
- CUDA drivers loaded
- Environment variables active
- GPU fully initialized

**Then continue Session 28:**
```powershell
# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Test CUDA
python test_cuda.py

# Run project tests
pytest tests/ -v

# Update checkpoint
python scripts/checkpoint_manager.py update --session 28 --completion 100 --status COMPLETED
```

---

## 📊 Your Project Benefits

**With CUDA installed, your project can:**
- ✅ Use GPU for ML model training (catboost, lightgbm)
- ✅ Accelerate data processing (pandas, numpy)
- ✅ Run AI-powered code analysis faster
- ✅ Use GPU for security scanning (if implemented)
- ✅ Future-proof for AI/ML features

**Without CUDA:**
- ⚠️ Everything still works (CPU only)
- ⚠️ ML tasks will be slower
- ⚠️ Limited to CPU-based analysis

---

## 🔗 Useful Links

- **CUDA Toolkit:** https://developer.nvidia.com/cuda-toolkit
- **cuDNN:** https://developer.nvidia.com/cudnn
- **PyTorch CUDA:** https://pytorch.org/get-started/locally/
- **TensorFlow GPU:** https://www.tensorflow.org/install/gpu
- **NVIDIA Drivers:** https://www.nvidia.com/Download/index.aspx
- **CUDA Documentation:** https://docs.nvidia.com/cuda/

---

**Created:** Session 28 - Windows 11 Migration
**Last Updated:** 2025-12-05
