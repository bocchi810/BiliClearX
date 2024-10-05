@echo off

python -m venv release-ven

.\release-ven\Scripts\pip install -r requirements.txt
.\release-ven\Scripts\pip install pyinstaller

.\release-ven\Scripts\pyinstaller biliClearX.spec
.\release-ven\Scripts\pyinstaller Review.spec

xcopy .\dist\biliClearX.exe .\ /s /e /y
xcopy .\dist\Review.exe .\ /s /e /y

rmdir /s /q release-ven
rmdir /s /q build
rmdir /s /q dist