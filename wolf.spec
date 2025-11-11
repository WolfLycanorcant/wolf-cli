# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get the root directory of the project
root_dir = Path(os.getcwd())

a = Analysis(
    ['wolf_launcher.py'],
    pathex=[str(root_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'wolf',
        'wolf.cli_wrapper',
        'wolf.config_manager',
        'wolf.permission_manager',
        'wolf.tool_registry',
        'wolf.tool_executor',
        'wolf.orchestrator',
        'wolf.llm',
        'wolf.llm.ollama',
        'wolf.providers',
        'wolf.providers.file_ops',
        'wolf.providers.ps_client',
        'wolf.providers.shell_client',
        'wolf.providers.web_search',
        'wolf.utils',
        'wolf.utils.logging_utils',
        'wolf.utils.paths',
        'wolf.utils.platform_utils',
        'wolf.utils.screenshot',
        'wolf.utils.validation',
        'wolf.memory',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='wolf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
