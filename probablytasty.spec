# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ProbablyTasty
Builds standalone executable for Windows and Linux
"""

from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui/themes', 'src/ui/themes'),
        ('src/templates', 'src/templates'),
        ('icons', 'icons'),
    ],
    hiddenimports=[
        'sqlalchemy.dialects.sqlite',
        'pydantic',
        'recipe_scrapers',
        'bs4',
        'jinja2',
        'anthropic',
        'openai',
        'google.generativeai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
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
    [],
    exclude_binaries=True,
    name='ProbablyTasty',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/applebiter.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ProbablyTasty',
)
