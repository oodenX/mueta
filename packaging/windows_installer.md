# Windows Installer (WiX Toolset)

## Prerequisites
- Install WiX Toolset: https://wixtoolset.org/
- Build mueta.exe using PyInstaller first

## Build Steps

1. Create Product.wxs:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="Mueta" Language="1033" Version="0.1.0"
           Manufacturer="oodenX" UpgradeCode="PUT-GUID-HERE">
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />

    <MajorUpgrade DowngradeErrorMessage="A newer version of Mueta is already installed." />
    <MediaTemplate EmbedCab="yes" />

    <Feature Id="ProductFeature" Title="Mueta" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
  </Product>

  <Fragment>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="Mueta" />
      </Directory>
    </Directory>
  </Fragment>

  <Fragment>
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="ProductComponent">
        <File Id="mueta.exe" Source="dist\mueta.exe" KeyPath="yes" />
        <Environment Id="PATH" Name="PATH" Value="[INSTALLFOLDER]"
                     Permanent="no" Part="last" Action="set" System="yes" />
      </Component>
    </ComponentGroup>
  </Fragment>
</Wix>
```

2. Build MSI:
```bash
candle Product.wxs
light -out mueta-0.1.0.msi Product.wixobj
```

## Alternative: Use cx_Freeze (Simpler)

```bash
pip install cx_Freeze
python setup_freeze.py bdist_msi
```

Where setup_freeze.py:
```python
from cx_Freeze import setup, Executable

setup(
    name="Mueta",
    version="0.1.0",
    description="Music metadata fetcher",
    executables=[Executable("src/mueta/main.py", target_name="mueta.exe")],
    options={
        "build_exe": {
            "packages": ["mueta"],
            "include_files": []
        }
    }
)
```
