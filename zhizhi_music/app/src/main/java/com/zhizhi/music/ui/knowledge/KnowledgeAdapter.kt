package com.zhizhi.music.ui.knowledge

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.zhizhi.music.databinding.ItemKnowledgeBinding

class KnowledgeAdapter(
    private val onItemClick: (KnowledgeViewModel.KnowledgeItem) -> Unit,
    private val onReadClick: (KnowledgeViewModel.KnowledgeItem) -> Unit
) : ListAdapter<KnowledgeViewModel.KnowledgeItem, KnowledgeAdapter.ViewHolder>(DIFF_CALLBACK) {

    companion object {
        val DIFF_CALLBACK = object : DiffUtil.ItemCallback<KnowledgeViewModel.KnowledgeItem>() {
            override fun areItemsTheSame(
                a: KnowledgeViewModel.KnowledgeItem,
                b: KnowledgeViewModel.KnowledgeItem
            ) = a.id == b.id

            override fun areContentsTheSame(
                a: KnowledgeViewModel.KnowledgeItem,
                b: KnowledgeViewModel.KnowledgeItem
            ) = a == b
        }
    }

    inner class ViewHolder(private val binding: ItemKnowledgeBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: KnowledgeViewModel.KnowledgeItem) {
            binding.tvTitle.text = item.title
            binding.tvCategory.text = item.category
            binding.tvContent.text = item.content

            var expanded = false
            binding.root.setOnClickListener {
                expanded = !expanded
                binding.tvContent.visibility = if (expanded) ViewGroup.VISIBLE else ViewGroup.GONE
                binding.btnReadAloud.visibility = if (expanded) ViewGroup.VISIBLE else ViewGroup.GONE
                onItemClick(item)
            }
            binding.btnReadAloud.setOnClickListener { onReadClick(item) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemKnowledgeBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
}
