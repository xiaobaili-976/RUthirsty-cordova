package com.zhizhi.music.util

import android.content.Context
import android.content.SharedPreferences

object PreferencesManager {

    private const val PREF_NAME = "zhizhi_prefs"
    private const val KEY_EYE_CARE = "eye_care_mode"
    private const val KEY_CHILD_LOCK = "child_lock"
    private const val KEY_BG_MUSIC = "bg_music"
    private const val KEY_VOICE_READ = "voice_read"
    private const val KEY_FIRST_LAUNCH = "first_launch"
    private const val KEY_SCORING_ENGINE = "scoring_engine"

    private lateinit var prefs: SharedPreferences

    fun init(context: Context) {
        prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    fun isEyeCareMode(): Boolean = prefs.getBoolean(KEY_EYE_CARE, true)
    fun setEyeCareMode(enabled: Boolean) = prefs.edit().putBoolean(KEY_EYE_CARE, enabled).apply()

    fun isChildLock(): Boolean = prefs.getBoolean(KEY_CHILD_LOCK, false)
    fun setChildLock(enabled: Boolean) = prefs.edit().putBoolean(KEY_CHILD_LOCK, enabled).apply()

    fun isBgMusic(): Boolean = prefs.getBoolean(KEY_BG_MUSIC, false)
    fun setBgMusic(enabled: Boolean) = prefs.edit().putBoolean(KEY_BG_MUSIC, enabled).apply()

    fun isVoiceRead(): Boolean = prefs.getBoolean(KEY_VOICE_READ, true)
    fun setVoiceRead(enabled: Boolean) = prefs.edit().putBoolean(KEY_VOICE_READ, enabled).apply()

    fun isFirstLaunch(): Boolean = prefs.getBoolean(KEY_FIRST_LAUNCH, true)
    fun setFirstLaunch(first: Boolean) = prefs.edit().putBoolean(KEY_FIRST_LAUNCH, first).apply()

    fun getScoringEngine(): String = prefs.getString(KEY_SCORING_ENGINE, "offline") ?: "offline"
    fun setScoringEngine(engine: String) = prefs.edit().putString(KEY_SCORING_ENGINE, engine).apply()
}
