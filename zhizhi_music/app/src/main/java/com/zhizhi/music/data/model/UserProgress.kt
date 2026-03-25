package com.zhizhi.music.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "user_progress")
data class UserProgress(
    @PrimaryKey
    val id: Int = 1,               // singleton row
    val currentLevel: Int = 1,
    val currentChapter: Int = 1,
    val totalPracticeSeconds: Int = 0,
    val consecutiveDays: Int = 0,
    val lastPracticeDate: String = "",
    val totalSessions: Int = 0,
    val unlockedSongIds: String = "",  // JSON array
    val earnedBadges: String = "",     // JSON array of badge ids
    val checkInDates: String = "",     // JSON array of date strings
    val weeklyGoalSeconds: Int = 1800  // 30 min default
)
