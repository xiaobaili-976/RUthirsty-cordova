package com.zhizhi.music.util

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale

class TtsManager(context: Context) : TextToSpeech.OnInitListener {

    private var tts: TextToSpeech = TextToSpeech(context, this)
    private var isReady = false
    private var pendingText: String? = null

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts.setLanguage(Locale.CHINESE)
            if (result != TextToSpeech.LANG_MISSING_DATA &&
                result != TextToSpeech.LANG_NOT_SUPPORTED) {
                isReady = true
                tts.setSpeechRate(0.75f) // Slow for children
                tts.setPitch(1.1f)       // Slightly higher pitch, friendlier
                pendingText?.let { speak(it) }
                pendingText = null
            }
        }
    }

    fun speak(text: String, utteranceId: String = "zhizhi_tts") {
        if (!PreferencesManager.isVoiceRead()) return
        if (isReady) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
        } else {
            pendingText = text
        }
    }

    fun speakQueue(text: String, utteranceId: String = "zhizhi_q") {
        if (!PreferencesManager.isVoiceRead()) return
        if (isReady) {
            tts.speak(text, TextToSpeech.QUEUE_ADD, null, utteranceId)
        }
    }

    fun stop() {
        if (isReady) tts.stop()
    }

    fun setOnDoneListener(listener: () -> Unit) {
        tts.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {}
            override fun onDone(utteranceId: String?) { listener() }
            override fun onError(utteranceId: String?) {}
        })
    }

    fun shutdown() {
        tts.stop()
        tts.shutdown()
    }
}
