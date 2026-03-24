# TOEIC Speaking Pro — 软件详细设计文档

**版本：** v1.1
**更新日期：** 2026-03-24
**文档状态：** 正式版

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [模块详细设计](#3-模块详细设计)
4. [功能详细清单](#4-功能详细清单)
5. [语音评分引擎](#5-语音评分引擎)
6. [开发者模式与授权](#6-开发者模式与授权)
7. [数据流与状态机](#7-数据流与状态机)
8. [UI 设计规范](#8-ui-设计规范)
9. [数据格式与配置文件](#9-数据格式与配置文件)
10. [打包与发布](#10-打包与发布)
11. [注意事项与已知限制](#11-注意事项与已知限制)
12. [开发与维护指南](#12-开发与维护指南)

---

## 1. 项目概述

### 1.1 软件定位

TOEIC Speaking Pro 是一款面向 Windows 桌面端的 **TOEIC 口语考试模拟器**，完整还原 TOEIC Speaking Test 的 Part 1–5 全流程，包含计时、录音、参考答案、TTS 语音指令、多引擎语音评分和背诵复习等功能。软件定位为轻量化、离线可用的个人备考工具，提供从练习到评分的完整闭环。

### 1.2 技术栈

| 层次 | 技术 |
|------|------|
| GUI 框架 | PyQt6 6.4+ |
| 语音合成 (TTS) | pyttsx3（Windows SAPI5） |
| 录音 | pyaudio（PCM 16-bit, 16kHz Mono） |
| 语音识别 (STT) | vosk（离线，英语模型） |
| 题库读取 | openpyxl（Excel）/ json / csv |
| 语音评分 | 讯飞 ISE / 腾讯云智聆 / 驰声 Chivox / 本地 Whisper（可切换） |
| 图标生成 | Pillow (PIL) |
| 打包发布 | PyInstaller + GitHub Actions |
| 运行平台 | Windows 10/11 64-bit（主）；macOS/Linux 部分兼容 |

### 1.3 版本历史

| 版本 | 核心变更 |
|------|---------|
| v1（基础版）| 完整 TOEIC Speaking 考试流程 + 录音 |
| v2 | 定时器优化、跳过功能解锁 |
| v3 | 多套题支持、Excel 题库、讯飞语音评分 [PRO] |
| v3 Pro | 背诵复习模式、标记系统、试用/激活机制 [PRO] |
| v1.0 | 5 项优化：录音回放、麦克风试音、专项训练、成绩报告、图标 |
| **v1.1（当前）** | **四引擎语音评分切换、开发者模式保留设置菜单** |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          main.py  (入口)                              │
│  初始化所有组件，完成依赖注入，启动 QApplication event loop            │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 依赖注入
         ┌───────────────┼──────────────────────────┐
         ▼               ▼                          ▼
  ┌─────────────┐  ┌───────────┐            ┌──────────────┐
  │  ExamEngine │  │ Recorder  │            │LicenseManager│
  │  (状态机)   │  │ Manager   │            │(试用/激活)   │
  └──────┬──────┘  └─────┬─────┘            └──────────────┘
         │ signals        │ signals
         ▼               ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │                     MainWindow (window.py)                          │
  │  Page 0: 套题选择  Page 1: 考试  Page 2: 结束  Page 3: 专项训练    │
  └──────────────────────┬─────────────────────────────────────────────┘
         │               │                │
         ▼               ▼                ▼
  ┌─────────────┐  ┌──────────────────────────────────────────┐
  │ TTSManager  │  │         语音评分引擎（可热切换）            │
  │ (pyttsx3)   │  │  ┌─────────────┐  ┌──────────────────┐  │
  └─────────────┘  │  │ VoiceScorer │  │ TencentScorer    │  │
                   │  │ (讯飞 ISE)  │  │ (腾讯云智聆)     │  │
  ┌─────────────┐  │  └─────────────┘  └──────────────────┘  │
  │ MarksManager│  │  ┌─────────────┐  ┌──────────────────┐  │
  │ (marks.json)│  │  │ ChivoxScorer│  │ LocalScorer      │  │
  └─────────────┘  │  │ (驰声)      │  │(本地开源离线)    │  │
  ┌─────────────┐  │  └─────────────┘  └──────────────────┘  │
  │ReviewEngine │  └──────────────────────────────────────────┘
  │(复习问题集) │            │
  └─────────────┘   ┌───────┴────────┐
  ┌─────────────┐   │ScoringEngine   │
  │ _WAVPlayer  │   │Config          │
  │ (录音回放)  │   │(持久化引擎选择)│
  └─────────────┘   └────────────────┘
```

### 2.2 设计原则

1. **考试流程边界锁定**：ExamEngine 的计时器、TTS、录音触发逻辑永不修改，所有新功能均以"叠加"方式实现。
2. **信号/槽解耦**：模块间通过 Qt signals 通信，避免直接方法调用跨层依赖。
3. **线程安全**：录音、STT、TTS、语音评分均在独立线程运行，UI 回调通过 `QTimer.singleShot(0, ...)` 调度回主线程。
4. **懒加载**：TTSManager（UI 朗读）、语音评分引擎仅在首次使用时创建。
5. **优雅降级**：无麦克风 / 无 vosk 模型 / 无 API 密钥，均静默降级而非崩溃。
6. **评分引擎统一接口**：所有评分引擎实现相同接口，窗口层无需感知具体引擎类型。

---

## 3. 模块详细设计

### 3.1 `main.py` — 应用入口

**职责：** 初始化所有组件，完成依赖注入，启动主窗口。

**初始化顺序：**

```
BASE_DIR 检测（冻结 EXE / 开发目录）
  → QApplication + 高 DPI 策略 + 全局 Tooltip 样式
  → ExamEngine(BASE_DIR)
  → RecorderManager(BASE_DIR)
  → LicenseManager(BASE_DIR)
  → MarksManager(BASE_DIR)      [PRO]
  → ReviewEngine(engine)         [PRO]
  → MainWindow(engine, recorder, license_mgr, marks_mgr, rev_engine)
  → app_icon.ico 加载（app.setWindowIcon）
  → win.show() → app.exec()
```

> `BASE_DIR` 冻结模式下为 `sys.executable` 所在目录，确保 EXE 与数据文件同级。高 DPI 使用 `PassThrough` 策略，避免 4K 屏文字模糊。

---

### 3.2 `engine.py` — 考试引擎（核心状态机）

#### 3.2.1 步骤类型定义

| 步骤类型 | 触发动作 | 推进条件 |
|---------|---------|---------|
| `screen` | 发送 `update_display` 信号 | 50ms 延迟后自动推进 |
| `tts` | 调用 TTSManager.speak() | TTS `finished` 信号 |
| `timer` | 启动 QTimer 倒计时 | 倒计时归零 |
| `set_answer` | 发送 `answer_updated` 信号 | 立即推进（0ms） |
| `record_start` | 发送 `rec_start` 信号 | 立即推进（0ms） |
| `record_stop` | 发送 `rec_stop` 信号 | 立即推进（0ms） |
| `end` | 发送 `exam_finished` 信号 | 流程终止 |

#### 3.2.2 公开 API

```python
engine.sets                               # → list[dict]  [{id, name}, ...]
engine.load_set(set_id: int)              # 选择套题
engine.start_exam()                       # 启动完整模考
engine.start_part_exam(set_id, part_num)  # 启动单 PART 专项训练
engine.skip()                             # 跳过当前计时/TTS
engine.abort()                            # 中止考试（返回首页）
engine.pause_timer()                      # 暂停倒计时（语音评分用）
engine.resume_timer()                     # 恢复倒计时
```

#### 3.2.3 考试完整步骤序列

```
[Part 1 介绍屏 + TTS]
  Q1: 题目屏 → TTS准备提示 → 45s准备 → TTS开始提示 → 录音45s → 停止
  Q2: 同上
[Part 2 介绍屏 + TTS]
  Q3: 图片屏 → TTS准备提示 → 45s准备 → TTS开始提示 → 录音30s → 停止
  Q4: 同上
[Part 3 介绍屏 + TTS]
  背景屏 + TTS读背景
  Q5: 背景+问题屏 → TTS问题 → 3s准备 → TTS开始 → 录音15s → 停止
  Q6: 同上 (15s)
  Q7: 同上 (30s)
[Part 4 介绍屏 + TTS]
  信息屏 + 45s准备
  Q8:  set_answer → TTS问题 → 3s → TTS开始 → 录音15s → 停止
  Q9:  同上 (15s)
  Q10: set_answer → TTS问题(2次) → 3s → TTS开始 → 录音30s → 停止
[Part 5 介绍屏 + TTS]
  Q11: 题目屏 → TTS题目 → 45s准备 → TTS开始 → 录音60s → 停止
[END]
```

---

### 3.3 `window.py` — 主窗口 UI

#### 3.3.1 页面结构（QStackedWidget）

| 页面索引 | 名称 | 说明 |
|---------|------|------|
| 0 | 套题选择页 | 套题列表 + 模式入口按钮 |
| 1 | 考试页 | 题目内容 + 计时栏 + 操作按钮 |
| 2 | 结束报告页 | 考试成绩报告 + 跳转按钮 |
| 3 | 专项训练页 | 5 种复习子模式独立界面 |

#### 3.3.2 头部栏（Header）结构

```
[TOEIC® Speaking Pro]  ......  [● REC]  [🏠]  [📖]  [⚙]
```

| 元素 | 试用模式 | 开发者模式 | 永久激活 |
|------|---------|-----------|---------|
| ● REC 红点 | 录音时显示 | 录音时显示 | 录音时显示 |
| 🏠 Home | 考试/复习时显示 | 考试/复习时显示 | 考试/复习时显示 |
| 📖 Answer | 考试/复习时显示 | 考试/复习时显示 | 考试/复习时显示 |
| ⚙ 设置齿轮 | **显示**（完整菜单）| **显示**（精简菜单）| 隐藏 |

> **v1.1 变更**：开发者模式下齿轮按钮**不再隐藏**，改为显示精简菜单（仅含引擎选择和退出）。

#### 3.3.3 设置齿轮菜单内容

**试用模式下（未激活）：**
```
试用期剩余 HH:MM:SS   ← 仅展示，不可点击
─────────────────────
输入邀请码            ← 打开激活对话框
─────────────────────
语音评分引擎   ▶     ← 子菜单：四引擎单选
─────────────────────
退出程序
```

**开发者模式下：**
```
语音评分引擎   ▶     ← 子菜单：四引擎单选
─────────────────────
退出程序
```
> 试用时间和邀请码在开发者模式下不显示，但引擎选择始终可用。

---

### 3.4 `recorder.py` — 录音与 STT

**录音格式：** PCM 16-bit，16000 Hz，单声道，chunk=1024 帧

**线程模型：**
```
主线程: start_recording() → 设置 _current_wav，启动录音线程
录音线程: 写入 PCM 帧，_recording=False 时退出
  └─ 保存 WAV 文件
     └─ （若有 vosk 模型）启动 STT 线程
STT 线程: 识别 → 保存 .txt → emit transcription_ready(wav_path, text)
```

**录音文件命名规则：**

| 题号 | hint 前缀 | 完整路径示例 |
|------|----------|------------|
| Q1, Q2 | `p1_q1`, `p1_q2` | `records/set_1/p1_q1_20260324_093012.wav` |
| Q3, Q4 | `p2_q3`, `p2_q4` | `records/set_1/p2_q3_20260324_093500.wav` |
| Q5–Q7 | `p3_q5`, `p3_q6`, `p3_q7` | — |
| Q8–Q10 | `p4_q8`, `p4_q9`, `p4_q10` | — |
| Q11 | `p5_q11` | — |

---

### 3.5 `tts_manager.py` — 文字转语音

**关键参数：** 语速 145 wpm，优先语音 Zira（女）> David（男）> Hazel

**重要约束：** `interrupt()` 调用后**不**发出 `finished` 信号，ExamEngine 通过 `_tts_skipped` 标志忽略后续信号。

---

### 3.6 `voice_scorer.py` — 讯飞 ISE 评分器

**API：** 讯飞 ISE（智能口语评测）WebSocket
**端点：** `wss://ise-api.xfyun.cn/v2/open-ise`
**超时：** 5 秒（→ `error="__TIMEOUT__"`）

**评分指标：**

| 字段 | 含义 | 范围 |
|------|------|------|
| `pronunciation` | 发音准确度 | 0–100 |
| `fluency` | 流利度 | 0–100 |
| `completeness` | 内容完整性 | 0–100 |
| `overall` | 综合得分 | 0–100 |

---

### 3.7 `scoring_engine_config.py` — 评分引擎选择配置

**职责：** 持久化用户选择的评分引擎，跨会话记忆。

**存储文件：** `scoring_engine.json`（EXE 同目录）

```json
{ "engine": "xunfei" }
```

**支持的引擎键值：**

| 键值 | 显示名称 | 需要网络 | 需要 API 密钥 |
|------|---------|---------|-------------|
| `local` | 本地开源 (Whisper+SpeechScore) | 否 | 否 |
| `xunfei` | 讯飞 ISE | 是 | 是 |
| `tencent` | 腾讯云智聆 | 是 | 是 |
| `chivox` | 驰声 Chivox | 是 | 是 |

> 默认引擎：`xunfei`（与旧版兼容）

---

### 3.8 `alt_scorers.py` — 替代评分引擎

包含三个评分器类，均实现与 `VoiceScorer` 相同的公开接口：

```python
class TencentScorer:   # 腾讯云智聆，配置存 tencent_config.json
class ChivoxScorer:    # 驰声 Chivox，配置存 chivox_config.json
class LocalScorer:     # 本地离线，无需密钥，has_credentials() 恒返回 True
```

**统一接口（所有评分器均实现）：**

```python
scorer.has_credentials() -> bool         # 是否已配置可用凭证
scorer.save_config(app_id, api_key, api_secret)  # 保存 API 密钥
scorer._load_config()                    # 从文件重新加载密钥
scorer.score_async(wav_path, answer_text, callback)  # 异步评分
scorer.app_id / scorer.api_key / scorer.api_secret   # 字符串属性
```

---

### 3.9 `license_manager.py` — 授权管理

详见第 [6 节](#6-开发者模式与授权)。

---

## 4. 功能详细清单

### 4.1 核心考试功能

#### F-01 完整 TOEIC Speaking 模考

| 属性 | 说明 |
|------|------|
| 覆盖部分 | Part 1–5，共 11 题 |
| 计时规则 | 严格遵循 TOEIC 官方规格 |
| TTS 指令 | 所有英文指令语音播报（pyttsx3） |
| 录音 | 每题作答阶段自动开始/结束录音 |
| 参考答案 | 每题均有参考答案，可随时查看 |
| 跳过功能 | 计时阶段和 TTS 阶段均可跳过 |

#### F-02 单 PART 专项训练

| PART | 题目数 | 准备时间 | 作答时间 |
|------|--------|---------|---------|
| Part 1 朗读文章 | 2 | 45s × 2 | 45s × 2 |
| Part 2 描述图片 | 2 | 45s × 2 | 30s × 2 |
| Part 3 回答问题 | 3 | 3s × 3 | 15s+15s+30s |
| Part 4 信息问答 | 3 | 45s（共） | 15s+15s+30s |
| Part 5 发表意见 | 1 | 45s | 60s |

---

### 4.2 录音与回放

#### F-03 考试录音

- 由 ExamEngine `record_start` / `record_stop` 信号自动触发
- Header 红色 ● REC 图标指示录音状态

#### F-04 作答音频一键回放

| 入口 | 说明 |
|------|------|
| 考试中 | 计时栏"回放录音"按钮（录音完成后启用）|
| 考试后 | 结束报告页"回放最近录音"按钮 |

- 播放期间：倒计时**显示冻结**，引擎计时**继续运行**
- 弹出倒计时对话框，支持提前终止

#### F-05 麦克风试音检测

| 流程 | 说明 |
|------|------|
| 点击首页话筒图标 | 打开试音对话框 |
| 录制 3 秒 | QTimer 独立倒计时（零考试影响）|
| 自动回放 | 600ms 等待文件写入后播放 |
| 结果反馈 | 成功绿 / 失败红 / 试音蓝 / 常态灰 四态图标 |

---

### 4.3 参考答案与 TTS

#### F-06 参考答案查看

- Header 书籍图标打开，宽度 800px，Calibri 14pt，1.5 行距
- 内置"朗读答案" / "停止朗读"，对话框关闭时自动停止 TTS

---

### 4.4 专项训练（背诵复习）模式

#### F-07 五种复习子模式

| 子模式 | 来源 | 顺序 | 答案默认 |
|--------|------|------|---------|
| 随机练习 | 全部题目 | 随机打乱 | 隐藏 |
| 答案速背 | 全部题目 | 题库顺序 | 自动展示 |
| 高频题专练 | ★ 标记题 | 随机打乱 | 隐藏 |
| 薄弱题巩固 | ● 标记题 | 随机打乱 | 隐藏 |
| 单项集训 | 全部题目 | 选择 PART | 标准计时 |

#### F-08 题目标记

| 标记 | 按钮激活色 | 存储键 |
|------|----------|-------|
| ● 薄弱题 | 红色 #FF6B6B | `weak` |
| ★ 高频题 | 橙色 #F5A623 | `high_freq` |

---

### 4.5 考试成绩报告

| 项目 | 内容 |
|------|------|
| 训练模式 | 完整模考 / 专项训练 + 套题名 |
| 考试用时 | X 分 X 秒（精确到秒）|
| 各 PART 状态 | ✓ 全部完成 / ⚠ 部分完成 / ✗ 未录音 |
| 薄弱项建议 | 未完成录音的 PART 名称列表 |

---

## 5. 语音评分引擎

### 5.1 引擎概览

v1.1 支持四种语音评分引擎，用户可在**右上角设置菜单**中随时切换，**无需重启**，选择立即生效并本地持久化。

| 引擎 | 键值 | 类型 | 网络要求 | API 账号 | 当前状态 |
|------|------|------|---------|---------|---------|
| 本地开源 (Whisper+SpeechScore) | `local` | 离线 | 否 | 否 | 框架已就绪，评分集成中 |
| 讯飞 ISE | `xunfei` | 云端 | 是 | 讯飞开放平台 | **完整可用** |
| 腾讯云智聆 | `tencent` | 云端 | 是 | 腾讯云 | 框架已就绪，API 集成中 |
| 驰声 Chivox | `chivox` | 云端 | 是 | 驰声官方 | 框架已就绪，API 集成中 |

---

### 5.2 引擎切换操作

#### 步骤 1：点击右上角齿轮图标（⚙）

- **试用模式**下：菜单包含试用时间、邀请码、语音评分引擎、退出
- **开发者模式**下：菜单仅含语音评分引擎、退出

#### 步骤 2：将鼠标悬停在"语音评分引擎 ▶"上

弹出子菜单，当前选中的引擎前显示 ✓ 勾选标记：

```
✓ 本地开源 (Whisper+SpeechScore)
  讯飞 ISE
  腾讯云智聆
  驰声 Chivox
```

#### 步骤 3：点击目标引擎即完成切换

- 选择保存到 `scoring_engine.json`
- 下次打开软件自动恢复为上次选择
- 无需重启，下次点击"语音评分"按钮即使用新引擎

---

### 5.3 讯飞 ISE 使用指南（完整可用）

#### 5.3.1 账号申请

1. 访问 [讯飞开放平台](https://www.xfyun.cn/)，注册账号
2. 进入控制台 → 创建应用
3. 在应用中开通 **ISE（智能口语评测）**服务
4. 获取三个凭证：**App ID**、**API Key**、**API Secret**

#### 5.3.2 首次配置

首次点击"语音评分"按钮时，软件自动弹出密钥配置对话框：

```
┌──────────────────────────────────────────┐
│        讯飞 ISE 密钥配置                  │
│                                          │
│  请输入讯飞开放平台的 ISE 服务密钥。      │
│  语音评分功能需要联网，其余功能不受影响。  │
│                                          │
│  App ID:      [________________]         │
│  API Key:     [________________]         │
│  API Secret:  [●●●●●●●●●●●●●●●●]        │
│                                          │
│               [保存]  [取消]             │
└──────────────────────────────────────────┘
```

填写完整三项后点击"保存"，凭证写入 `xunfei_config.json`。

#### 5.3.3 使用流程

1. 完成录音后，"语音评分"按钮变为**可用状态**
2. 点击"语音评分"→ 按钮显示"评分中…"，计时器**自动暂停**
3. 约 2–5 秒后弹出评分结果：

```
┌──────────────────────────────────────────┐
│       语音评分结果 / Score Report         │
│                                          │
│  发音准确度  Pronunciation       87.5    │
│  流利度      Fluency              82.0   │
│  内容完整性  Completeness         90.0   │
│  综合得分    Overall              86.5   │
│                                          │
│                              [关闭]      │
└──────────────────────────────────────────┘
```

4. 关闭对话框后，计时器**自动恢复**

#### 5.3.4 超时处理

若网络慢或服务繁忙（5 秒内无响应）：

```
评分超时，是否重试？
[重试]  [关闭]
```

- 选"重试"：再次发起评分请求（计时器保持暂停）
- 选"关闭"：取消评分，计时器恢复

#### 5.3.5 密钥存储位置

```
TOEIC_Speaking_Pro.exe 同目录/
└── xunfei_config.json    ← App ID / API Key / API Secret（明文 JSON）
```

> ⚠️ **安全提示：** 密钥以明文存储，请勿将此文件上传至公开代码仓库或共享给他人。

#### 5.3.6 环境变量方式（优先级更高）

也可通过环境变量配置，优先级高于配置文件：

```bash
set XUNFEI_APP_ID=12345678
set XUNFEI_API_KEY=abc123...
set XUNFEI_API_SECRET=xyz789...
```

---

### 5.4 腾讯云智聆使用指南（框架就绪）

#### 5.4.1 账号申请

1. 访问 [腾讯云控制台](https://console.cloud.tencent.com/)，注册账号
2. 开通**智聆口语评测（SOE）**服务
3. 在 API 密钥管理中获取：**SecretId（App ID）**、**SecretKey（API Key）**

#### 5.4.2 首次配置

切换到腾讯云智聆引擎后，首次点击"语音评分"弹出配置对话框：

```
┌──────────────────────────────────────────┐
│        腾讯云智聆 密钥配置                │
│                                          │
│  请输入腾讯云智聆口语评测服务密钥。       │
│  语音评分功能需要联网，其余功能不受影响。  │
│                                          │
│  App ID:      [SecretId__________]       │
│  API Key:     [SecretKey_________]       │
│  API Secret:  [●●●●●●●●●●●●●●●●]        │
│                                          │
│               [保存]  [取消]             │
└──────────────────────────────────────────┘
```

凭证写入 `tencent_config.json`。

> 📌 当前版本腾讯云评分 API 集成尚在开发中，配置保存后评分操作将显示"该评分引擎尚未完整接入，敬请期待后续版本"提示。

---

### 5.5 驰声 Chivox 使用指南（框架就绪）

#### 5.5.1 账号申请

1. 访问 [驰声官网](https://www.chivox.com/)，联系商务或申请试用账号
2. 获取三个凭证：**App ID**、**API Key**、**API Secret**

#### 5.5.2 首次配置

切换到驰声引擎后，首次点击"语音评分"弹出配置对话框：

```
┌──────────────────────────────────────────┐
│        驰声 Chivox 密钥配置              │
│                                          │
│  请输入驰声 Chivox 语音评测服务密钥。    │
│  语音评分功能需要联网，其余功能不受影响。  │
│                                          │
│  App ID:      [________________]         │
│  API Key:     [________________]         │
│  API Secret:  [●●●●●●●●●●●●●●●●]        │
│                                          │
│               [保存]  [取消]             │
└──────────────────────────────────────────┘
```

凭证写入 `chivox_config.json`。

> 📌 当前版本驰声评分 API 集成尚在开发中，提示同上。

---

### 5.6 本地开源引擎使用指南（框架就绪）

#### 5.6.1 特点

- 完全**离线运行**，无需任何 API 账号
- 使用 **Whisper**（语音识别）+ **SpeechScore**（评分算法）
- 无网络评分延迟，保护录音隐私

#### 5.6.2 使用方式

切换到"本地开源"引擎后，点击"语音评分"**无需任何配置**，直接进行评分。

> 📌 当前版本本地评分引擎尚在集成中，点击后将提示"本地开源评分引擎（Whisper+SpeechScore）尚未集成，敬请期待后续版本"。

---

### 5.7 计时器与评分的联动规则（铁律）

无论使用哪种评分引擎，以下规则始终生效：

| 事件 | 计时器行为 |
|------|----------|
| 打开密钥配置对话框 | **立即暂停** `pause_timer()` |
| 关闭密钥配置对话框（任何方式）| **立即恢复** `resume_timer()` |
| 评分请求发出 | 保持暂停 |
| 评分结果对话框弹出 | 保持暂停 |
| 关闭评分结果对话框 | **立即恢复** `resume_timer()` |
| 评分超时 → 关闭 | **立即恢复** `resume_timer()` |
| 评分超时 → 重试 | 保持暂停（继续等待）|

> `pause_timer()` / `resume_timer()` 在 TTS 阶段调用为 no-op（不影响 TTS 推进）。

---

### 5.8 七种评分场景处理

| 场景 | 触发条件 | 处理逻辑 |
|------|---------|---------|
| 1 | 无录音文件 | 暂停计时 → 提示"无有效录音" → 恢复计时 |
| 2 | 未配置密钥（仅 API 引擎）| 暂停计时 → 弹出密钥配置对话框 |
| 3 | 配置无效（空字段）| 警告"请填写完整密钥" → 关闭配置对话框 → 恢复计时 |
| 4 | 网络错误 | 提示"请检查网络连接" → 恢复计时 |
| 5 | 5s 超时 | 询问"重试/关闭"；重试保持暂停，关闭恢复计时 |
| 6 | API 其他失败 | 通用"评分失败，请重试"提示 → 恢复计时 |
| 7 | 评分成功 | 弹出 4 项得分对话框 → 关闭后恢复计时 |

---

## 6. 开发者模式与授权

### 6.1 授权状态一览

| 状态 | 判定条件 | 设置菜单 | 功能权限 |
|------|---------|---------|---------|
| 试用期中 | `trial_remaining > 0` | 完整菜单（时间+邀请码+引擎+退出）| 全功能 |
| 试用到期 | `trial_remaining ≤ 0` | 完整菜单（时间显示"已到期"）| 启动时阻塞激活对话框 |
| **开发者模式** | 密码验证 或 文件检测 | **精简菜单（引擎+退出）** | 全功能，无时间限制 |
| 永久激活 | 邀请码验证 + license 文件 | 齿轮**隐藏**（无需设置）| 全功能，无时间限制 |

---

### 6.2 开发者模式进入方式

#### 方式一：键盘快捷键（运行时动态解锁）

1. 软件运行中，在**主窗口任意页面**按下快捷键：

   ```
   Ctrl + Shift + T
   ```

2. 弹出密码输入对话框：

   ```
   ┌────────────────────────────────┐
   │         开发者模式             │
   │  请输入开发口令：              │
   │  [●●●●●●●●●●●●●●]            │
   │         [OK]  [Cancel]        │
   └────────────────────────────────┘
   ```

3. 输入口令（区分大小写）：

   ```
   TOEIC_DEV_2024
   ```

4. 输入正确后弹出确认提示"开发者模式已启用"，设置菜单立即切换为精简模式。

> ⚠️ 若软件已处于开发者模式，再次按快捷键会提示"已处于开发者模式"。

#### 方式二：文件触发（启动时自动检测）

1. 在 `TOEIC_Speaking_Pro.exe` **同目录**下创建文件：

   ```
   dev_mode.txt
   ```

   文件内容任意（空文件即可）。

2. 重启软件，启动时自动检测到该文件并进入开发者模式，**无需输入密码**。

> **常用命令（Windows）：**
> ```cmd
> echo. > dev_mode.txt
> ```
> **Linux/macOS 开发环境：**
> ```bash
> touch toeic_simulator/dev_mode.txt
> ```

#### 开发者模式行为变化

| 功能 | 非开发者模式 | 开发者模式 |
|------|-----------|-----------|
| 试用倒计时 | 每秒刷新 | 停止计时器，不显示 |
| 设置菜单 | 时间+邀请码+引擎+退出 | **仅引擎+退出** |
| 功能限制 | 无（试用期内）| 无 |
| 启动阻塞 | 到期后出现 | **不出现** |

---

### 6.3 试用期机制

```
首次启动
  → 写入 toeic_trial.dat（首启 Unix 时间戳，XOR+Base64 混淆）
每次启动
  → 读取 trial.dat，比对当前时间
  → 试用剩余 = 72 小时 − (当前时间 − 首启时间)
试用有效（>0）→ 正常使用，设置菜单显示剩余时间
试用到期（≤0）→ 启动后 150ms 弹出阻塞激活对话框（不可关闭）
```

**试用倒计时展示：** 设置菜单内（`HH:MM:SS` 格式，每次打开菜单实时刷新）。

---

### 6.4 永久激活（邀请码）

#### 邀请码格式

```
BASE-XXXXXX000
      └─6位─┘└3位┘
```

- `XXXXXX`：本机机器码（MD5(CPU序列号+磁盘序列号)，大写十六进制）后 **6 位**
- `000`：3 位数字校验位

#### 获取机器码

在 EXE 同目录放置 `dev_mode.txt` 进入开发者模式后，机器码可在源代码 `license_manager.py` 的 `_get_machine_code()` 函数处调试获取。

#### 激活流程

1. 点击设置菜单 → "输入邀请码"
2. 填入格式为 `BASE-XXXXXX000` 的邀请码
3. 激活成功 → 写入 `toeic_license.dat`，齿轮图标隐藏
4. 激活失败 → 提示"格式错误"或"机器码不匹配"

**激活文件：** `toeic_license.dat`（`code=…|machine=…|ts=…`，XOR+Base64 混淆）

> ⚠️ 邀请码与机器码绑定，一机一码，换机需重新生成。

---

## 7. 数据流与状态机

### 7.1 考试启动流程

```
用户选择套题 → _on_confirm_set()
  → engine.load_set(set_id)
  → 初始化跟踪变量 (start_time, part_recordings)
  → 切换到 Page 1
  → engine.start_exam()
     → _build_steps() 生成步骤列表
     → _run() → 执行第一个步骤
```

### 7.2 语音评分状态机

```
点击"语音评分" → _on_voice_score(wav_path, answer_text):
  获取当前活跃引擎  ← _get_active_scorer()
  重新加载配置      ← scorer._load_config()
  │
  ├─ 无录音文件  → pause → QMessageBox → resume → 返回
  │
  ├─ 无密钥（API引擎）→ pause → _show_scorer_credentials_dialog()
  │                          ├─ 保存成功 → 继续评分（仍暂停）
  │                          └─ 取消     → resume → 返回
  │
  └─ 有密钥（或 LocalScorer）→ pause
       ↓
  _do_voice_score():
    btn → "评分中…"（禁用）
    scorer.score_async() → 后台线程
    ↓ callback on_main(result, error):
      btn 恢复 "语音评分"
      ├─ __TIMEOUT__ → 重试/关闭对话框
      │    ├─ 重试 → _do_voice_score()（递归）
      │    └─ 关闭 → resume → 返回
      ├─ error → QMessageBox(错误信息) → resume → 返回
      └─ 成功  → _show_score_result_dialog() → 关闭 → resume → 返回
```

### 7.3 引擎切换状态机

```
点击设置菜单 → 展开"语音评分引擎"子菜单
  → 显示 4 个引擎，当前选中引擎有 ✓ 标记
  → 用户点击目标引擎 → _on_select_engine(key)
      │
      ├─ key == 当前引擎 → 无操作（幂等）
      │
      └─ key != 当前引擎
            → scoring_cfg.save(key)        # 写入 scoring_engine.json
            → self._voice_scorer = None    # 清除缓存
            → 下次调用 _get_active_scorer() 时惰性创建新引擎实例
```

---

## 8. UI 设计规范

### 8.1 色彩体系

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `_BLUE` | `#003087` | 主品牌色（按钮、标题、高亮） |
| `_GOLD` | `#FFD700` | 金色（预留）|
| `_BG` | `#FFFFFF` | 页面背景 |
| `_LIGHT` | `#F5F7FA` | 面板/计时栏背景 |
| `_BORDER` | `#DDE3EE` | 边框颜色 |
| `_HI` | `#EEF3FF` | 悬停高亮背景 |

### 8.2 字体规格

| 用途 | 字号 | 样式 |
|------|------|------|
| App 主标题 | 40px | Bold |
| Header 标题 | 18px | Bold |
| 题目标题 | 21px | Bold |
| 题目正文 | 19px | Normal，行距 1.8 |
| 答案正文 | 14pt Calibri | Normal，行距 1.5，#333333 |
| 定时器显示 | 34px | Bold，危险时变 #CC0000（≤10s）|
| 按钮文字（大）| 20px | Bold |
| 按钮文字（小）| 15px | Bold |

### 8.3 图标规范

所有头部图标均通过 **QPainter 手绘**，无外部图标库依赖：

| 图标 | 设计描述 | 尺寸 |
|------|---------|------|
| 🏠 Home | 等腰三角形屋顶 + 矩形房体 + 门线 | 24×24 |
| 📖 Answer | 圆角矩形书本 + 书脊线 + 2 条页面线 | 24×24 |
| ⚙ Settings | 外圆 + 内孔 + 4 个方向齿牙 | 24×24 |
| × Exit | 两条交叉对角线 | 24×24 |
| 🎵 Wave | 5 柱对称声波图（喇叭形）| 20×20 |
| 🎤 Mic | 胶囊形话筒体 + 半圆架 + 竖线+底座 | 24×24 |

按钮容器：30×30px，透明背景，悬停时 `rgba(255,255,255,0.18)` 半透明白色。

---

## 9. 数据格式与配置文件

### 9.1 运行时目录结构（完整版）

```
TOEIC_Speaking_Pro.exe        ← 主程序
question_bank.xlsx             ← 题库（必须）
app_icon.ico                  ← 应用图标
│
├── 自动生成的运行时文件
│   ├── toeic_trial.dat       ← 试用时间戳（首次启动生成）
│   ├── toeic_license.dat     ← 授权文件（激活后生成）
│   ├── marks.json            ← 标记数据（首次标记时生成）
│   └── scoring_engine.json   ← 引擎选择（首次切换时生成）
│
├── 按需创建的配置文件（首次配置评分时生成）
│   ├── xunfei_config.json    ← 讯飞 ISE 密钥
│   ├── tencent_config.json   ← 腾讯云智聆密钥
│   └── chivox_config.json    ← 驰声 Chivox 密钥
│
├── 可选文件（用户手动放置）
│   └── dev_mode.txt          ← 开发者模式触发文件（空文件即可）
│
├── images/
│   └── set1/
│       ├── q3.jpg            ← Part 2 图片
│       └── q4.jpg
│
├── records/
│   ├── set_1/                ← 考试录音（自动生成）
│   │   ├── p1_q1_20260324_093012.wav
│   │   └── p1_q1_20260324_093012.txt  ← STT 转写（有 vosk 时）
│   ├── review/               ← 专项训练录音
│   └── mic_test/             ← 试音录音（临时）
│
└── model/
    └── (vosk 模型文件)       ← 可选，离线 STT
```

### 9.2 scoring_engine.json

```json
{
  "engine": "xunfei"
}
```

有效值：`"local"` / `"xunfei"` / `"tencent"` / `"chivox"`

### 9.3 xunfei_config.json

```json
{
  "app_id":     "12345678",
  "api_key":    "abcdef1234567890abcdef1234567890",
  "api_secret": "ABCDEF1234567890abcdef1234567890"
}
```

### 9.4 tencent_config.json

```json
{
  "app_id":     "AKIDxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "api_key":    "SecretKey_placeholder",
  "api_secret": "(reserved)"
}
```

### 9.5 chivox_config.json

```json
{
  "app_id":     "your_chivox_appid",
  "api_key":    "your_api_key",
  "api_secret": "your_api_secret"
}
```

### 9.6 marks.json

```json
{
  "1:p1:0": {"weak": false, "high_freq": true},
  "1:p3:2": {"weak": true,  "high_freq": false},
  "2:p5:0": {"weak": true,  "high_freq": true}
}
```

### 9.7 题库 Excel 格式（`question_bank.xlsx`）

| Sheet | 关键列 |
|-------|-------|
| Sets | set_id, set_name |
| Part1 | set_id, text, answer |
| Part2 | set_id, image（相对路径）, answer |
| Part3 | set_id, background（仅第一行）, question_text, answer |
| Part4 | set_id, info（仅第一行）, question_text, answer |
| Part5 | set_id, text, answer |

---

## 10. 打包与发布

### 10.1 PyInstaller 关键配置

| 配置项 | 值 |
|--------|---|
| `console` | `False`（无命令行窗口）|
| `onefile` | 单文件 EXE |
| `upx` | `True`（体积压缩）|
| `icon` | `app_icon.ico` |

**关键 hiddenimports（含 v1.1 新增）：**

```
# 应用模块
engine, window, recorder, tts_manager, license_manager
marks_manager, review_engine, voice_scorer
scoring_engine_config  ← v1.1 新增
alt_scorers            ← v1.1 新增

# 框架
pyttsx3.drivers.sapi5, PyQt6.sip
openpyxl, websocket._*, vosk
```

### 10.2 GitHub Actions 自动构建

**触发条件：**
- `push` 到 `main` 分支（`toeic_simulator/**` 变更时）
- `workflow_dispatch`（手动触发）

**构建环境：** `windows-latest`，Python 3.11

**构建流程：**
```
Checkout → pip install -r requirements.txt
         → pyinstaller toeic_pro.spec --clean --noconfirm
         → 组装 release/ 目录（EXE + 题库 + 图片 + README）
         → 压缩为 zip
         → 上传 artifact（保留 30 天）
         → 发布 GitHub Release
```

**产物命名：** `TOEIC_Speaking_Pro_Windows_v1.0.{run_number}.zip`

**下载地址：** `https://github.com/xiaobaili-976/RUthirsty-cordova/releases`

---

## 11. 注意事项与已知限制

### 11.1 计时器（最高优先级约束）

> ⚠️ **铁律：ExamEngine 的计时器、TTS、录音触发逻辑永不修改。**

| 约束 | 规定 |
|------|------|
| 语音评分 | 打开对话框立即 `pause_timer()`，关闭立即 `resume_timer()` |
| 录音回放 | 纯后台线程，不调用任何 Engine API |
| 麦克风试音 | 独立 QTimer，与考试 QTimer 零关联 |

### 11.2 语音评分相关

| 问题 | 说明 |
|------|------|
| API 密钥安全 | 明文 JSON 存储，不要提交到公开代码仓库 |
| 讯飞评分语言 | 英语文本评分准确率更高；建议 `answer` 字段使用英文 |
| 无参考答案 | 发送空字符串，评分结果可能不准确 |
| 5s 超时 | 网络慢或服务繁忙时触发，重试通常成功 |
| 腾讯/驰声/本地 | 当前版本框架已就绪，API 完整实现将在后续版本发布 |

### 11.3 开发者模式相关

| 问题 | 说明 |
|------|------|
| 密码区分大小写 | `TOEIC_DEV_2024` 全大写（含下划线） |
| dev_mode.txt 路径 | 必须与 `.exe` 同目录；源码运行时为 `toeic_simulator/` 目录 |
| 重启生效（文件方式）| 文件触发仅在启动时检测，运行中放置需重启 |
| 开发者模式不写文件 | 密码方式的开发者状态**不持久化**，重启后失效（文件方式持久）|

### 11.4 授权机制相关

| 问题 | 说明 |
|------|------|
| 机器码平台依赖 | 依赖 `wmic`，仅 Windows 准确；其他平台使用 fallback |
| 混淆强度 | XOR+Base64 仅防止直接查看，非密码学安全 |
| 时钟回拨 | 手动改回系统时间可延长试用期 |

### 11.5 已知限制（当前版本不包含）

| 功能 | 状态 |
|------|------|
| 腾讯云/驰声/本地评分完整实现 | 开发中 |
| 云端同步 / 用户账号 | 无计划 |
| 移动端 | 无计划 |
| 跨会话做题历史 | 无计划 |
| 自动更新 | 无（通过 GitHub Release 手动下载）|

---

## 12. 开发与维护指南

### 12.1 环境搭建

```bash
# 安装依赖
pip install -r toeic_simulator/requirements.txt

# 生成图标
cd toeic_simulator
python make_icon.py

# 迁移题库（如有旧 JSON）
python make_question_bank_xlsx.py

# 启动开发版（文件方式开发者模式）
touch dev_mode.txt
python main.py
```

### 12.2 开发者模式快速启动

```bash
# 方式一：文件触发（推荐，持久）
echo "" > toeic_simulator/dev_mode.txt
python toeic_simulator/main.py

# 方式二：运行后按 Ctrl+Shift+T
python toeic_simulator/main.py
# → 按 Ctrl+Shift+T → 输入 TOEIC_DEV_2024
```

### 12.3 新增题目步骤

1. 打开 `question_bank.xlsx`
2. 在 `Sets` 表新增 `set_id` 和 `set_name`
3. 在 `Part1`–`Part5` 各表补充对应 `set_id` 行
4. Part 3/4 的 `background`/`info` 仅在第一行填写
5. 保存并重启软件

### 12.4 新增评分引擎步骤

1. 在 `scoring_engine_config.py` 的 `ENGINES` 列表中添加 `(key, label)` 条目
2. 在 `alt_scorers.py` 中新建继承 `_ApiBaseScorer` 的类
3. 在 `window.py` 的 `_get_active_scorer()` 中添加 `elif engine == "newkey"` 分支
4. 在 `window.py` 的 `_show_scorer_credentials_dialog()` 的 `_titles` 字典中添加对应标题和提示文字
5. 在 `toeic_pro.spec` 的 `hiddenimports` 中添加新模块名

### 12.5 新增功能开发原则

1. **不修改** `engine.py` 中的 `_run`, `_tick`, `_on_tts_done`, `_advance` 方法
2. 计时器相关功能必须通过 `pause_timer` / `resume_timer` 配合
3. 新增 UI 页面走 `QStackedWidget` 机制（index ≥ 4）
4. 线程任务通过 `QTimer.singleShot(0, ...)` 回调主线程
5. 新依赖同时加入 `requirements.txt` 和 `toeic_pro.spec` 的 `hiddenimports`

### 12.6 打包发布流程

```bash
# 本地测试打包
cd toeic_simulator
pyinstaller toeic_pro.spec --clean --noconfirm
# 产物：dist/TOEIC_Speaking_Pro.exe（Windows）或 dist/TOEIC_Speaking_Pro（Linux）

# 正式发布：推送到 main 分支自动触发 GitHub Actions
git push origin main
# → Actions 构建 Windows EXE → 自动发布 GitHub Release → 下载 zip
```

### 12.7 常见问题排查

| 现象 | 排查方向 |
|------|---------|
| EXE 无声音 | 检查 Windows 英语 TTS 语音包（控制面板→语音）|
| 录音无效 | 检查麦克风驱动、系统隐私权限（允许桌面应用访问麦克风）|
| 图片不显示 | 确认 `images/` 与 EXE 同目录，路径与 xlsx 一致 |
| 语音评分超时 | 检查网络、讯飞账号服务余额、API 密钥是否正确 |
| 试用期异常 | 删除 `toeic_trial.dat` 重置（仅开发/测试用）|
| 激活失败 | 确认邀请码格式 `BASE-XXXXXX000`，机器码是否匹配 |
| EXE 报毒 | PyInstaller 打包常被误报，可提交厂商白名单或进行代码签名 |
| 切换引擎后评分报错 | 确认已填写新引擎的 API 密钥，或检查网络连接 |
| 开发者模式失效 | 密码方式不持久化，重启后失效，改用 `dev_mode.txt` 文件方式 |

---

*本文档基于源代码自动分析生成，如有歧义以源代码为准。*
*最后更新：2026-03-24 | TOEIC Speaking Pro v1.1*
