package com.boardrockchess

/** Entry point placeholder. Interactive loop not implemented. */
fun main() {
    val game = Game()
    game.initWorld()
    println("Game initialized with human at ${'$'}{game.human?.pos}")
}

