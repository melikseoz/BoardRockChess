package com.boardrockchess

import kotlin.math.min

open class Actor(
    val name: String,
    val color: Color,
    var pos: Vec
) {
    var deaths: Int = 0
    var dead: Boolean = false
    var respawnTicks: Int = 0
    var lastDeathPos: Vec? = null
    var speedTurns: Int = 0
    var skipTurns: Int = 0

    val alive: Boolean
        get() = !dead

    fun setPosition(p: Vec) { pos = p }

    open fun move(p: Vec, game: Game) {
        pos = p
        val iter = game.powerups.iterator()
        while (iter.hasNext()) {
            val pu = iter.next()
            if (pu.active && pu.pos == pos) {
                pu.apply(this, game)
                if (!pu.active) iter.remove()
            }
        }
    }
}

class HumanPlayer(name: String, color: Color, pos: Vec) : Actor(name, color, pos) {
    /** Attempt move by delta vector; return true if move successful. */
    fun tryMove(delta: Vec?, w: Int, h: Int, obstacles: Set<Vec>, obstaclesEnabled: Boolean): Boolean {
        if (delta == null) return true
        val nxt = add(pos, delta)
        if (nxt.first in 0 until w && nxt.second in 0 until h && (!obstaclesEnabled || nxt !in obstacles)) {
            pos = nxt
            return true
        }
        return false
    }
}

class HunterCPU(name: String, color: Color, pos: Vec) : Actor(name, color, pos) {
    fun decide(target: Vec, w: Int, h: Int, obstacles: Set<Vec>, obstaclesEnabled: Boolean): Vec {
        val options = legalNeighbors(pos, w, h, obstacles, obstaclesEnabled).toMutableList()
        options.add(pos)
        var best = options[0]
        var bestDist = cheb(best, target)
        for (opt in options) {
            val d = cheb(opt, target)
            if (d < bestDist) { best = opt; bestDist = d }
        }
        return best
    }
}

class TargetCPU(name: String, color: Color, pos: Vec) : Actor(name, color, pos) {
    fun decide(human: Vec, hunter: Vec, w: Int, h: Int, obstacles: Set<Vec>, obstaclesEnabled: Boolean): Vec {
        val options = legalNeighbors(pos, w, h, obstacles, obstaclesEnabled)
        if (options.isEmpty()) return pos
        var bestScore = Int.MIN_VALUE
        val best = mutableListOf<Vec>()
        for (q in options) {
            val score = min(cheb(q, human), cheb(q, hunter))
            if (score > bestScore) {
                bestScore = score
                best.clear(); best.add(q)
            } else if (score == bestScore) {
                best.add(q)
            }
        }
        return best.first()
    }
}

