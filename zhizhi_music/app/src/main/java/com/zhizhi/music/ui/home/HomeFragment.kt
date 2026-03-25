package com.zhizhi.music.ui.home

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.zhizhi.music.R
import com.zhizhi.music.databinding.FragmentHomeBinding
import com.zhizhi.music.util.PreferencesManager
import com.zhizhi.music.util.TtsManager

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HomeViewModel by viewModels()
    private lateinit var tts: TtsManager

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tts = TtsManager(requireContext())
        setupGlobalControls()
        setupObservers()
        setupQuickButtons()
        setupDailyPlan()
    }

    private fun setupGlobalControls() {
        binding.switchEyeCare.isChecked = PreferencesManager.isEyeCareMode()
        binding.switchChildLock.isChecked = PreferencesManager.isChildLock()
        binding.switchBgMusic.isChecked = PreferencesManager.isBgMusic()
        binding.switchVoiceRead.isChecked = PreferencesManager.isVoiceRead()

        binding.switchEyeCare.setOnCheckedChangeListener { _, checked ->
            PreferencesManager.setEyeCareMode(checked)
            applyEyeCareMode(checked)
        }
        binding.switchChildLock.setOnCheckedChangeListener { _, checked ->
            PreferencesManager.setChildLock(checked)
        }
        binding.switchBgMusic.setOnCheckedChangeListener { _, checked ->
            PreferencesManager.setBgMusic(checked)
        }
        binding.switchVoiceRead.setOnCheckedChangeListener { _, checked ->
            PreferencesManager.setVoiceRead(checked)
            if (checked) tts.speak("语音朗读已开启")
        }

        binding.avatarCard.setOnClickListener {
            showProfileDialog()
        }
    }

    private fun applyEyeCareMode(enabled: Boolean) {
        val bgColor = if (enabled)
            requireContext().getColor(R.color.eye_care_background)
        else
            requireContext().getColor(R.color.md_theme_background)
        binding.root.setBackgroundColor(bgColor)
    }

    private fun setupObservers() {
        viewModel.userProgress.observe(viewLifecycleOwner) { progress ->
            progress ?: return@observe
            binding.tvConsecutiveDays.text = "${progress.consecutiveDays}天"
            binding.tvTotalSessions.text = "${progress.totalSessions}次"
            val maxStage = 10
            val currentStage = (progress.currentLevel - 1) * 3 + progress.currentChapter
            binding.progressBarStage.max = maxStage
            binding.progressBarStage.progress = currentStage
            binding.tvStageLabel.text = "第${currentStage}关 / 共${maxStage}关"
        }

        viewModel.todaySeconds.observe(viewLifecycleOwner) { secs ->
            binding.tvTodayTime.text = viewModel.formatSeconds(secs)
        }

        viewModel.weekSeconds.observe(viewLifecycleOwner) { secs ->
            binding.tvWeekTime.text = viewModel.formatSeconds(secs)
        }

        viewModel.dailyPlan.observe(viewLifecycleOwner) { plan ->
            binding.tvDailyPlan.text = plan
            if (PreferencesManager.isVoiceRead()) {
                tts.speak("今日练习计划：$plan")
            }
        }

        viewModel.checkInDone.observe(viewLifecycleOwner) { done ->
            binding.btnCheckIn.isEnabled = !done
            binding.btnCheckIn.text = if (done) "今日已打卡 ✓" else "立即打卡"
        }
    }

    private fun setupQuickButtons() {
        binding.btnUkulele.setOnClickListener {
            tts.speak("进入尤克里里助手")
            findNavController().navigate(R.id.nav_ukulele)
        }
        binding.btnSinging.setOnClickListener {
            tts.speak("进入唱歌助手")
            findNavController().navigate(R.id.nav_singing)
        }
        binding.btnLibrary.setOnClickListener {
            tts.speak("进入曲库中心")
            findNavController().navigate(R.id.nav_library)
        }
        binding.btnKnowledge.setOnClickListener {
            tts.speak("进入基础知识")
            findNavController().navigate(R.id.nav_knowledge)
        }
        binding.btnCheckIn.setOnClickListener {
            viewModel.doCheckIn()
            tts.speak("打卡成功！坚持每天练习，你会越来越棒！")
            Snackbar.make(binding.root, "今日打卡成功！继续保持！", Snackbar.LENGTH_SHORT).show()
        }
    }

    private fun setupDailyPlan() {
        binding.btnReadPlan.setOnClickListener {
            val plan = binding.tvDailyPlan.text.toString()
            tts.speak(plan)
        }
        binding.cardDailyPlan.setOnClickListener {
            // Navigate to corresponding practice
            findNavController().navigate(R.id.nav_ukulele)
        }
    }

    private fun showProfileDialog() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("个人中心")
            .setItems(arrayOf("练琴统计与周报", "成长勋章", "历史录音对比", "关于知知小音乐")) { _, which ->
                when (which) {
                    0 -> showWeeklyReport()
                    1 -> showBadges()
                    2 -> showRecordingHistory()
                    3 -> showAbout()
                }
            }
            .show()
    }

    private fun showWeeklyReport() {
        viewModel.userProgress.value?.let { progress ->
            val weekSecs = viewModel.weekSeconds.value ?: 0
            MaterialAlertDialogBuilder(requireContext())
                .setTitle("本周练琴报告")
                .setMessage(
                    "本周总练琴时间：${viewModel.formatSeconds(weekSecs)}\n" +
                    "累计打卡：${progress.consecutiveDays} 天\n" +
                    "总练习次数：${progress.totalSessions} 次\n\n" +
                    "加油！坚持每天练习，音乐会越来越好听！"
                )
                .setPositiveButton("好的", null)
                .show()
        }
    }

    private fun showBadges() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("成长勋章")
            .setMessage("🌟 入门勋章 - 完成第一首曲目\n🎵 旋律勋章 - 连续练习7天\n🏆 大师勋章 - 完成进阶曲目")
            .setPositiveButton("太棒了！", null)
            .show()
    }

    private fun showRecordingHistory() {
        Snackbar.make(binding.root, "历史录音功能，在尤克里里助手页面录音后可查看", Snackbar.LENGTH_LONG).show()
    }

    private fun showAbout() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("关于知知小音乐")
            .setMessage("版本：1.0.0\n\n知知小音乐是专为儿童设计的尤克里里+唱歌全能训练助手。\n\n完全离线运行，无广告，无内购。\n\n祝小朋友学习愉快，越弹越棒！")
            .setPositiveButton("好的", null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        tts.shutdown()
        _binding = null
    }
}
