package com.zhizhi.music.audio

import android.content.Context
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class AudioPlayer(context: Context) {

    private val player = ExoPlayer.Builder(context).build()

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying

    private val _position = MutableStateFlow(0L)
    val position: StateFlow<Long> = _position

    private val _duration = MutableStateFlow(0L)
    val duration: StateFlow<Long> = _duration

    init {
        player.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(playing: Boolean) {
                _isPlaying.value = playing
            }
            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) {
                    _isPlaying.value = false
                }
                _duration.value = player.duration.coerceAtLeast(0)
            }
        })
    }

    fun playFromAsset(context: Context, assetFileName: String) {
        try {
            val uri = Uri.parse("asset:///$assetFileName")
            playUri(uri)
        } catch (e: Exception) {
            // Asset not found, ignore
        }
    }

    fun playFromFile(path: String) {
        playUri(Uri.parse(path))
    }

    fun playUri(uri: Uri) {
        player.setMediaItem(MediaItem.fromUri(uri))
        player.prepare()
        player.play()
    }

    fun playPause() {
        if (player.isPlaying) player.pause() else player.play()
    }

    fun pause() { player.pause() }

    fun stop() {
        player.stop()
        player.clearMediaItems()
    }

    fun seekTo(posMs: Long) { player.seekTo(posMs) }

    fun setPlaybackSpeed(speed: Float) {
        player.setPlaybackSpeed(speed)
    }

    fun getCurrentPosition(): Long = player.currentPosition

    fun getDuration(): Long = player.duration

    fun release() {
        player.release()
    }
}
