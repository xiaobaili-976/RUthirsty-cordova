package com.zhizhi.music.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "practices")
data class Practice(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val songId: Int = -1,          // -1 = free practice
    val songTitle: String = "自由练习",
    val practiceType: String,      // "ukulele" | "singing" | "knowledge"
    val durationSeconds: Int,
    val pitchScore: Float = 0f,
    val chordScore: Float = 0f,
    val rhythmScore: Float = 0f,
    val overallScore: Float = 0f,
    val audioFilePath: String = "",
    val errorPositions: String = "", // JSON array of error timestamps
    val feedback: String = "",
    val timestamp: Long = System.currentTimeMillis()
)
