TOEIC Speaking Pro  v1.0
==============================================

[启动方式]
  双击 TOEIC_Speaking_Pro.exe，无需安装 Python。

[首次使用]
  软件附带 3 天免费试用期。
  点击右上角齿轮图标可查看剩余时间或输入邀请码激活正版。
  试用到期后弹出激活窗口，输入邀请码或退出程序。
  激活/开发者模式后，使用窗口标题栏的 × 关闭程序即可。

[主要功能]
  · Start Exam      — 完整 TOEIC Speaking 模考（Part 1-5）
  · 专项训练        — 单独练习 Part 1 / 2 / 3 / 4 / 5，计时规则与模考一致
  · 背诵复习模式    — 随机练习 / 答案速背 / 高频题专练 / 薄弱题巩固
  · 回放录音        — 考试/结束后一键回放最近录音，复盘发音
  · 麦克风试音      — 开考前 3 秒试录并自动回放，确认设备正常
  · 成绩报告        — 考试结束自动生成用时、各 PART 录音完成率、薄弱项建议

[题库更新]
  用 Excel 编辑 question_bank.xlsx，保存后重启生效。
  Sheet 结构：Sets | Part1 | Part2 | Part3 | Part4 | Part5

[Part 2 图片]
  将图片放入 images\set1\、images\set2\ 等子文件夹，
  路径须与 xlsx 中一致（如 images/set1/q3.jpg）。

[语音评分]
  需要讯飞开放平台 ISE 服务账号（联网使用）。
  首次点击"语音评分"按钮时程序引导输入 API 密钥。
  评分期间考试计时自动暂停，关闭结果窗口后恢复。

[语音转文字（可选）]
  1. 前往 https://alphacephei.com/vosk/models
  2. 下载 vosk-model-small-en-us（约 40 MB）
  3. 解压后重命名为 model，放在 EXE 同目录，重启生效。

[开发者模式]
  方法一：Ctrl+Shift+T 输入开发口令
  方法二：将 dev_mode.txt 放在 EXE 同目录，重启生效

[系统要求]
  Windows 10 / 11（64 位），无需安装任何依赖。
