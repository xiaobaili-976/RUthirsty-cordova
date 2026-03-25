package com.zhizhi.music.util

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.net.Uri
import android.view.View
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object ShareUtils {

    fun shareText(context: Context, text: String, title: String = "分享") {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, text)
            putExtra(Intent.EXTRA_TITLE, title)
        }
        context.startActivity(Intent.createChooser(intent, title))
    }

    fun shareFile(context: Context, file: File, mimeType: String = "application/pdf") {
        val uri = FileProvider.getUriForFile(
            context, "${context.packageName}.fileprovider", file
        )
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = mimeType
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享文件"))
    }

    fun generateScorePoster(
        context: Context,
        songTitle: String,
        pitchScore: Float,
        chordScore: Float,
        rhythmScore: Float,
        overallScore: Float,
        practiceDate: String
    ): File? {
        return try {
            val width = 900
            val height = 1200
            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bitmap)

            // Background gradient
            val bgPaint = Paint(Paint.ANTI_ALIAS_FLAG)
            bgPaint.color = Color.parseColor("#F0F8FF")
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), bgPaint)

            // Header decoration
            val headerPaint = Paint(Paint.ANTI_ALIAS_FLAG)
            headerPaint.color = Color.parseColor("#4FC3F7")
            canvas.drawRoundRect(RectF(0f, 0f, width.toFloat(), 220f), 0f, 0f, headerPaint)

            // Title
            val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 56f
                isFakeBoldText = true
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("知知小音乐", width / 2f, 90f, titlePaint)

            val subTitlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#E1F5FE")
                textSize = 36f
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("练习成绩单", width / 2f, 145f, subTitlePaint)
            canvas.drawText(practiceDate, width / 2f, 195f, subTitlePaint.apply { textSize = 28f })

            // Song name
            val songPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#1565C0")
                textSize = 48f
                isFakeBoldText = true
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("《$songTitle》", width / 2f, 310f, songPaint)

            // Score display
            val scoreCirclePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#4FC3F7")
                style = Paint.Style.FILL
            }
            canvas.drawCircle(width / 2f, 480f, 120f, scoreCirclePaint)

            val scorePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 80f
                isFakeBoldText = true
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("${overallScore.toInt()}", width / 2f, 510f, scorePaint)

            val scoreLabel = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 32f
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("综合得分", width / 2f, 555f, scoreLabel)

            // Three-dimension scores
            val dimY = 670f
            val dimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#37474F")
                textSize = 36f
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("音准 ${pitchScore.toInt()}分", width / 4f, dimY, dimPaint)
            canvas.drawText("和弦 ${chordScore.toInt()}分", width / 2f, dimY, dimPaint)
            canvas.drawText("节奏 ${rhythmScore.toInt()}分", 3 * width / 4f, dimY, dimPaint)

            // Divider
            val divPaint = Paint().apply {
                color = Color.parseColor("#B0BEC5")
                strokeWidth = 2f
            }
            canvas.drawLine(60f, 710f, (width - 60).toFloat(), 710f, divPaint)

            // Encouragement
            val encourageText = when {
                overallScore >= 90 -> "太棒了！你是小小尤克里里大师！"
                overallScore >= 75 -> "弹得很好！继续练习会更厉害！"
                overallScore >= 60 -> "不错哦！多练几次就完美了！"
                else -> "加油！每次练习都在进步！"
            }
            val encPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#1976D2")
                textSize = 40f
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText(encourageText, width / 2f, 790f, encPaint)

            // Footer
            val footPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.parseColor("#90A4AE")
                textSize = 28f
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("知知小音乐 · 儿童尤克里里+唱歌全能训练助手", width / 2f, 1150f, footPaint)

            // Save to file
            val posterDir = File(context.filesDir, "posters")
            posterDir.mkdirs()
            val sdf = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault())
            val posterFile = File(posterDir, "score_poster_${sdf.format(Date())}.png")
            FileOutputStream(posterFile).use { fos ->
                bitmap.compress(Bitmap.CompressFormat.PNG, 95, fos)
            }
            bitmap.recycle()
            posterFile
        } catch (e: Exception) {
            null
        }
    }

    fun shareScorePoster(context: Context, posterFile: File) {
        val uri = FileProvider.getUriForFile(
            context, "${context.packageName}.fileprovider", posterFile
        )
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "image/png"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TEXT, "我在知知小音乐练习了《》，快来一起学！")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享成绩"))
    }
}
