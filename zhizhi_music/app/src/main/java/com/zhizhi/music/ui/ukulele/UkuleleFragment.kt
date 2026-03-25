package com.zhizhi.music.ui.ukulele

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.animation.AnimationUtils
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.zhizhi.music.R
import com.zhizhi.music.databinding.FragmentUkuleleBinding
import com.zhizhi.music.util.PdfExporter
import com.zhizhi.music.util.ShareUtils
import com.zhizhi.music.util.TtsManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class UkuleleFragment : Fragment() {

    private var _binding: FragmentUkuleleBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UkuleleViewModel by viewModels()
    private lateinit var tts: TtsManager

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentUkuleleBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tts = TtsManager(requireContext())
        setupRecordingUI()
        setupMetronomeUI()
        setupObservers()
        setupActionButtons()
        tts.speak("尤克里里助手已准备好，点击录音按钮开始录音，我会帮你分析弹奏并打分。")
    }

    private fun setupRecordingUI() {
        binding.btnRecord.setOnClickListener {
            if (viewModel.isRecording.value == true) {
                viewModel.stopRecordingAndAnalyze()
                tts.speak("录音已停止，正在分析，请稍等几秒钟。")
            } else {
                if (checkAudioPermission()) {
                    val dir = requireContext().cacheDir
                    viewModel.startRecording(dir)
                    tts.speak("开始录音了！请弹奏你的曲目，弹完后再点击停止按钮。")
                } else {
                    requestAudioPermission()
                }
            }
        }
    }

    private fun setupMetronomeUI() {
        binding.btnMetronome.setOnClickListener {
            viewModel.toggleMetronome()
        }
        binding.btnBpmPlus.setOnClickListener { viewModel.increaseBpm() }
        binding.btnBpmMinus.setOnClickListener { viewModel.decreaseBpm() }
    }

    private fun setupObservers() {
        viewModel.isRecording.observe(viewLifecycleOwner) { recording ->
            if (recording) {
                binding.btnRecord.text = "停止录音"
                binding.btnRecord.setIconResource(R.drawable.ic_stop)
                binding.waveformView.visibility = View.VISIBLE
                binding.tvRecordHint.text = "录音中...请弹奏"
            } else {
                binding.btnRecord.text = "开始录音"
                binding.btnRecord.setIconResource(R.drawable.ic_mic)
                binding.tvRecordHint.text = "点击录音开始分析"
            }
        }

        viewModel.recordingSeconds.observe(viewLifecycleOwner) { secs ->
            binding.tvRecordTime.text = String.format("%02d:%02d", secs / 60, secs % 60)
        }

        viewModel.amplitude.observe(viewLifecycleOwner) { amp ->
            binding.progressAmplitude.progress = (amp / 328).coerceIn(0, 100)
        }

        viewModel.isAnalyzing.observe(viewLifecycleOwner) { analyzing ->
            binding.progressAnalyzing.visibility = if (analyzing) View.VISIBLE else View.GONE
            binding.tvAnalyzingHint.visibility = if (analyzing) View.VISIBLE else View.GONE
            if (analyzing) {
                tts.speak("正在分析中，请稍等。")
            }
        }

        viewModel.result.observe(viewLifecycleOwner) { result ->
            result ?: return@observe
            showResult(result)
        }

        viewModel.bpm.observe(viewLifecycleOwner) { bpm ->
            binding.tvBpm.text = "$bpm BPM"
        }

        viewModel.metronomeOn.observe(viewLifecycleOwner) { on ->
            binding.btnMetronome.text = if (on) "关闭节拍器" else "开启节拍器"
        }

        viewModel.metronomeTick.observe(viewLifecycleOwner) { tick ->
            if (tick) {
                binding.viewMetronomeFlash.visibility = View.VISIBLE
                val anim = AnimationUtils.loadAnimation(requireContext(), R.anim.metronome_flash)
                binding.viewMetronomeFlash.startAnimation(anim)
            } else {
                binding.viewMetronomeFlash.visibility = View.INVISIBLE
            }
        }
    }

    private fun showResult(result: com.zhizhi.music.ai.AudioProcessor.AnalysisResult) {
        binding.cardResult.visibility = View.VISIBLE

        // Scores
        binding.tvPitchScore.text = "${result.pitchScore.toInt()}分"
        binding.tvChordScore.text = "${result.chordScore.toInt()}分"
        binding.tvRhythmScore.text = "${result.rhythmScore.toInt()}分"
        binding.tvOverallScore.text = "${result.overallScore.toInt()}"

        // Color feedback
        val scoreColor = when {
            result.overallScore >= 90 -> requireContext().getColor(R.color.score_excellent)
            result.overallScore >= 75 -> requireContext().getColor(R.color.score_good)
            result.overallScore >= 60 -> requireContext().getColor(R.color.score_average)
            else -> requireContext().getColor(R.color.score_poor)
        }
        binding.tvOverallScore.setTextColor(scoreColor)

        // Feedback
        binding.tvFeedback.text = result.feedbackText
        binding.btnReadFeedback.setOnClickListener { tts.speak(result.feedbackText) }

        // Auto-read feedback
        tts.speak("评分完成！综合得分${result.overallScore.toInt()}分。${result.feedbackText}")

        // Warnings
        if (result.hasMuffledSound) {
            binding.chipMuffled.visibility = View.VISIBLE
        }
        if (result.hasWeakPressing) {
            binding.chipWeak.visibility = View.VISIBLE
        }
        if (result.hasChordSwitchDelay) {
            binding.chipSwitchDelay.visibility = View.VISIBLE
        }

        // Chord display
        if (result.detectedChords.isNotEmpty()) {
            binding.tvDetectedChords.text = "识别到的和弦：${result.detectedChords.joinToString(" → ")}"
        }
    }

    private fun setupActionButtons() {
        binding.btnExportPdf.setOnClickListener {
            tts.speak("正在生成曲谱，请稍等。")
            // Export PDF for a placeholder song
            val song = com.zhizhi.music.data.SongData.getAllSongs().firstOrNull()
            song?.let { s ->
                CoroutineScope(Dispatchers.Main).launch {
                    PdfExporter.exportSheetMusic(requireContext(), s) { file ->
                        if (file != null) {
                            tts.speak("曲谱已生成，可以分享给老师或打印出来。")
                            ShareUtils.shareFile(requireContext(), file)
                        } else {
                            tts.speak("曲谱生成失败，请再试一次。")
                        }
                    }
                }
            }
        }

        binding.btnShareScore.setOnClickListener {
            val result = viewModel.result.value ?: run {
                Snackbar.make(binding.root, "请先录音评分", Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val posterFile = ShareUtils.generateScorePoster(
                requireContext(),
                "练习曲目",
                result.pitchScore,
                result.chordScore,
                result.rhythmScore,
                result.overallScore,
                java.text.SimpleDateFormat("yyyy年MM月dd日", java.util.Locale.CHINESE)
                    .format(java.util.Date())
            )
            posterFile?.let { ShareUtils.shareScorePoster(requireContext(), it) }
        }

        binding.btnShowChordTrainer.setOnClickListener {
            showChordTrainerDialog()
        }
    }

    private fun showChordTrainerDialog() {
        val chords = arrayOf("C和弦", "G和弦", "Am和弦", "F和弦", "Dm和弦", "Em和弦", "G7和弦")
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("和弦训练器")
            .setItems(chords) { _, which ->
                val chordTips = arrayOf(
                    "C和弦：无名指按第一弦第三品，其他空弦。",
                    "G和弦：食指第二弦第二品，中指第一弦第三品，无名指第三弦第二品。",
                    "Am和弦：中指第四弦第二品，无名指第三弦第二品。",
                    "F和弦：食指横按第一二弦第一品，中指第四弦第二品。",
                    "Dm和弦：食指第一弦第一品，中指第四弦第二品，无名指第三弦第二品。",
                    "Em和弦：食指第三弦第四品，中指第四弦第三品，无名指第二弦第三品。",
                    "G7和弦：食指第二弦第一品，中指第三弦第二品，无名指第一弦第二品。"
                )
                tts.speak(chordTips[which])
                Snackbar.make(binding.root, chordTips[which], Snackbar.LENGTH_LONG).show()
            }
            .show()
    }

    private fun checkAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            requireContext(), Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun requestAudioPermission() {
        requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), 1001)
        tts.speak("需要麦克风权限才能录音，请允许。")
    }

    override fun onDestroyView() {
        super.onDestroyView()
        tts.shutdown()
        _binding = null
    }
}
