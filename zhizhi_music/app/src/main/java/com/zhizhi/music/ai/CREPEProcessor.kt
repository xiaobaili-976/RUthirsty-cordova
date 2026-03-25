package com.zhizhi.music.ai

import android.content.Context
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * CREPE pitch detection model (TFLite version).
 * Model: crepe.tflite (place in assets/models/)
 * Input: 1024-sample audio window at 16kHz
 * Output: pitch in Hz with confidence
 */
class CREPEProcessor(context: Context) : BaseTFLiteModel(context, "crepe.tflite") {

    companion object {
        const val WINDOW_SIZE = 1024
        const val HOP_SIZE = 512
        const val CONFIDENCE_THRESHOLD = 0.5f

        // CREPE frequency bins (20Hz to 1975Hz, 360 bins, cents)
        private const val CENTS_MIN = 1997.3794084376191f
        private const val CENTS_MAX = 7180.0f

        val NOTE_NAMES = arrayOf("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    }

    data class PitchResult(
        val pitchHz: Float,
        val noteName: String,
        val octave: Int,
        val centsOffset: Float,  // deviation from perfect pitch in cents
        val confidence: Float,
        val isInTune: Boolean    // within ±25 cents
    )

    /**
     * Detect pitch from audio samples.
     * Returns list of pitch results for each frame.
     */
    fun detectPitch(samples: FloatArray): List<PitchResult> {
        val results = mutableListOf<PitchResult>()
        val numFrames = (samples.size - WINDOW_SIZE) / HOP_SIZE + 1

        for (i in 0 until numFrames) {
            val start = i * HOP_SIZE
            val frame = samples.copyOfRange(start, (start + WINDOW_SIZE).coerceAtMost(samples.size))

            val result = if (isLoaded) {
                runModelInference(frame)
            } else {
                // Fallback: YIN algorithm
                detectPitchYIN(frame)
            }
            if (result != null) results.add(result)
        }
        return results
    }

    private fun runModelInference(frame: FloatArray): PitchResult? {
        return try {
            val normalizedFrame = normalizeAudio(frame)
            val inputBuffer = floatArrayToByteBuffer(normalizedFrame)
            val output = Array(1) { FloatArray(360) }

            interpreter?.run(inputBuffer, output)

            val activations = output[0]
            val maxIdx = activations.indices.maxByOrNull { activations[it] } ?: return null
            val confidence = activations[maxIdx]

            if (confidence < CONFIDENCE_THRESHOLD) return null

            // Convert bin index to frequency
            val cents = CENTS_MIN + maxIdx * (CENTS_MAX - CENTS_MIN) / 360f
            val hz = 10f.pow(cents / 1200f)

            hzToPitchResult(hz, confidence)
        } catch (e: Exception) {
            null
        }
    }

    /**
     * YIN pitch detection algorithm as offline fallback.
     */
    private fun detectPitchYIN(samples: FloatArray, threshold: Float = 0.15f): PitchResult? {
        val n = samples.size
        val half = n / 2
        val yin = FloatArray(half)

        yin[0] = 1f
        var runningSum = 0f

        for (tau in 1 until half) {
            var diff = 0f
            for (j in 0 until half) {
                val d = samples[j] - samples[j + tau]
                diff += d * d
            }
            yin[tau] = diff
            runningSum += diff
            yin[tau] *= tau / runningSum
        }

        var tauEstimate = -1
        for (tau in 2 until half) {
            if (yin[tau] < threshold) {
                while (tau + 1 < half && yin[tau + 1] < yin[tau]) {
                    if (yin[tau] < threshold) {
                        tauEstimate = tau
                        break
                    }
                }
                if (tauEstimate != -1) break
            }
        }

        if (tauEstimate == -1) return null
        val hz = 16000f / tauEstimate
        if (hz < 50f || hz > 2000f) return null

        return hzToPitchResult(hz, 0.8f)
    }

    private fun hzToPitchResult(hz: Float, confidence: Float): PitchResult? {
        if (hz <= 0) return null
        val midiNote = 12 * (ln(hz / 440f) / ln(2f)) + 69f
        val nearestMidi = Math.round(midiNote)
        val cents = (midiNote - nearestMidi) * 100f
        val noteIndex = ((nearestMidi % 12) + 12) % 12
        val octave = nearestMidi / 12 - 1

        return PitchResult(
            pitchHz = hz,
            noteName = NOTE_NAMES[noteIndex],
            octave = octave,
            centsOffset = cents,
            confidence = confidence,
            isInTune = abs(cents) <= 25f
        )
    }

    private fun normalizeAudio(samples: FloatArray): FloatArray {
        val maxAbs = samples.maxOfOrNull { abs(it) } ?: 1f
        return if (maxAbs > 0) FloatArray(samples.size) { samples[it] / maxAbs }
        else samples
    }

    /**
     * Calculate pitch accuracy score (0-100) from a series of pitch results.
     * Compares against target note.
     */
    fun calculatePitchScore(results: List<PitchResult>, targetNote: String): Float {
        if (results.isEmpty()) return 0f
        val inTuneCount = results.count { it.isInTune && it.noteName == targetNote }
        return (inTuneCount.toFloat() / results.size * 100f).coerceIn(0f, 100f)
    }
}
