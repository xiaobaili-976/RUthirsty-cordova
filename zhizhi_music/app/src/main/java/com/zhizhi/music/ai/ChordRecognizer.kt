package com.zhizhi.music.ai

import android.content.Context
import kotlin.math.abs
import kotlin.math.sqrt

/**
 * Ukulele chord recognition model.
 * Model: chord_ukulele.tflite (place in assets/models/)
 * Input: chroma feature vector (12-dim) extracted from audio
 * Output: chord class probabilities (21 common chords)
 */
class ChordRecognizer(context: Context) : BaseTFLiteModel(context, "chord_ukulele.tflite") {

    companion object {
        val CHORD_NAMES = arrayOf(
            "C", "Cm", "C7", "D", "Dm", "D7",
            "E", "Em", "E7", "F", "Fm", "F7",
            "G", "Gm", "G7", "A", "Am", "A7",
            "B", "Bm", "B7"
        )
        const val SAMPLE_RATE = 16000
        const val HOP_SIZE = 512
        const val N_CHROMA = 12
        const val CONFIDENCE_THRESHOLD = 0.55f
    }

    data class ChordResult(
        val chordName: String,
        val confidence: Float,
        val isMuffled: Boolean,     // detected muffled/buzzy sound
        val isWeak: Boolean,        // insufficient pressing force
        val switchDelay: Boolean    // chord switch was too slow
    )

    /**
     * Recognize chord from audio samples.
     * Returns detected chord with quality metrics.
     */
    fun recognizeChord(samples: FloatArray): ChordResult {
        val chroma = extractChromaFeatures(samples)
        val isMuffled = detectMuffledSound(samples)
        val isWeak = detectWeakPressing(samples)

        return if (isLoaded) {
            runChordInference(chroma, isMuffled, isWeak)
        } else {
            // Fallback: template matching
            matchChordTemplate(chroma, isMuffled, isWeak)
        }
    }

    /**
     * Analyze a sequence of chord segments to detect switch delays.
     */
    fun analyzeChordSequence(
        samples: FloatArray,
        expectedChords: List<String>,
        segmentSizeMs: Int = 2000
    ): List<ChordResult> {
        val segmentSamples = (segmentSizeMs * SAMPLE_RATE / 1000)
        val results = mutableListOf<ChordResult>()

        for (i in expectedChords.indices) {
            val start = i * segmentSamples
            val end = ((i + 1) * segmentSamples).coerceAtMost(samples.size)
            if (start >= samples.size) break

            val segment = samples.copyOfRange(start, end)
            val result = recognizeChord(segment)
            val prevChord = if (i > 0) expectedChords[i - 1] else null
            val switchDelay = detectSwitchDelay(segment, prevChord, expectedChords[i])
            results.add(result.copy(switchDelay = switchDelay))
        }
        return results
    }

    private fun runChordInference(
        chroma: FloatArray,
        isMuffled: Boolean,
        isWeak: Boolean
    ): ChordResult {
        return try {
            val inputBuffer = floatArrayToByteBuffer(chroma)
            val output = Array(1) { FloatArray(CHORD_NAMES.size) }
            interpreter?.run(inputBuffer, output)

            val probs = output[0]
            val maxIdx = probs.indices.maxByOrNull { probs[it] } ?: 0
            val confidence = probs[maxIdx]

            ChordResult(
                chordName = if (confidence >= CONFIDENCE_THRESHOLD) CHORD_NAMES[maxIdx] else "?",
                confidence = confidence,
                isMuffled = isMuffled,
                isWeak = isWeak,
                switchDelay = false
            )
        } catch (e: Exception) {
            ChordResult("?", 0f, isMuffled, isWeak, false)
        }
    }

