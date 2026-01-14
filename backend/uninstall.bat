@echo off
echo AutoCaption Uninstaller
echo ========================
echo.
echo This will delete:
echo   - Virtual environment (venv)
echo   - Downloaded models
echo   - All projects and their data
echo.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" exit /b

echo.
echo Stopping any running instances...
taskkill /f /im python.exe 2>nul

echo Deleting virtual environment...
rmdir /s /q "C:\Users\sauna\Desktop\AutoCaption\backend\venv" 2>nul

echo Deleting models...
rmdir /s /q "C:\Users\sauna\Desktop\AutoCaption\backend\models" 2>nul

echo Deleting projects...
rmdir /s /q "C:\Users\sauna\Desktop\AutoCaption\backend\projects" 2>nul

echo Deleting FFmpeg...
rmdir /s /q "C:\Users\sauna\Desktop\AutoCaption\backend\ffmpeg" 2>nul

echo.
echo Uninstall complete!
echo You can now delete the AutoCaption folder.
pause
