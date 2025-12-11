# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ProbablyTasty
Builds standalone executable for Windows and Linux
"""

block_cipher = None

import os

spec_root = os.path.abspath(SPECPATH)

a = Analysis(
    ['src/main.py'],
    pathex=[spec_root],
    binaries=[],
    datas=[
        (os.path.join(spec_root, 'src/ui/themes/dark.qss'), 'src/ui/themes'),
        (os.path.join(spec_root, 'src/ui/themes/light.qss'), 'src/ui/themes'),
        (os.path.join(spec_root, 'src/templates/recipe.html'), 'src/templates'),
        (os.path.join(spec_root, 'icons/probablytasty.png'), 'icons'),
        (os.path.join(spec_root, 'icons/hicolor'), 'icons/hicolor'),
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
