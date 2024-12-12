from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'040904B0',
                [
                    StringStruct(u'CompanyName', u'AngeloLaMadrid'),
                    StringStruct(u'FileDescription', u'Download Organizer - Organiza tus descargas automáticamente'),
                    StringStruct(u'FileVersion', u'1.0.0'),
                    StringStruct(u'InternalName', u'organizar'),
                    StringStruct(u'LegalCopyright', u'Copyright © 2024 AngeloLaMadrid'),
                    StringStruct(u'OriginalFilename', u'organizar.exe'),
                    StringStruct(u'ProductName', u'Download Organizer'),
                    StringStruct(u'ProductVersion', u'1.0.0')
                ]
            )
        ])
    ]
)