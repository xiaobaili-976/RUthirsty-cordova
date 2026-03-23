@echo off
setlocal
echo ============================================================
echo  TOEIC Speaking Test Simulator v2 — Build Script
echo ============================================================
echo.

echo [1/4] Installing Python dependencies...
pip install --upgrade PyQt6 pyttsx3 pyaudio vosk pyinstaller
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python 3.9+ is on PATH.
    pause & exit /b 1
)

echo.
echo [2/4] Building EXE with PyInstaller...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "TOEIC_Speaking_Simulator" ^
    --hidden-import "pyttsx3.drivers" ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pyttsx3.drivers.nsss" ^
    --hidden-import "pyttsx3.drivers.espeak" ^
    --hidden-import "vosk" ^
    --collect-all PyQt6 ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo.
echo [3/4] Preparing runtime distribution folder...
if not exist "dist\images\set1" mkdir "dist\images\set1"
if not exist "dist\images\set2" mkdir "dist\images\set2"
if not exist "dist\records"     mkdir "dist\records"
if not exist "dist\model"       mkdir "dist\model"
copy /Y "question_bank.json" "dist\" >nul 2>&1

echo.
echo [4/4] Writing usage notes...
(
echo TOEIC Speaking Test Simulator v2 — 使用说明
echo ==============================================
echo.
echo 【基本使用】
echo 1. 编辑 question_bank.json，按格式填入各套题目与参考答案。
echo 2. 将 PART 2 图片分别放入 images\set1\, images\set2\ 等子文件夹，
echo    路径须与 question_bank.json 中一致（如 images/set1/q3.jpg）。
echo 3. 双击 TOEIC_Speaking_Simulator.exe 启动程序。
echo 4. 在套题选择界面选择套题，点击"确认选择"开始考试。
echo 5. 考试全程可点击"跳过"按钮跳过当前倒计时，
echo    点击标题栏"?"按钮查看当前题目参考答案。
echo.
echo 【录音与语音转文字】
echo - 程序检测到麦克风后，作答阶段自动开始录音（标题栏显示 ● REC）。
echo - 录音文件保存至 records\set_{编号}\ 文件夹。
echo - 如需启用语音转文字功能：
echo     a. 前往 https://alphacephei.com/vosk/models
echo     b. 下载英文小模型（推荐 vosk-model-small-en-us-0.15，约 40MB）
echo     c. 解压后将模型文件夹改名为 model，放在本程序目录下
echo     d. 重新运行程序，转写文本将与录音文件一同保存。
echo.
echo 【系统要求】
echo - Windows 10 / 11（64位），无需安装 Python
echo - 麦克风（可选，不连接时考试流程正常运行）
) > "dist\README.txt"

echo.
echo ============================================================
echo  Build complete!
echo  EXE: dist\TOEIC_Speaking_Simulator.exe
echo.
echo  目录结构说明:
echo    dist\TOEIC_Speaking_Simulator.exe  主程序
echo    dist\question_bank.json            题目配置（可编辑）
echo    dist\images\set1\                  套题1的 PART2 图片
echo    dist\images\set2\                  套题2的 PART2 图片
echo    dist\model\                        vosk 语音模型（下载后放此处）
echo    dist\records\                      练习录音（自动生成）
echo ============================================================
pause

