package com.boardrockchess

// Simplified Power-up system translated from Python version.

import kotlin.math.max

open class PowerUp(var pos: Vec) {
    var active: Boolean = true
    open fun apply(actor: Actor, game: Game) { active = false }
    open fun draw(screen: Any?, cfg: Config) { /* drawing handled elsewhere */ }
}

class SpeedPowerUp(pos: Vec) : PowerUp(pos) {
    override fun apply(actor: Actor, game: Game) {
        super.apply(actor, game)
        actor.speedTurns = 2
    }
}

class TimeStopPowerUp(pos: Vec) : PowerUp(pos) {
    override fun apply(actor: Actor, game: Game) {
        super.apply(actor, game)
        when (actor) {
            game.human -> game.hunter?.let { it.skipTurns = max(it.skipTurns, 2) }
            game.hunter -> game.human?.let { it.skipTurns = max(it.skipTurns, 2) }
            else -> {
                game.human?.let { it.skipTurns = max(it.skipTurns, 2) }
                game.hunter?.let { it.skipTurns = max(it.skipTurns, 2) }
            }
        }
    }
}

