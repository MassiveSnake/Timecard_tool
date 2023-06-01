# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['Hour_Registry_Run.py'],
    pathex=['C:\\Users\\stamb3257\\PYTHON_Projects\\arc-hours-registry-project\\Hour_Registry_env\\virtual_env\\lib\\site-packages'],
    binaries=[],
    datas=[( 'C:\\Users\\stamb3257\\PYTHON_Projects\\arc-hours-registry-project\\Hour_Registry_env\\Arcadis_logo.ico', '.')],
    hiddenimports=['pandas', 'PyQt5', 'matplotlib', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
a.datas += [('Arcadis_logo.ico' , 'C:\\Users\\stamb3257\\PYTHON_Projects\\arc-hours-registry-project\\Hour_Registry_env\\Arcadis_logo.ico', 'DATA')] 
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Hour_Registry_Run',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon= 'C:\\Users\\stamb3257\\PYTHON_Projects\\arc-hours-registry-project\\Hour_Registry_env\\Arcadis_logo.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Hour_Registry_Run',
)
