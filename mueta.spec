# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Mueta
# Build with: pyinstaller mueta.spec

block_cipher = None

a = Analysis(
    ['src/mueta/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'mueta.cli',
        'mueta.core',
        'mueta.engine',
        'mueta.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tests',
        'pytest',
        'black',
        'pre-commit',
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
    name='mueta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip binary for smaller size
    upx=True,    # Use UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
