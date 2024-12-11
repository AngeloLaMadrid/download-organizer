# organizar.spec
a = Analysis(
    ['organizar.py'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons')],  # Incluye carpeta de iconos
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='organizar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='logo.ico'  # Cambiar a logo.ico
)