package com.zhizhi.music.ui.ukulele

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.zhizhi.music.ZhizhiApp
import com.zhizhi.music.ai.AudioProcessor
import com.zhizhi.music.audio.AudioPlayer
import com.zhizhi.music.audio.AudioRecorder
import com.zhizhi.music.data.model.Practice
import com.zhizhi.music.data.repository.ProgressRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File

class UkuleleViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = ProgressRepository(ZhizhiApp.getInstance().database)
    private val recorder = AudioRecorder()
    private val audioProcessor = AudioProcessor(app)
    private val player = AudioPlayer(app)

    // Recording state
    private val _isRecording = MutableLiveData(false)
    val isRecording: LiveData<Boolean> = _isRecording

    private val _recordingSeconds = MutableLiveData(0)
    val recordingSeconds: LiveData<Int> = _recordingSeconds

    private val _amplitude = MutableLiveData(0)
    val amplitude: LiveData<Int> = _amplitude

    // Analysis result
    private val _result = MutableLiveData<AudioProcessor.AnalysisResult?>()
    val result: LiveData<AudioProcessor.AnalysisResult?> = _result

    private val _isAnalyzing = MutableLiveData(false)
    val isAnalyzing: LiveData<Boolean> = _isAnalyzing

    // Metronome
    private val _bpm = MutableLiveData(80)
    val bpm: LiveData<Int> = _bpm

    private val _metronomeOn = MutableLiveData(false)
    val metronomeOn: LiveData<Boolean> = _metronomeOn

    private var recordingFile: File? = null
    private var timerJob: Job? = null
    private var metronomeJob: Job? = null
    private val _metronomeTick = MutableLiveData(false)
    val metronomeTick: LiveData<Boolean> = _metronomeTick

    init {
        audioProcessor.loadModels()
    }

    fun startRecording(outputDir: File) {
        viewModelScope.launch {
            val file = File(outputDir, "rec_${System.currentTimeMillis()}.pcm")
            recordingFile = file
            _isRecording.value = true
            _recordingSeconds.value = 0

            timerJob = launch {
                while (isActive) {
                    delay(1000)
                    _recordingSeconds.value = (_recordingSeconds.value ?: 0) + 1
                    if ((_recordingSeconds.value ?: 0) >= 60) {
                        stopRecordingAndAnalyze()
                        break
                    }
                }
            }

            recorder.startRecording(file) { amp ->
                _amplitude.postValue(amp)
            }
        }
    }

    fun stopRecordingAndAnalyze(expectedChords: List<String> = emptyList(), bpm: Int = 80) {
        timerJob?.cancel()
        recorder.stopRecording()
        _isRecording.value = false

        val file = recordingFile ?: return
        _isAnalyzing.value = true

        viewModelScope.launch {
            val analysisResult = audioProcessor.analyzeRecording(file, expectedChords, bpm)
            _result.value = analysisResult
            _isAnalyzing.value = false

            // Save practice record
            val practice = Practice(
                practiceType = "ukulele",
                durationSeconds = _recordingSeconds.value ?: 0,
                pitchScore = analysisResult.pitchScore,
                chordScore = analysisResult.chordScore,
                rhythmScore = analysisResult.rhythmScore,
                overallScore = analysisResult.overallScore,
                audioFilePath = file.absolutePath,
                feedback = analysisResult.feedbackText
            )
            repo.insertPractice(practice)
        }
    }

    fun setBpm(bpm: Int) { _bpm.value = bpm }

    fun toggleMetronome() {
        val on = !(_metronomeOn.value ?: false)
        _metronomeOn.value = on
        if (on) startMetronome() else stopMetronome()
    }

    private fun startMetronome() {
        metronomeJob?.cancel()
        metronomeJob = viewModelScope.launch {
            while (isActive && _metronomeOn.value == true) {
                _metronomeTick.value = true
                delay(50)
                _metronomeTick.value = false
                val interval = 60000L / (_bpm.value ?: 80)
                delay(interval - 50)
            }
        }
    }

    private fun stopMetronome() {
        metronomeJob?.cancel()
    }

    fun playDemo(assetName: String) {
        player.playFromAsset(getApplication(), "audio/$assetName.mp3")
    }

    fun stopPlayback() { player.stop() }

    fun increaseBpm() { _bpm.value = ((_bpm.value ?: 80) + 5).coerceAtMost(200) }
    fun decreaseBpm() { _bpm.value = ((_bpm.value ?: 80) - 5).coerceAtLeast(40) }

    override fun onCleared() {
        super.onCleared()
        recorder.release()
        player.release()
        audioProcessor.release()
    }
}
