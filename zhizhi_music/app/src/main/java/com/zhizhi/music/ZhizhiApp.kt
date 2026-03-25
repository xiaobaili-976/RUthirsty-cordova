package com.zhizhi.music

import android.app.Application
import android.content.Context
import com.zhizhi.music.data.database.AppDatabase
import com.zhizhi.music.util.PreferencesManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class ZhizhiApp : Application() {

    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    val database: AppDatabase by lazy { AppDatabase.getInstance(this) }

    override fun onCreate() {
        super.onCreate()
        instance = this
        // Initialize preferences with defaults
        PreferencesManager.init(this)
        // Pre-populate song database on first launch
        applicationScope.launch {
            database.songDao().getCount().let { count ->
                if (count == 0) {
                    com.zhizhi.music.data.SongData.getAllSongs().forEach {
                        database.songDao().insertSong(it)
                    }
                }
            }
        }
    }

    companion object {
        @Volatile
        private var instance: ZhizhiApp? = null

        fun getInstance(): ZhizhiApp = instance
            ?: throw IllegalStateException("Application not initialized")

        fun getAppContext(): Context = getInstance().applicationContext
    }
}