    private fun matchChordTemplate(
        chroma: FloatArray,
        isMuffled: Boolean,
        isWeak: Boolean
    ): ChordResult {
        // Simple template matching
        val templates = mapOf(
            "C"  to floatArrayOf(1f,0f,0f,0f,1f,0f,0f,1f,0f,0f,0f,0f),
            "Am" to floatArrayOf(1f,0f,0f,0f,1f,0f,0f,0f,0f,1f,0f,0f),
            "F"  to floatArrayOf(1f,0f,0f,0f,0f,1f,0f,0f,0f,1f,0f,0f),
            "G"  to floatArrayOf(0f,0f,1f,0f,0f,0f,0f,1f,0f,0f,0f,1f),
            "Dm" to floatArrayOf(0f,0f,1f,0f,0f,1f,0f,0f,0f,1f,0f,0f),
            "G7" to floatArrayOf(0f,0f,1f,0f,0f,1f,0f,1f,0f,0f,0f,1f),
            "Em" to floatArrayOf(0f,0f,0f,0f,1f,0f,0f,1f,0f,0f,0f,1f)
        )

        var bestChord = "?"
        var bestScore = -1f
        templates.forEach { (chord, template) ->
            val score = cosineSimilarity(chroma, template)
            if (score > bestScore) {
                bestScore = score
                bestChord = chord
            }
        }

        return ChordResult(
            chordName = if (bestScore > 0.5f) bestChord else "?",
            confidence = bestScore,
            isMuffled = isMuffled,
            isWeak = isWeak,
            switchDelay = false
        )
    }

    private fun extractChromaFeatures(samples: FloatArray): FloatArray {
        val chroma = FloatArray(N_CHROMA)
        // Simplified chroma extraction via spectral energy in pitch classes
        val windowSize = 2048
        val halfWin = windowSize / 2
        if (samples.size < windowSize) return chroma

        // Use energy-based approach
        val centerSamples = samples.copyOfRange(
            (samples.size - windowSize) / 2,
            (samples.size + windowSize) / 2
        )

        for (bin in 0 until halfWin) {
            val freq = bin.toFloat() * SAMPLE_RATE / windowSize
            if (freq > 80f && freq < 2000f) {
                val pitchClass = (12 * Math.log(freq / 440.0) / Math.log(2.0) + 9).toInt()
                    .let { ((it % 12) + 12) % 12 }
                val energy = centerSamples[bin] * centerSamples[bin]
                chroma[pitchClass] += energy
            }
        }

        // Normalize
        val max = chroma.maxOrNull() ?: 1f
        if (max > 0) chroma.forEachIndexed { i, v -> chroma[i] = v / max }
        return chroma
    }

    private fun detectMuffledSound(samples: FloatArray): Boolean {
        // Muffled sound has low high-frequency energy ratio
        val mid = samples.size / 2
        val lowEnergy = samples.take(mid).sumOf { (it * it).toDouble() }
        val highEnergy = samples.drop(mid).sumOf { (it * it).toDouble() }
        return highEnergy < lowEnergy * 0.1
    }

    private fun detectWeakPressing(samples: FloatArray): Boolean {
        val rms = sqrt(samples.sumOf { (it * it).toDouble() } / samples.size)
        return rms < 0.05
    }

    private fun detectSwitchDelay(
        segment: FloatArray,
        prevChord: String?,
        currentChord: String?
    ): Boolean {
        if (prevChord == null || currentChord == null) return false
        // If first 30% of segment is silent, assume chord switch was delayed
        val silentThreshold = 0.03f
        val checkEnd = (segment.size * 0.3).toInt()
        val leadingSilence = segment.take(checkEnd).all { abs(it) < silentThreshold }
        return leadingSilence
    }

    private fun cosineSimilarity(a: FloatArray, b: FloatArray): Float {
        var dot = 0f; var normA = 0f; var normB = 0f
        for (i in a.indices) {
            dot += a[i] * b[i]; normA += a[i] * a[i]; normB += b[i] * b[i]
        }
        return if (normA > 0 && normB > 0) dot / (sqrt(normA) * sqrt(normB)) else 0f
    }
}
