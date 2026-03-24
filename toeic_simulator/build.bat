@echo off
setlocal
echo ============================================================
echo  TOEIC Speaking Pro — Build Script
echo  Output: dist\TOEIC_Speaking_Pro.exe  (single file)
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python 3.9+ is on PATH.
    pause & exit /b 1
)

echo.
echo [2/4] Building EXE with PyInstaller (using toeic_pro.spec)...
pyinstaller toeic_pro.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo.
echo [3/4] Preparing runtime distribution folder...
if not exist "dist\images"  mkdir "dist\images"
if not exist "dist\records" mkdir "dist\records"
if not exist "dist\model"   mkdir "dist\model"

:: Copy question bank files if they exist
for %%f in (question_bank.xlsx question_bank.json questions.json) do (
    if exist "%%f" copy /Y "%%f" "dist\" >nul
)

:: Copy images folder if present
if exist "images" (
    xcopy /E /I /Y "images" "dist\images" >nul
)

echo.
echo [4/4] Writing README...
(
echo TOEIC Speaking Pro — 使用说明
echo ================================
echo.
echo 【启动方式】
echo   双击 TOEIC_Speaking_Pro.exe 即可运行，无需安装 Python。
echo.
echo 【首次启动】
echo   - 软件附带 3 天免费试用期，到期后需输入邀请码激活。
echo   - 点击右上角齿轮图标可查看剩余试用时间或输入邀请码。
echo.
echo 【题库更新】
echo   将新的 question_bank.xlsx 放入本目录，重启软件即生效。
echo.
echo 【语音评分】
echo   支持四种评分引擎，点击右上角齿轮 → 语音评分引擎 切换：
echo     · 本地开源 (Whisper+SpeechScore) — 离线，无需账号（集成中）
echo     · 讯飞 ISE         — 需讯飞开放平台账号，联网使用
echo     · 腾讯云智聆       — 需腾讯云账号，联网使用（集成中）
echo     · 驰声 Chivox      — 需驰声账号，联网使用（集成中）
echo   首次点击"语音评分"按钮时，程序会引导填写 API 密钥。
echo.
echo 【语音转文字 (可选)】
echo   1. 前往 https://alphacephei.com/vosk/models
echo   2. 下载英文小模型（vosk-model-small-en-us-0.15，约 40MB）
echo   3. 解压后将文件夹改名为 model，放入本目录
echo   4. 重启软件即可启用转写功能。
echo.
echo 【目录结构】
echo   TOEIC_Speaking_Pro.exe   主程序
echo   question_bank.xlsx       题库（可替换）
echo   images\                  PART2 题目图片
echo   records\                 练习录音（自动生成）
echo   model\                   vosk 语音模型（可选）
echo.
echo 【系统要求】
echo   Windows 10 / 11 (64 位)，无需安装任何运行库。
) > "dist\README.txt"

echo.
echo ============================================================
echo  Build complete!
echo  EXE: dist\TOEIC_Speaking_Pro.exe
echo ============================================================
pause
