package com.zhizhi.music.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "songs")
data class Song(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val title: String,
    val level: Int,               // 1=入门, 2=中等, 3=进阶
    val levelName: String,        // "入门" / "中等" / "进阶"
    val difficulty: Int,          // 1-5 星级
    val chords: String,           // 所用和弦，逗号分隔
    val bpm: Int,                 // 标准速度
    val demoAudioPath: String,    // 示范音频资源名
    val slowAudioPath: String,    // 慢速音频资源名
    val leftHandAudioPath: String,// 左手音轨
    val rightHandAudioPath: String,// 右手音轨
    val sheetMusicPath: String,   // 简谱+和弦谱 JSON
    val voiceTipsText: String,    // 语音弹奏要点文字
    val isUnlocked: Boolean = true,
    val isFavorite: Boolean = false,
    val playCount: Int = 0,
    val bestScore: Float = 0f
)
