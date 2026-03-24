# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file — TOEIC Speaking Pro
# Usage:  pyinstaller toeic_pro.spec  (run from toeic_simulator/ directory)
# Output: dist/TOEIC_Speaking_Pro  folder  +  TOEIC_Speaking_Pro.exe inside

import os
import sys

block_cipher = None

# ── Source directory ──────────────────────────────────────────────────────────
SRC = os.path.dirname(os.path.abspath(SPEC))

# ── Data files to bundle ──────────────────────────────────────────────────────
# Only include files/directories that actually exist at build time
_extra_datas = []
for fname in ('question_bank.json', 'questions.json',
              'answer_templates.json', 'question_bank.xlsx'):
    fpath = os.path.join(SRC, fname)
    if os.path.isfile(fpath):
        _extra_datas.append((fpath, '.'))

_img_dir = os.path.join(SRC, 'images')
if os.path.isdir(_img_dir):
    _extra_datas.append((_img_dir, 'images'))

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(SRC, 'main.py')],
    pathex=[SRC],
    binaries=[],
    datas=_extra_datas,
    hiddenimports=[
        # ── Application modules (ensure all are bundled) ──
        'engine',
        'window',
        'recorder',
        'tts_manager',
        'license_manager',
        'marks_manager',
        'review_engine',
        'voice_scorer',
        # ── pyttsx3 TTS drivers (Windows SAPI5 is primary) ──
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'pyttsx3.drivers.nsss',
        'pyttsx3.drivers.espeak',
        # ── PyQt6 ──
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # ── vosk STT (optional feature) ──
        'vosk',
        # ── openpyxl xlsx loader ──
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.styles.differential',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        # ── websocket-client (voice scoring) ──
        'websocket',
        'websocket._core',
        'websocket._exceptions',
        'websocket._http',
        'websocket._logging',
        'websocket._socket',
        'websocket._ssl_compat',
        'websocket._utils',
        # ── stdlib extras that PyInstaller sometimes misses ──
        'wave',
        'json',
        'csv',
        'hmac',
        'hashlib',
        'base64',
        'xml.etree.ElementTree',
        'urllib.parse',
        'wsgiref.handlers',
        'threading',
        'subprocess',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter',
        'matplotlib', 'numpy', 'scipy',
        'PIL', 'IPython', 'notebook',
        'pandas', 'sqlalchemy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── One-file EXE ──────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TOEIC_Speaking_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window (windowed mode)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment next line and provide icon.ico to set a custom app icon:
    # icon=os.path.join(SRC, 'icon.ico'),
)
