package com.zhizhi.music.data.database

import androidx.lifecycle.LiveData
import androidx.room.*
import com.zhizhi.music.data.model.Practice
import com.zhizhi.music.data.model.UserProgress

@Dao
interface ProgressDao {

    // --- Practice records ---
    @Insert
    suspend fun insertPractice(practice: Practice): Long

    @Query("SELECT * FROM practices ORDER BY timestamp DESC")
    fun getAllPractices(): LiveData<List<Practice>>

    @Query("SELECT * FROM practices WHERE timestamp >= :since ORDER BY timestamp DESC")
    fun getPracticesSince(since: Long): LiveData<List<Practice>>

    @Query("SELECT SUM(durationSeconds) FROM practices WHERE timestamp >= :dayStart AND timestamp < :dayEnd")
    suspend fun getDayTotalSeconds(dayStart: Long, dayEnd: Long): Int?

    @Query("SELECT SUM(durationSeconds) FROM practices WHERE timestamp >= :weekStart")
    suspend fun getWeekTotalSeconds(weekStart: Long): Int?

    @Query("SELECT * FROM practices ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentPractices(limit: Int): LiveData<List<Practice>>

    @Query("SELECT AVG(overallScore) FROM practices WHERE practiceType = :type")
    suspend fun getAverageScore(type: String): Float?

    // --- User progress ---
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveUserProgress(progress: UserProgress)

    @Query("SELECT * FROM user_progress WHERE id = 1")
    fun getUserProgress(): LiveData<UserProgress?>

    @Query("SELECT * FROM user_progress WHERE id = 1")
    suspend fun getUserProgressOnce(): UserProgress?
}
