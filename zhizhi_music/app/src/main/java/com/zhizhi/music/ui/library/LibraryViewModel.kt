package com.zhizhi.music.ui.library

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.switchMap
import androidx.lifecycle.viewModelScope
import com.zhizhi.music.ZhizhiApp
import com.zhizhi.music.data.model.Song
import com.zhizhi.music.data.repository.SongRepository
import kotlinx.coroutines.launch

class LibraryViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = SongRepository(ZhizhiApp.getInstance().database)

    private val _selectedLevel = MutableLiveData(0) // 0=全部
    val selectedLevel: LiveData<Int> = _selectedLevel

    private val _searchQuery = MutableLiveData("")
    val searchQuery: LiveData<String> = _searchQuery

    val songs: LiveData<List<Song>> = _searchQuery.switchMap { query ->
        if (query.isEmpty()) {
            val level = _selectedLevel.value ?: 0
            if (level == 0) repo.getAllSongs() else repo.getSongsByLevel(level)
        } else {
            repo.searchSongs(query)
        }
    }

    private val _selectedSong = MutableLiveData<Song?>()
    val selectedSong: LiveData<Song?> = _selectedSong

    fun setLevel(level: Int) {
        _selectedLevel.value = level
        _searchQuery.value = "" // reset search
    }

    fun search(query: String) { _searchQuery.value = query }

    fun selectSong(song: Song) { _selectedSong.value = song }

    fun toggleFavorite(song: Song) {
        viewModelScope.launch {
            repo.setFavorite(song.id, !song.isFavorite)
        }
    }

    fun recordPlay(song: Song, score: Float) {
        viewModelScope.launch {
            repo.updatePlayStats(song.id, score)
        }
    }
}
