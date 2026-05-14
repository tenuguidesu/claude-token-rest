# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=[
        "rumps",
        "watchdog",
        "watchdog.observers",
        "watchdog.events",
        "config",
        "aggregator",
        "watcher",
    ],
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
    [],
    exclude_binaries=True,
    name="ClaudeTokenRest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name="ClaudeTokenRest",
)

app = BUNDLE(
    coll,
    name="ClaudeTokenRest.app",
    icon="assets/icon.icns",
    bundle_identifier="com.claudetokenrest.app",
    info_plist={
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSHumanReadableCopyright": "© 2026",
        "NSAppleEventsUsageDescription": "Accessibility access is not required.",
    },
)
