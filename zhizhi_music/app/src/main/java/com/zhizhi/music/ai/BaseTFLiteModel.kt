package com.zhizhi.music.ai

import android.content.Context
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

/**
 * Base class for TFLite model loading and inference.
 * Each model file should be placed in app/src/main/assets/models/
 */
abstract class BaseTFLiteModel(
    protected val context: Context,
    private val modelFileName: String
) {
    protected var interpreter: Interpreter? = null
    protected var isLoaded = false

    fun loadModel(): Boolean {
        return try {
            val model = loadModelFile(modelFileName)
            val options = Interpreter.Options().apply {
                setNumThreads(4)
                setUseNNAPI(false) // Offline, no NNAPI dependency
            }
            interpreter = Interpreter(model, options)
            isLoaded = true
            true
        } catch (e: Exception) {
            isLoaded = false
            false
        }
    }

    private fun loadModelFile(fileName: String): MappedByteBuffer {
        val assetManager = context.assets
        val fileDescriptor = assetManager.openFd("models/$fileName")
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }

    protected fun floatArrayToByteBuffer(floatArray: FloatArray): ByteBuffer {
        val byteBuffer = ByteBuffer.allocateDirect(floatArray.size * 4)
        byteBuffer.order(ByteOrder.nativeOrder())
        floatArray.forEach { byteBuffer.putFloat(it) }
        byteBuffer.rewind()
        return byteBuffer
    }

    open fun close() {
        interpreter?.close()
        interpreter = null
        isLoaded = false
    }
}
