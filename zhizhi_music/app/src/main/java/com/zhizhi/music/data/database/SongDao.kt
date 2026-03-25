package com.zhizhi.music.data.database

import androidx.lifecycle.LiveData
import androidx.room.*
import com.zhizhi.music.data.model.Song

@Dao
interface SongDao {

    @Query("SELECT COUNT(*) FROM songs")
    suspend fun getCount(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSong(song: Song)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(songs: List<Song>)

    @Query("SELECT * FROM songs ORDER BY level ASC, difficulty ASC")
    fun getAllSongs(): LiveData<List<Song>>

    @Query("SELECT * FROM songs WHERE level = :level ORDER BY difficulty ASC")
    fun getSongsByLevel(level: Int): LiveData<List<Song>>

    @Query("SELECT * FROM songs WHERE id = :id")
    suspend fun getSongById(id: Int): Song?

    @Query("SELECT * FROM songs WHERE title LIKE '%' || :query || '%'")
    fun searchSongs(query: String): LiveData<List<Song>>

    @Update
    suspend fun updateSong(song: Song)

    @Query("UPDATE songs SET isFavorite = :isFavorite WHERE id = :id")
    suspend fun setFavorite(id: Int, isFavorite: Boolean)

    @Query("UPDATE songs SET isUnlocked = :unlocked WHERE id = :id")
    suspend fun unlockSong(id: Int, unlocked: Boolean)

    @Query("UPDATE songs SET playCount = playCount + 1, bestScore = CASE WHEN :score > bestScore THEN :score ELSE bestScore END WHERE id = :id")
    suspend fun updatePlayStats(id: Int, score: Float)
}
