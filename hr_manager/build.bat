@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查 Python 环境
    pause
    exit /b 1
)

echo [2/3] 生成图标...
if exist gen_icon.py (
    python gen_icon.py
)

echo [3/3] 打包 EXE...
pyinstaller hr_manager.spec --clean --noconfirm --distpath Release
if %errorlevel% neq 0 (
    echo 打包失败，请查看错误信息
    pause
    exit /b 1
)

echo.
echo ===================================
echo  构建完成！
echo  EXE 路径: Release\HR_Manager.exe
echo ===================================
pause
