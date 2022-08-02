# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
    ('coupons', 'coupons'),
    ('images', 'images'),
    ('locale', 'locale'),

    ('maps/@01 [Bronze] Minus', 'maps/@01 [Bronze] Minus'),
    ('maps/@02 [Silver] Computer Saloon', 'maps/@02 [Silver] Computer Saloon'),
    ('maps/@03 [Gold] Radiant', 'maps/@03 [Gold] Radiant'),
    ('maps/@04 [Platinum] Bongo Clickbait', 'maps/@04 [Platinum] Bongo Clickbait'),

    ('sounds', 'sounds'),

    ('conversions.py', '.'),

    ('icon.png', '.'),
    ('LICENSE.md', '.'),
    ('noto-sans.otf', '.'),
    ('noto-sans-license.txt', '.'),
    ('options.json', '.'),
    ('roboto.ttf', '.'),
    ('roboto-license.txt', '.'),
    ('splashes.txt', '.'),

    ('Tutorial.md', './docs'),
    ('Vib-Ribbon Minus Guide for Mappers.md', './docs')
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
