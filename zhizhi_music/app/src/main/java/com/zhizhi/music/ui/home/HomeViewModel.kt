package com.zhizhi.music.ui.home

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.zhizhi.music.ZhizhiApp
import com.zhizhi.music.data.model.UserProgress
import com.zhizhi.music.data.repository.ProgressRepository
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class HomeViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = ProgressRepository(ZhizhiApp.getInstance().database)

    val userProgress: LiveData<UserProgress?> = repo.getUserProgress()

    private val _todaySeconds = MutableLiveData(0)
    val todaySeconds: LiveData<Int> = _todaySeconds

    private val _weekSeconds = MutableLiveData(0)
    val weekSeconds: LiveData<Int> = _weekSeconds

    private val _dailyPlan = MutableLiveData<String>()
    val dailyPlan: LiveData<String> = _dailyPlan

    private val _checkInDone = MutableLiveData(false)
    val checkInDone: LiveData<Boolean> = _checkInDone

    init {
        loadTodayStats()
        generateDailyPlan()
        checkTodayCheckIn()
    }

    fun loadTodayStats() {
        viewModelScope.launch {
            _todaySeconds.value = repo.getTodayTotalSeconds()
            _weekSeconds.value = repo.getWeekTotalSeconds()
        }
    }

    private fun generateDailyPlan() {
        viewModelScope.launch {
            val progress = repo.getUserProgressOnce()
            val level = progress.currentLevel
            val plan = when (level) {
                1 -> "今日任务：练习《小星星》和《两只老虎》，先慢速弹奏，再跟着节拍器弹，每首弹3遍。"
                2 -> "今日任务：练习《同桌的你》，重点练习G转Em和弦切换，慢速弹5遍，然后对照评分。"
                else -> "今日任务：练习《孤勇者》，着重攻克Am转F的快速切换，录音评分，达到80分以上！"
            }
            _dailyPlan.value = plan
        }
    }

    private fun checkTodayCheckIn() {
        viewModelScope.launch {
            val progress = repo.getUserProgressOnce()
            val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
            _checkInDone.value = progress.lastPracticeDate == today
        }
    }

    fun doCheckIn() {
        viewModelScope.launch {
            val progress = repo.getUserProgressOnce()
            val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
            if (progress.lastPracticeDate != today) {
                val dates = if (progress.checkInDates.isEmpty()) today
                else "${progress.checkInDates},$today"
                val consecutive = if (isConsecutiveDay(progress.lastPracticeDate, today))
                    progress.consecutiveDays + 1 else 1
                repo.updateProgress(progress.copy(
                    lastPracticeDate = today,
                    consecutiveDays = consecutive,
                    checkInDates = dates
                ))
                _checkInDone.value = true
            }
        }
    }

    private fun isConsecutiveDay(last: String, today: String): Boolean {
        return try {
            val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val lastDate = sdf.parse(last) ?: return false
            val todayDate = sdf.parse(today) ?: return false
            (todayDate.time - lastDate.time) / (1000 * 60 * 60 * 24) == 1L
        } catch (e: Exception) { false }
    }

    fun formatSeconds(seconds: Int): String {
        val m = seconds / 60; val s = seconds % 60
        return String.format("%d分%02d秒", m, s)
    }
}
