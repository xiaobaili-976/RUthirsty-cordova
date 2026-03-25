package com.zhizhi.music.ai

import android.content.Context
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

/**
 * RNNoise-based deep noise reduction.
 * Model: rnnoise.tflite (place in assets/models/)
 * Processes 16kHz mono PCM audio, outputs denoised audio.
 */
class RNNoiseProcessor(context: Context) : BaseTFLiteModel(context, "rnnoise.tflite") {

    companion object {
        const val FRAME_SIZE = 480  // 30ms at 16kHz
    }

    /**
     * Denoise a float array of PCM samples.
     * If model not loaded, returns original samples (graceful fallback).
     */
    fun denoise(samples: FloatArray): FloatArray {
        if (!isLoaded) return samples

        val output = FloatArray(samples.size)
        val numFrames = samples.size / FRAME_SIZE

        for (i in 0 until numFrames) {
            val frame = samples.copyOfRange(i * FRAME_SIZE, (i + 1) * FRAME_SIZE)
            val inputBuffer = floatArrayToByteBuffer(frame)

            val outputBuffer = ByteBuffer.allocateDirect(FRAME_SIZE * 4)
            outputBuffer.order(ByteOrder.nativeOrder())

            try {
                interpreter?.run(inputBuffer, outputBuffer)
                outputBuffer.rewind()
                for (j in 0 until FRAME_SIZE) {
                    output[i * FRAME_SIZE + j] = outputBuffer.float
                }
            } catch (e: Exception) {
                // Fallback: copy original frame
                frame.copyInto(output, i * FRAME_SIZE)
            }
        }
        return output
    }

    /**
     * Simple adaptive noise gate as fallback when model unavailable.
     * Estimates noise floor and suppresses low-amplitude noise.
     */
    fun applyNoiseGate(samples: FloatArray, threshold: Float = 0.02f): FloatArray {
        // Calculate RMS of first 0.5s as noise floor estimate
        val noiseFloorSamples = minOf(samples.size, 8000)
        var sumSq = 0.0
        for (i in 0 until noiseFloorSamples) sumSq += samples[i].toDouble() * samples[i]
        val noiseRms = sqrt(sumSq / noiseFloorSamples).toFloat()
        val gate = maxOf(threshold, noiseRms * 2f)

        return FloatArray(samples.size) { i ->
            if (Math.abs(samples[i]) < gate) 0f else samples[i]
        }
    }
}
