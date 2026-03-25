# 知知音乐

一款面向音乐学习者的 Android 应用，集尤克里里练习、演唱训练、乐理知识与曲库管理于一体，内置 AI 音频分析能力。

## 功能模块

- **尤克里里练习**：和弦识别、指法辅助
- **演唱练习**：录音 + AI 音高检测（CREPE 模型），实时反馈演唱准确度
- **乐理知识库**：系统化音乐理论学习内容
- **曲库管理**：歌曲收藏与练习进度跟踪
- **辅助功能**：TTS 朗读、PDF 导出、内容分享

## 项目结构

```
zhizhi_music/
├── app/src/main/
│   ├── java/com/zhizhi/music/
│   │   ├── ai/                # TFLite 模型推理（和弦识别、音高检测、RNNoise 降噪）
│   │   ├── audio/             # 录音与播放
│   │   ├── data/              # Room 数据库、数据模型与 Repository
│   │   ├── ui/                # 各功能 Fragment + ViewModel
│   │   │   ├── home/          # 首页
│   │   │   ├── ukulele/       # 尤克里里练习
│   │   │   ├── singing/       # 演唱练习
│   │   │   ├── knowledge/     # 乐理知识
│   │   │   └── library/       # 曲库
│   │   └── util/              # TTS、PDF 导出、分享等工具类
│   └── res/                   # 布局、资源、导航图
└── build.gradle
```

## 环境要求

- Android Studio Hedgehog 或更高版本
- JDK 17
- Android SDK，compileSdk 34，minSdk 28

## 构建

```bash
cd zhizhi_music
./gradlew assembleDebug
```

生成的 APK 位于 `app/build/outputs/apk/debug/`。

## 技术栈

- Kotlin
- Android Jetpack（ViewModel、Room、Navigation、ViewBinding）
- TensorFlow Lite（CREPE 音高检测、和弦识别、RNNoise 降噪）
- RecyclerView、MediaRecorder、MediaPlayer

## 权限

| 权限 | 用途 |
|------|------|
| `RECORD_AUDIO` | 录音练习 |
| `READ_MEDIA_AUDIO` | 读取本地音频文件 |
| `WRITE_EXTERNAL_STORAGE` | 导出 PDF（Android 9 及以下） |
| `FOREGROUND_SERVICE` | 后台播放 |

## 许可证

MIT License
