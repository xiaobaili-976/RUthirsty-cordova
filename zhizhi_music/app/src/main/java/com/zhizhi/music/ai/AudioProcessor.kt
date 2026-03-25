package com.zhizhi.music.ai

import android.content.Context
import com.zhizhi.music.audio.AudioRecorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import kotlin.math.abs
import kotlin.math.sqrt

/**
 * Unified audio processing pipeline:
 * PCM audio → RNNoise denoise → Chord/Pitch recognition → Score
 */
class AudioProcessor(private val context: Context) {

    private val rnNoise = RNNoiseProcessor(context)
    private val crepe = CREPEProcessor(context)
    private val chordRecognizer = ChordRecognizer(context)

    data class AnalysisResult(
        val detectedChords: List<String>,
        val pitchResults: List<CREPEProcessor.PitchResult>,
        val chordResults: List<ChordRecognizer.ChordResult>,
        val pitchScore: Float,
        val chordScore: Float,
        val rhythmScore: Float,
        val overallScore: Float,
        val errorPositions: List<Float>,   // time positions in seconds where errors occur
        val hasMuffledSound: Boolean,
        val hasWeakPressing: Boolean,
        val hasChordSwitchDelay: Boolean,
        val feedbackText: String,
        val processingTimeMs: Long
    )

    fun loadModels() {
        rnNoise.loadModel()
        crepe.loadModel()
        chordRecognizer.loadModel()
    }

    fun release() {
        rnNoise.close()
        crepe.close()
        chordRecognizer.close()
    }

    /**
     * Full pipeline: read PCM file → denoise → analyze → score.
     * Must be called from a coroutine.
     */
    suspend fun analyzeRecording(
        pcmFile: File,
        expectedChords: List<String> = emptyList(),
        songBpm: Int = 80
    ): AnalysisResult = withContext(Dispatchers.Default) {
        val startTime = System.currentTimeMillis()

        // 1. Load PCM samples
        val samples = loadPcmFile(pcmFile)

        // 2. Denoise
        val denoised = if (rnNoise.isLoaded) {
            rnNoise.denoise(samples)
        } else {
            rnNoise.applyNoiseGate(samples)
        }

        // 3. Pitch detection
        val pitchResults = crepe.detectPitch(denoised)

        // 4. Chord recognition
        val chordResults = if (expectedChords.isNotEmpty()) {
            chordRecognizer.analyzeChordSequence(denoised, expectedChords)
        } else {
            listOf(chordRecognizer.recognizeChord(denoised))
        }

        val detectedChords = chordResults.map { it.chordName }

        // 5. Score calculation
        val pitchScore = calculatePitchScore(pitchResults)
        val chordScore = calculateChordScore(chordResults, expectedChords)
        val rhythmScore = calculateRhythmScore(denoised, songBpm)
        val overallScore = (pitchScore * 0.35f + chordScore * 0.40f + rhythmScore * 0.25f)
            .coerceIn(0f, 100f)

        // 6. Error positions
        val errorPositions = findErrorPositions(pitchResults, chordResults, samples.size)

        // 7. Quality flags
        val hasMuffled = chordResults.any { it.isMuffled }
        val hasWeak = chordResults.any { it.isWeak }
        val hasSwitchDelay = chordResults.any { it.switchDelay }

        // 8. Feedback
        val feedback = generateFeedback(
            pitchScore, chordScore, rhythmScore, hasMuffled, hasWeak, hasSwitchDelay
        )

        AnalysisResult(
            detectedChords = detectedChords,
            pitchResults = pitchResults,
            chordResults = chordResults,
            pitchScore = pitchScore,
            chordScore = chordScore,
            rhythmScore = rhythmScore,
            overallScore = overallScore,
            errorPositions = errorPositions,
            hasMuffledSound = hasMuffled,
            hasWeakPressing = hasWeak,
            hasChordSwitchDelay = hasSwitchDelay,
            feedbackText = feedback,
            processingTimeMs = System.currentTimeMillis() - startTime
        )
    }

    private fun loadPcmFile(file: File): FloatArray {
        val bytes = file.readBytes()
        val samples = FloatArray(bytes.size / 2)
        for (i in samples.indices) {
            val lo = bytes[i * 2].toInt() and 0xFF
            val hi = bytes[i * 2 + 1].toInt()
            samples[i] = ((hi shl 8) or lo).toShort() / 32768f
        }
        return samples
    }

