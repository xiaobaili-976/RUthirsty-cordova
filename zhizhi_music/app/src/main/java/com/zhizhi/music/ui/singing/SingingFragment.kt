package com.zhizhi.music.ui.singing

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.zhizhi.music.R
import com.zhizhi.music.databinding.FragmentSingingBinding
import com.zhizhi.music.util.ShareUtils
import com.zhizhi.music.util.TtsManager
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class SingingFragment : Fragment() {

    private var _binding: FragmentSingingBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SingingViewModel by viewModels()
    private lateinit var tts: TtsManager

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSingingBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tts = TtsManager(requireContext())
        setupSingButton()
        setupObservers()
        setupSolfege()
        setupActionButtons()
        tts.speak("唱歌助手已准备好！点击开始唱歌，我会实时显示你的音高，并给你打分。")
    }

    private fun setupSingButton() {
        binding.btnStartSinging.setOnClickListener {
            if (viewModel.isRecording.value == true) {
                viewModel.stopAndScore()
                tts.speak("唱歌停止，正在分析，请稍等。")
            } else {
                if (checkPermission()) {
                    viewModel.startSinging(requireContext().cacheDir)
                    tts.speak("开始录音！请唱你最喜欢的歌，唱完后点击停止。")
                } else {
                    requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), 1001)
                }
            }
        }

        binding.btnHumDetect.setOnClickListener {
            if (checkPermission()) {
                tts.speak("请哼唱一段旋律，我来帮你识别是哪首歌，哼唱十秒钟。")
                viewModel.humAndDetect(requireContext().cacheDir)
            }
        }
    }

    private fun setupObservers() {
        viewModel.isRecording.observe(viewLifecycleOwner) { recording ->
            binding.btnStartSinging.text = if (recording) "停止唱歌" else "开始唱歌"
            binding.btnStartSinging.setIconResource(
                if (recording) R.drawable.ic_stop else R.drawable.ic_mic
            )
            binding.pitchLineView.visibility = if (recording) View.VISIBLE else View.GONE
        }

        viewModel.recordingSeconds.observe(viewLifecycleOwner) { secs ->
            binding.tvRecordTime.text = String.format("%02d:%02d", secs / 60, secs % 60)
        }

        viewModel.currentNote.observe(viewLifecycleOwner) { note ->
            binding.tvCurrentNote.text = note
        }

        viewModel.currentPitchHz.observe(viewLifecycleOwner) { hz ->
            if (hz > 0) {
                binding.tvCurrentHz.text = String.format("%.1f Hz", hz)
                // Update pitch line (simplified)
                val normalizedPitch = ((hz - 100f) / (1000f - 100f)).coerceIn(0f, 1f)
                binding.pitchIndicator.translationY = binding.pitchLineView.height * (1f - normalizedPitch)
            }
        }

        viewModel.isAnalyzing.observe(viewLifecycleOwner) { analyzing ->
            binding.progressAnalyzing.visibility = if (analyzing) View.VISIBLE else View.GONE
        }

        viewModel.singingResult.observe(viewLifecycleOwner) { result ->
            result ?: return@observe
            showSingingResult(result)
        }
    }

    private fun showSingingResult(result: com.zhizhi.music.ai.AudioProcessor.AnalysisResult) {
        binding.cardResult.visibility = View.VISIBLE
        binding.tvPitchScore.text = "${result.pitchScore.toInt()}分"
        binding.tvRhythmScore.text = "${result.rhythmScore.toInt()}分"
        binding.tvCompleteScore.text = "${result.chordScore.toInt()}分"
        binding.tvOverallScore.text = "${result.overallScore.toInt()}"

        val scoreColor = when {
            result.overallScore >= 90 -> requireContext().getColor(R.color.score_excellent)
            result.overallScore >= 75 -> requireContext().getColor(R.color.score_good)
            result.overallScore >= 60 -> requireContext().getColor(R.color.score_average)
            else -> requireContext().getColor(R.color.score_poor)
        }
        binding.tvOverallScore.setTextColor(scoreColor)

        binding.tvFeedback.text = result.feedbackText
        binding.btnReadFeedback.setOnClickListener { tts.speak(result.feedbackText) }

        tts.speak("唱歌评分完成！综合得分${result.overallScore.toInt()}分。${result.feedbackText}")

        binding.btnShareScore.visibility = View.VISIBLE
    }

    private fun setupSolfege() {
        val noteButtons = listOf(
            binding.btnDo, binding.btnRe, binding.btnMi,
            binding.btnFa, binding.btnSol, binding.btnLa, binding.btnSi
        )
        val noteNames = listOf("哆", "来", "咪", "发", "嗦", "啦", "西")
        noteButtons.forEachIndexed { index, btn ->
            btn.setOnClickListener {
                viewModel.playStandardNote(index)
                tts.speak("标准音：${noteNames[index]}")
            }
        }
    }

    private fun setupActionButtons() {
        binding.btnBreathPractice.setOnClickListener {
            showBreathingExercise()
        }

        binding.btnShareScore.setOnClickListener {
            val result = viewModel.singingResult.value ?: return@setOnClickListener
            val posterFile = ShareUtils.generateScorePoster(
                requireContext(), "唱歌练习",
                result.pitchScore, result.chordScore, result.rhythmScore, result.overallScore,
                SimpleDateFormat("yyyy年MM月dd日", Locale.CHINESE).format(Date())
            )
            posterFile?.let { ShareUtils.shareScorePoster(requireContext(), it) }
        }
    }

    private fun showBreathingExercise() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("气息练习")
            .setMessage(
                "气息练习步骤：\n\n" +
                "1. 鼻子慢慢吸气4拍，感觉肚子鼓起来\n" +
                "2. 屏住呼吸2拍\n" +
                "3. 嘴巴慢慢呼气8拍，发\"嘶\"声\n" +
                "4. 重复5遍\n\n" +
                "记住：唱歌要用腹式呼吸，肚子起伏，肩膀不要动。"
            )
            .setPositiveButton("开始练习") { _, _ ->
                tts.speak("气息练习开始。用鼻子慢慢吸气，数一二三四。屏住呼吸，一二。用嘴慢慢呼气，发嘶声，一二三四五六七八。")
            }
            .setNegativeButton("取消", null)
            .show()
    }

    private fun checkPermission() = ContextCompat.checkSelfPermission(
        requireContext(), Manifest.permission.RECORD_AUDIO
    ) == PackageManager.PERMISSION_GRANTED

    override fun onDestroyView() {
        super.onDestroyView()
        tts.shutdown()
        _binding = null
    }
}
