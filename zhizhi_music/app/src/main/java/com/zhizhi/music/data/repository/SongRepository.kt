package com.zhizhi.music.data.repository

import androidx.lifecycle.LiveData
import com.zhizhi.music.data.database.AppDatabase
import com.zhizhi.music.data.model.Song

class SongRepository(private val db: AppDatabase) {

    private val dao = db.songDao()

    fun getAllSongs(): LiveData<List<Song>> = dao.getAllSongs()

    fun getSongsByLevel(level: Int): LiveData<List<Song>> = dao.getSongsByLevel(level)

    fun searchSongs(query: String): LiveData<List<Song>> = dao.searchSongs(query)

    suspend fun getSongById(id: Int): Song? = dao.getSongById(id)

    suspend fun setFavorite(id: Int, fav: Boolean) = dao.setFavorite(id, fav)

    suspend fun unlockSong(id: Int) = dao.unlockSong(id, true)

    suspend fun updatePlayStats(id: Int, score: Float) = dao.updatePlayStats(id, score)
}
