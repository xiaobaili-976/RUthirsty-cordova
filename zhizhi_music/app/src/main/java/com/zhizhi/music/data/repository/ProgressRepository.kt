package com.zhizhi.music.data.repository

import androidx.lifecycle.LiveData
import com.zhizhi.music.data.database.AppDatabase
import com.zhizhi.music.data.model.Practice
import com.zhizhi.music.data.model.UserProgress
import java.util.Calendar

class ProgressRepository(private val db: AppDatabase) {

    private val dao = db.progressDao()

    fun getAllPractices(): LiveData<List<Practice>> = dao.getAllPractices()

    fun getRecentPractices(limit: Int = 10): LiveData<List<Practice>> =
        dao.getRecentPractices(limit)

    suspend fun insertPractice(practice: Practice): Long = dao.insertPractice(practice)

    fun getUserProgress(): LiveData<UserProgress?> = dao.getUserProgress()

    suspend fun getUserProgressOnce(): UserProgress = dao.getUserProgressOnce()
        ?: UserProgress().also { dao.saveUserProgress(it) }

    suspend fun getTodayTotalSeconds(): Int {
        val cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        val dayStart = cal.timeInMillis
        cal.add(Calendar.DAY_OF_YEAR, 1)
        val dayEnd = cal.timeInMillis
        return dao.getDayTotalSeconds(dayStart, dayEnd) ?: 0
    }

    suspend fun getWeekTotalSeconds(): Int {
        val cal = Calendar.getInstance()
        cal.set(Calendar.DAY_OF_WEEK, cal.firstDayOfWeek)
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        return dao.getWeekTotalSeconds(cal.timeInMillis) ?: 0
    }

    suspend fun updateProgress(progress: UserProgress) = dao.saveUserProgress(progress)

    suspend fun addPracticeTime(seconds: Int) {
        val current = getUserProgressOnce()
        dao.saveUserProgress(current.copy(
            totalPracticeSeconds = current.totalPracticeSeconds + seconds,
            totalSessions = current.totalSessions + 1
        ))
    }
}
