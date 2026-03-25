package com.zhizhi.music.ui.library

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SearchView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.chip.Chip
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.zhizhi.music.R
import com.zhizhi.music.data.model.Song
import com.zhizhi.music.databinding.FragmentLibraryBinding
import com.zhizhi.music.util.PdfExporter
import com.zhizhi.music.util.ShareUtils
import com.zhizhi.music.util.TtsManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class LibraryFragment : Fragment() {

    private var _binding: FragmentLibraryBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LibraryViewModel by viewModels()
    private lateinit var tts: TtsManager
    private lateinit var adapter: SongAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLibraryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tts = TtsManager(requireContext())
        setupRecyclerView()
        setupLevelChips()
        setupSearch()
        setupObservers()
        tts.speak("欢迎来到曲库中心，这里有一百二十首精选曲目，从入门到进阶，一步一步学！")
    }

    private fun setupRecyclerView() {
        adapter = SongAdapter(
            onPlayClick = { song -> playSongDemo(song) },
            onPracticeClick = { song -> startPractice(song) },
            onExportClick = { song -> exportSongPdf(song) },
            onFavoriteClick = { song -> viewModel.toggleFavorite(song) }
        )
        binding.rvSongs.layoutManager = LinearLayoutManager(requireContext())
        binding.rvSongs.adapter = adapter
    }

    private fun setupLevelChips() {
        val levels = listOf(Pair(0, "全部"), Pair(1, "入门(40首)"), Pair(2, "中等(50首)"), Pair(3, "进阶(30首)"))
        levels.forEach { (level, label) ->
            val chip = Chip(requireContext()).apply {
                text = label
                isCheckable = true
                isChecked = level == 0
                setOnClickListener { viewModel.setLevel(level) }
            }
            binding.chipGroupLevel.addView(chip)
        }
    }

    private fun setupSearch() {
        binding.searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(q: String?) = true.also { viewModel.search(q ?: "") }
            override fun onQueryTextChange(q: String?) = true.also { viewModel.search(q ?: "") }
        })
    }

    private fun setupObservers() {
        viewModel.songs.observe(viewLifecycleOwner) { songs ->
            adapter.submitList(songs)
            binding.tvSongCount.text = "共 ${songs.size} 首"
        }
    }

    private fun playSongDemo(song: Song) {
        tts.speak("正在播放《${song.title}》示范音频。${song.voiceTipsText}")
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("《${song.title}》")
            .setMessage(
                "难度：${"★".repeat(song.difficulty)}\n" +
                "和弦：${song.chords}\n" +
                "速度：${song.bpm} BPM\n\n" +
                "弹奏要点：\n${song.voiceTipsText}"
            )
            .setPositiveButton("开始练习") { _, _ -> startPractice(song) }
            .setNegativeButton("导出曲谱") { _, _ -> exportSongPdf(song) }
            .setNeutralButton("关闭", null)
            .show()
    }

    private fun startPractice(song: Song) {
        viewModel.selectSong(song)
        tts.speak("开始练习《${song.title}》！${song.voiceTipsText}。准备好了就进入尤克里里助手页面开始录音。")
        MaterialAlertDialogBuilder(requireContext())
            .setTitle("练习《${song.title}》")
            .setMessage(
                "弹奏要点：${song.voiceTipsText}\n\n" +
                "速度建议：慢速 ${(song.bpm * 0.7).toInt()} BPM → 标准 ${song.bpm} BPM\n" +
                "和弦：${song.chords}"
            )
            .setPositiveButton("去尤克里里助手练习") { _, _ ->
                requireActivity().let { act ->
                    if (act is com.zhizhi.music.MainActivity) {
                        act.supportFragmentManager.let {
                            androidx.navigation.Navigation.findNavController(
                                act, R.id.nav_host_fragment
                            ).navigate(R.id.nav_ukulele)
                        }
                    }
                }
            }
            .setNegativeButton("取消", null)
            .show()
    }

    private fun exportSongPdf(song: Song) {
        tts.speak("正在生成《${song.title}》曲谱，请稍等。")
        CoroutineScope(Dispatchers.Main).launch {
            PdfExporter.exportSheetMusic(requireContext(), song) { file ->
                if (file != null) {
                    tts.speak("曲谱生成成功！可以保存或者打印出来练习。")
                    ShareUtils.shareFile(requireContext(), file)
                } else {
                    tts.speak("曲谱生成失败，请再试一次。")
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        tts.shutdown()
        _binding = null
    }
}
