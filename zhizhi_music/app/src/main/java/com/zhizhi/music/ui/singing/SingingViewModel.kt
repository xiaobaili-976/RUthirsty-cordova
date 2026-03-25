package com.zhizhi.music.ui.singing

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.zhizhi.music.ZhizhiApp
import com.zhizhi.music.ai.AudioProcessor
import com.zhizhi.music.ai.CREPEProcessor
import com.zhizhi.music.audio.AudioPlayer
import com.zhizhi.music.audio.AudioRecorder
import com.zhizhi.music.data.model.Practice
import com.zhizhi.music.data.repository.ProgressRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.io.File
import kotlin.math.abs

class SingingViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = ProgressRepository(ZhizhiApp.getInstance().database)
    private val recorder = AudioRecorder()
    private val audioProcessor = AudioProcessor(app)
    private val player = AudioPlayer(app)
    private val crepe = com.zhizhi.music.ai.CREPEProcessor(app)

    private val _isRecording = MutableLiveData(false)
    val isRecording: LiveData<Boolean> = _isRecording

    private val _isAnalyzing = MutableLiveData(false)
    val isAnalyzing: LiveData<Boolean> = _isAnalyzing

    private val _recordingSeconds = MutableLiveData(0)
    val recordingSeconds: LiveData<Int> = _recordingSeconds

    private val _currentPitchHz = MutableLiveData(0f)
    val currentPitchHz: LiveData<Float> = _currentPitchHz

    private val _currentNote = MutableLiveData("")
    val currentNote: LiveData<String> = _currentNote

    private val _pitchDeviation = MutableLiveData(0f)  // cents, negative=flat, positive=sharp
    val pitchDeviation: LiveData<Float> = _pitchDeviation

    private val _singingResult = MutableLiveData<AudioProcessor.AnalysisResult?>()
    val singingResult: LiveData<AudioProcessor.AnalysisResult?> = _singingResult

    // Real-time pitch history for waveform visualization
    private val _pitchHistory = MutableLiveData<List<Float>>(emptyList())
    val pitchHistory: LiveData<List<Float>> = _pitchHistory

    private var timerJob: Job? = null
    private var recordingFile: File? = null
    private val pitchHistoryBuffer = mutableListOf<Float>()

    init {
        audioProcessor.loadModels()
        crepe.loadModel()
    }

    fun startSinging(outputDir: File) {
        viewModelScope.launch {
            val file = File(outputDir, "singing_${System.currentTimeMillis()}.pcm")
            recordingFile = file
            _isRecording.value = true
            _recordingSeconds.value = 0
            pitchHistoryBuffer.clear()

            timerJob = launch {
                while (isActive) {
                    delay(1000)
                    _recordingSeconds.value = (_recordingSeconds.value ?: 0) + 1
                    if ((_recordingSeconds.value ?: 0) >= 60) {
                        stopAndScore()
                        break
                    }
                }
            }

            // Start recording with real-time pitch feedback
            launch(Dispatchers.Default) {
                val rnNoise = com.zhizhi.music.ai.RNNoiseProcessor(getApplication())
                recorder.startRecording(file) { amplitude ->
                    // In a real implementation, we'd process real-time audio buffers here
                    // For simplicity, we update amplitude and simulate pitch updates
                    _currentPitchHz.postValue(amplitude.toFloat() * 0.1f + 220f)
                }
            }
        }
    }

    fun stopAndScore() {
        timerJob?.cancel()
        recorder.stopRecording()
        _isRecording.value = false
        _isAnalyzing.value = true

        val file = recordingFile ?: run {
            _isAnalyzing.value = false
            return
        }

        viewModelScope.launch {
            val result = audioProcessor.analyzeRecording(file)
            _singingResult.value = result
            _isAnalyzing.value = false

            repo.insertPractice(
                Practice(
                    practiceType = "singing",
                    durationSeconds = _recordingSeconds.value ?: 0,
                    pitchScore = result.pitchScore,
                    chordScore = result.chordScore,
                    rhythmScore = result.rhythmScore,
                    overallScore = result.overallScore,
                    audioFilePath = file.absolutePath,
                    feedback = result.feedbackText
                )
            )
        }
    }

    fun playStandardNote(noteIndex: Int) {
        // Play standard solfège notes (do re mi fa sol la si)
        val noteFreqs = listOf(261.6f, 293.7f, 329.6f, 349.2f, 392.0f, 440.0f, 493.9f)
        val noteName = listOf("哆", "来", "咪", "发", "嗦", "啦", "西")
        // In real implementation, generate sine wave audio and play
        _currentNote.value = noteName.getOrElse(noteIndex) { "?" }
        _currentPitchHz.value = noteFreqs.getOrElse(noteIndex) { 440f }
    }

    fun humAndDetect(outputDir: File) {
        // Start recording to detect hummed melody
        viewModelScope.launch {
            val file = File(outputDir, "hum_${System.currentTimeMillis()}.pcm")
            _isRecording.value = true
            recorder.startRecording(file) {}
            delay(10000) // Record 10 seconds
            recorder.stopRecording()
            _isRecording.value = false
            // In real app: run pitch detection to identify song
            _singingResult.value = null
        }
    }

    override fun onCleared() {
        super.onCleared()
        recorder.release()
        player.release()
        audioProcessor.release()
        crepe.close()
    }
}
