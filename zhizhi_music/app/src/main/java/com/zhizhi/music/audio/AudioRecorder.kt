package com.zhizhi.music.audio

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

class AudioRecorder {

    companion object {
        const val SAMPLE_RATE = 16000
        const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
    }

    private var audioRecord: AudioRecord? = null
    private var isRecording = false
    private var recordingFile: File? = null

    fun isRecording() = isRecording

    fun getRecordingFilePath(): String? = recordingFile?.absolutePath

    suspend fun startRecording(outputFile: File, onAmplitudeUpdate: ((Int) -> Unit)? = null) =
        withContext(Dispatchers.IO) {
            recordingFile = outputFile
            val bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT)

            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                CHANNEL_CONFIG,
                AUDIO_FORMAT,
                bufferSize * 4
            )

            audioRecord?.startRecording()
            isRecording = true

            FileOutputStream(outputFile).use { fos ->
                val buffer = ShortArray(bufferSize)
                while (isRecording) {
                    val read = audioRecord?.read(buffer, 0, bufferSize) ?: 0
                    if (read > 0) {
                        // Calculate amplitude
                        val amplitude = buffer.take(read).maxOrNull()?.toInt()?.let {
                            Math.abs(it)
                        } ?: 0
                        onAmplitudeUpdate?.invoke(amplitude)

                        // Write PCM bytes
                        val bytes = ByteArray(read * 2)
                        for (i in 0 until read) {
                            bytes[i * 2] = (buffer[i].toInt() and 0xFF).toByte()
                            bytes[i * 2 + 1] = (buffer[i].toInt() shr 8).toByte()
                        }
                        fos.write(bytes)
                    }
                }
            }
        }

    fun stopRecording() {
        isRecording = false
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
    }

    fun release() {
        stopRecording()
    }
}
