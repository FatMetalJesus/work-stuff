@echo off
setlocal

python -m pip install -r requirements.txt
pyinstaller --noconfirm --windowed --name IncidentIQ-Mass-Assigner --paths src src/iiq_desktop/__main__.py

echo Build complete. EXE is in dist\IncidentIQ-Mass-Assigner\IncidentIQ-Mass-Assigner.exe
