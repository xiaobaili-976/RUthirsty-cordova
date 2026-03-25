package com.zhizhi.music.ui.knowledge

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SearchView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.chip.Chip
import com.zhizhi.music.databinding.FragmentKnowledgeBinding
import com.zhizhi.music.util.TtsManager

class KnowledgeFragment : Fragment() {

    private var _binding: FragmentKnowledgeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: KnowledgeViewModel by viewModels()
    private lateinit var tts: TtsManager
    private lateinit var adapter: KnowledgeAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentKnowledgeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tts = TtsManager(requireContext())

        setupRecyclerView()
        setupCategoryChips()
        setupSearch()
        setupObservers()
        tts.speak("欢迎来到基础知识，这里有尤克里里学习的所有知识，点击喇叭按钮可以听老师讲解。")
    }

    private fun setupRecyclerView() {
        adapter = KnowledgeAdapter(
            onItemClick = { item ->
                tts.speak(item.ttsText)
            },
            onReadClick = { item ->
                tts.speak(item.ttsText)
            }
        )
        binding.rvKnowledge.layoutManager = LinearLayoutManager(requireContext())
        binding.rvKnowledge.adapter = adapter
    }

    private fun setupCategoryChips() {
        val categories = listOf("入门刚需", "进阶提升", "趣味激励")
        categories.forEach { cat ->
            val chip = Chip(requireContext()).apply {
                text = cat
                isCheckable = true
                isChecked = cat == "入门刚需"
                setOnClickListener { viewModel.filterByCategory(cat) }
            }
            binding.chipGroupCategory.addView(chip)
        }
    }

    private fun setupSearch() {
        binding.searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                viewModel.search(query ?: "")
                return true
            }
            override fun onQueryTextChange(newText: String?): Boolean {
                viewModel.search(newText ?: "")
                return true
            }
        })
    }

    private fun setupObservers() {
        viewModel.items.observe(viewLifecycleOwner) { items ->
            adapter.submitList(items)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        tts.shutdown()
        _binding = null
    }
}
