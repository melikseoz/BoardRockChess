package com.boardrockchess

import com.badlogic.gdx.backends.lwjgl3.Lwjgl3Application
import com.badlogic.gdx.backends.lwjgl3.Lwjgl3ApplicationConfiguration

/** Launches the libGDX UI for the Kotlin game. */
fun main() {
    val config = Lwjgl3ApplicationConfiguration().apply {
        setTitle("BoardRockChess")
        setWindowedMode(720, 720)
    }
    Lwjgl3Application(BoardRockApp(), config)
}
