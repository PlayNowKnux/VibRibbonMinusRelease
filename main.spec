# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
    ('coupons', 'coupons'),
    ('images', 'images'),
    ('locale', 'locale'),
    ('maps', 'maps'),
    ('sounds', 'sounds'),

    ('icon.png', '.'),
    ('noto-sans.otf', '.'),
    ('noto-sans-license.txt', '.'),
    ('options.json', '.'),
    ('roboto.ttf', '.'),
    ('roboto-license.txt', '.'),
    ('splashes.txt', '.')
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Vib-Ribbon Minus',
    icon='icon.png',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
