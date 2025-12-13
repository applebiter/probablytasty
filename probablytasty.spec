# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ProbablyTasty
Builds standalone executable for Windows and Linux
"""

from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

# Collect data files using Tree for directory recursion
# Use os.path.join for cross-platform compatibility
themes_tree = Tree(os.path.join('src', 'ui', 'themes'), prefix=os.path.join('src', 'ui', 'themes'), excludes=['*.pyc', '__pycache__'])
icons_tree = Tree('icons', prefix='icons', excludes=['*.pyc', '__pycache__'])

# Collect data files for packages that need them
mf2py_datas = collect_data_files('mf2py')
extruct_datas = collect_data_files('extruct')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=mf2py_datas + extruct_datas,
    hiddenimports=[
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'src.models',
        'src.models.database',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    themes_tree,
    icons_tree,
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
    a.datas,
    themes_tree,
    icons_tree,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ProbablyTasty',
)
