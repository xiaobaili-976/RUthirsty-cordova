package com.zhizhi.music.util

import android.content.Context
import com.itextpdf.text.BaseColor
import com.itextpdf.text.Document
import com.itextpdf.text.Element
import com.itextpdf.text.Font
import com.itextpdf.text.PageSize
import com.itextpdf.text.Paragraph
import com.itextpdf.text.Phrase
import com.itextpdf.text.Rectangle
import com.itextpdf.text.pdf.BaseFont
import com.itextpdf.text.pdf.PdfPCell
import com.itextpdf.text.pdf.PdfPTable
import com.itextpdf.text.pdf.PdfWriter
import com.zhizhi.music.data.model.Song
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object PdfExporter {

    suspend fun exportSheetMusic(
        context: Context,
        song: Song,
        onComplete: (File?) -> Unit
    ) = withContext(Dispatchers.IO) {
        try {
            val pdfDir = File(context.filesDir, "pdfs")
            pdfDir.mkdirs()
            val sdf = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault())
            val pdfFile = File(pdfDir, "${song.title}_曲谱_${sdf.format(Date())}.pdf")

            val document = Document(PageSize.A4, 36f, 36f, 54f, 54f)
            PdfWriter.getInstance(document, FileOutputStream(pdfFile))
            document.open()

            // Title
            val titleFont = Font(Font.FontFamily.HELVETICA, 22f, Font.BOLD, BaseColor(21, 101, 192))
            val title = Paragraph("《${song.title}》 曲谱\n", titleFont)
            title.alignment = Element.ALIGN_CENTER
            document.add(title)

            // Meta info
            val metaFont = Font(Font.FontFamily.HELVETICA, 11f, Font.NORMAL, BaseColor(84, 110, 122))
            val meta = Paragraph(
                "难度：${"★".repeat(song.difficulty)}${"☆".repeat(5 - song.difficulty)}   " +
                "级别：${song.levelName}   BPM：${song.bpm}   和弦：${song.chords}\n\n",
                metaFont
            )
            meta.alignment = Element.ALIGN_CENTER
            document.add(meta)

            // Separator
            val sepFont = Font(Font.FontFamily.HELVETICA, 10f, Font.NORMAL, BaseColor(176, 190, 197))
            document.add(Paragraph("─".repeat(70) + "\n", sepFont))

            // Sheet music placeholder (in real app, render actual notation)
            val sheetFont = Font(Font.FontFamily.COURIER, 14f, Font.BOLD, BaseColor(33, 33, 33))
            document.add(Paragraph("简 谱\n\n", Font(Font.FontFamily.HELVETICA, 14f, Font.BOLD, BaseColor(21, 101, 192))))

            val sheetTable = PdfPTable(8)
            sheetTable.widthPercentage = 100f
            val noteNames = listOf("1", "2", "3", "4", "5", "6", "7", "1·")
            noteNames.forEach { note ->
                val cell = PdfPCell(Phrase(note, sheetFont))
                cell.horizontalAlignment = Element.ALIGN_CENTER
                cell.verticalAlignment = Element.ALIGN_MIDDLE
                cell.minimumHeight = 40f
                cell.border = Rectangle.BOX
                cell.borderColor = BaseColor(224, 224, 224)
                cell.backgroundColor = BaseColor(240, 248, 255)
                sheetTable.addCell(cell)
            }
            document.add(sheetTable)

            document.add(Paragraph("\n"))
            document.add(Paragraph("和 弦 谱\n\n", Font(Font.FontFamily.HELVETICA, 14f, Font.BOLD, BaseColor(21, 101, 192))))

            // Chord table
            val chordList = song.chords.split(",")
            val chordTable = PdfPTable(chordList.size.coerceAtMost(6))
            chordTable.widthPercentage = 80f
            chordList.take(6).forEach { chord ->
                val cell = PdfPCell(Phrase(chord.trim(), Font(Font.FontFamily.HELVETICA, 16f, Font.BOLD, BaseColor(30, 136, 229))))
                cell.horizontalAlignment = Element.ALIGN_CENTER
                cell.verticalAlignment = Element.ALIGN_MIDDLE
                cell.minimumHeight = 60f
                cell.border = Rectangle.BOX
                cell.borderColor = BaseColor(79, 195, 247)
                cell.backgroundColor = BaseColor(225, 245, 254)
                chordTable.addCell(cell)
            }
            document.add(chordTable)

            document.add(Paragraph("\n"))
            document.add(Paragraph("─".repeat(70) + "\n", sepFont))

            // Voice tips
            document.add(Paragraph("语音弹奏要点\n\n", Font(Font.FontFamily.HELVETICA, 13f, Font.BOLD, BaseColor(198, 40, 40))))
            val tipsFont = Font(Font.FontFamily.HELVETICA, 12f, Font.NORMAL, BaseColor(55, 71, 79))
            document.add(Paragraph(song.voiceTipsText + "\n", tipsFont))

            // Footer
            document.add(Paragraph("\n\n"))
            document.add(Paragraph(
                "由 知知小音乐 自动生成 · ${SimpleDateFormat("yyyy年MM月dd日", Locale.CHINESE).format(Date())}",
                Font(Font.FontFamily.HELVETICA, 9f, Font.ITALIC, BaseColor(144, 164, 174))
            ))

            document.close()
            withContext(Dispatchers.Main) { onComplete(pdfFile) }
        } catch (e: Exception) {
            withContext(Dispatchers.Main) { onComplete(null) }
        }
    }
}
