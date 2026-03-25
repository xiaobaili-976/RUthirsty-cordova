# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — HR Manager
# Usage: pyinstaller hr_manager.spec  (run from hr_manager/ directory)

import os

block_cipher = None
SRC = os.path.dirname(os.path.abspath(SPEC))

_extra_datas = []
for fname in ('data/hr_manager.db',):
    fpath = os.path.join(SRC, fname)
    if os.path.isfile(fpath):
        _extra_datas.append((fpath, 'data'))

a = Analysis(
    [os.path.join(SRC, 'main.py')],
    pathex=[SRC],
    binaries=[],
    datas=_extra_datas,
    hiddenimports=[
        # App modules
        'db.crypto', 'db.database', 'db.models',
        'managers.auth_manager', 'managers.employee_manager',
        'managers.contract_manager', 'managers.salary_manager',
        'managers.position_manager', 'managers.esop_manager',
        'managers.stability_manager', 'managers.backup_manager',
        'widgets.nav_bar', 'widgets.sidebar', 'widgets.right_drawer',
        'widgets.ring_chart',
        'pages.dashboard_page', 'pages.org_page', 'pages.employee_page',
        'pages.contract_page', 'pages.salary_page', 'pages.position_page',
        'pages.esop_page', 'pages.stability_page',
        'dialogs.login_dialog', 'dialogs.employee_form', 'dialogs.contract_form',
        'dialogs.salary_form', 'dialogs.position_form', 'dialogs.esop_form',
        'dialogs.stability_form', 'dialogs.settings_dialog',
        'styles', 'window',
        # PyQt6
        'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
        'PyQt6.QtSvg', 'PyQt6.sip',
        # Crypto + auth
        'cryptography', 'cryptography.fernet',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.backends',
        'bcrypt',
        # Data
        'openpyxl', 'openpyxl.styles', 'openpyxl.utils',
        # stdlib
        'sqlite3', 'json', 'csv', 'hashlib', 'hmac', 'base64',
        'threading', 'datetime', 'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter',
        'matplotlib', 'numpy', 'scipy',
        'IPython', 'notebook', 'pandas', 'sqlalchemy',
        'pyttsx3', 'pyaudio', 'vosk', 'websocket',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HR_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir='%LOCALAPPDATA%\\HR_Manager',
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SRC, 'app_icon.ico') if os.path.isfile(
        os.path.join(SRC, 'app_icon.ico')) else None,
)
