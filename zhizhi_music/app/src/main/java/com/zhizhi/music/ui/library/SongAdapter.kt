package com.zhizhi.music.ui.library

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.zhizhi.music.R
import com.zhizhi.music.data.model.Song
import com.zhizhi.music.databinding.ItemSongBinding

class SongAdapter(
    private val onPlayClick: (Song) -> Unit,
    private val onPracticeClick: (Song) -> Unit,
    private val onExportClick: (Song) -> Unit,
    private val onFavoriteClick: (Song) -> Unit
) : ListAdapter<Song, SongAdapter.ViewHolder>(DIFF) {

    companion object {
        val DIFF = object : DiffUtil.ItemCallback<Song>() {
            override fun areItemsTheSame(a: Song, b: Song) = a.id == b.id
            override fun areContentsTheSame(a: Song, b: Song) = a == b
        }
    }

    inner class ViewHolder(private val binding: ItemSongBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(song: Song) {
            binding.tvTitle.text = song.title
            binding.tvLevel.text = song.levelName
            binding.tvChords.text = song.chords
            binding.tvBpm.text = "${song.bpm} BPM"
            binding.tvBestScore.text = if (song.bestScore > 0) "最高分：${song.bestScore.toInt()}" else "未练习"

            // Difficulty stars
            binding.ratingDifficulty.rating = song.difficulty.toFloat()

            // Lock indicator
            binding.ivLock.visibility = if (song.isUnlocked)
                ViewGroup.GONE else ViewGroup.VISIBLE
            binding.tvLocked.visibility = if (song.isUnlocked)
                ViewGroup.GONE else ViewGroup.VISIBLE

            // Favorite
            binding.btnFavorite.setIconResource(
                if (song.isFavorite) R.drawable.ic_favorite_filled else R.drawable.ic_favorite
            )

            binding.btnPlay.setOnClickListener { if (song.isUnlocked) onPlayClick(song) else showLockedMessage() }
            binding.btnPractice.setOnClickListener { if (song.isUnlocked) onPracticeClick(song) else showLockedMessage() }
            binding.btnExport.setOnClickListener { if (song.isUnlocked) onExportClick(song) else showLockedMessage() }
            binding.btnFavorite.setOnClickListener { onFavoriteClick(song) }

            // Level badge color
            val levelColor = when (song.level) {
                1 -> binding.root.context.getColor(R.color.level_entry)
                2 -> binding.root.context.getColor(R.color.level_medium)
                else -> binding.root.context.getColor(R.color.level_advanced)
            }
            binding.tvLevel.setTextColor(levelColor)
            binding.tvLevel.setBackgroundColor(levelColor and 0x33FFFFFF)
        }

        private fun showLockedMessage() {
            com.google.android.material.snackbar.Snackbar.make(
                binding.root, "完成前面的曲目才能解锁这首哦！继续加油！",
                com.google.android.material.snackbar.Snackbar.LENGTH_SHORT
            ).show()
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemSongBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
}
