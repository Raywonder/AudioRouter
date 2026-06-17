# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

SPEC_DIR = Path.cwd()
ROOT = SPEC_DIR.parents[1]

a = Analysis(
    ["asioa_router_wx.py"],
    pathex=[str(SPEC_DIR), str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "docs"), "docs"),
        (str(ROOT / "README.md"), "."),
        (str(ROOT / "LICENSE.txt"), "."),
        (str(ROOT / "THIRD_PARTY_NOTICES.md"), "."),
        (str(ROOT / "RELEASE_NOTES.md"), "."),
        (str(ROOT / "assets"), "assets"),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="ASIOA Audio Router",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ASIOA Audio Router",
)