    private fun calculatePitchScore(pitchResults: List<CREPEProcessor.PitchResult>): Float {
        if (pitchResults.isEmpty()) return 75f
        val inTune = pitchResults.count { it.isInTune && it.confidence > 0.5f }
        return (inTune.toFloat() / pitchResults.size * 100f).coerceIn(0f, 100f)
    }

    private fun calculateChordScore(
        results: List<ChordRecognizer.ChordResult>,
        expected: List<String>
    ): Float {
        if (expected.isEmpty()) {
            val goodChords = results.count { it.confidence > 0.6f && !it.isMuffled && !it.isWeak }
            return if (results.isEmpty()) 75f
            else (goodChords.toFloat() / results.size * 100f).coerceIn(0f, 100f)
        }
        var correct = 0
        results.zip(expected).forEach { (result, exp) ->
            if (result.chordName == exp && !result.isMuffled) correct++
        }
        return (correct.toFloat() / expected.size * 100f).coerceIn(0f, 100f)
    }

    private fun calculateRhythmScore(samples: FloatArray, bpm: Int): Float {
        // Beat detection using onset strength
        val beatIntervalSamples = (AudioRecorder.SAMPLE_RATE * 60f / bpm).toInt()
        val onsets = detectOnsets(samples)
        if (onsets.isEmpty()) return 70f

        var alignedCount = 0
        onsets.forEach { onset ->
            val nearestBeat = Math.round(onset.toFloat() / beatIntervalSamples) * beatIntervalSamples
            val deviation = abs(onset - nearestBeat).toFloat() / beatIntervalSamples
            if (deviation < 0.15f) alignedCount++
        }
        return (alignedCount.toFloat() / onsets.size * 100f).coerceIn(0f, 100f)
    }

    private fun detectOnsets(samples: FloatArray, windowSize: Int = 512): List<Int> {
        val onsets = mutableListOf<Int>()
        var prevEnergy = 0f
        var i = 0
        while (i + windowSize < samples.size) {
            val energy = samples.copyOfRange(i, i + windowSize).let { frame ->
                sqrt(frame.sumOf { (it * it).toDouble() }.toFloat() / windowSize)
            }
            if (energy > prevEnergy * 1.5f && energy > 0.05f) {
                onsets.add(i)
            }
            prevEnergy = energy
            i += windowSize / 2
        }
        return onsets
    }

    private fun findErrorPositions(
        pitchResults: List<CREPEProcessor.PitchResult>,
        chordResults: List<ChordRecognizer.ChordResult>,
        totalSamples: Int
    ): List<Float> {
        val errorPositions = mutableListOf<Float>()
        val sampleRate = AudioRecorder.SAMPLE_RATE.toFloat()

        pitchResults.forEachIndexed { idx, pitch ->
            if (!pitch.isInTune) {
                val timePos = idx * CREPEProcessor.HOP_SIZE / sampleRate
                errorPositions.add(timePos)
            }
        }
        return errorPositions.distinct().sorted()
    }

    private fun generateFeedback(
        pitchScore: Float,
        chordScore: Float,
        rhythmScore: Float,
        hasMuffled: Boolean,
        hasWeak: Boolean,
        hasSwitchDelay: Boolean
    ): String {
        val sb = StringBuilder()
        when {
            chordScore >= 90 && pitchScore >= 90 && rhythmScore >= 90 ->
                sb.append("太棒了！你弹得非常好，每个音都清晰准确！")
            chordScore >= 75 && pitchScore >= 75 ->
                sb.append("弹得不错！有几个地方还可以更好。")
            else -> sb.append("继续加油！每次练习都在进步。")
        }

        if (hasMuffled) sb.append("有几个音有点闷，手指要按实，不要碰到旁边的弦哦。")
        if (hasWeak) sb.append("有些音力气不够，手指要用力按紧琴弦。")
        if (hasSwitchDelay) sb.append("和弦切换有点慢，可以专项练习和弦转换，从慢速开始练。")

        if (pitchScore < 70) sb.append("音准需要加强，可以对照音高练习，先跟着节拍器练。")
        if (rhythmScore < 70) sb.append("节奏需要加强，建议打开节拍器跟着练习，不要赶拍子。")

        return sb.toString()
    }
}
