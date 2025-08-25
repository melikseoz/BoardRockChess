package com.boardrockchess

import kotlin.random.Random
import kotlin.math.max
import kotlin.math.abs

/**
 * Core game state and logic translated from the Python implementation.
 * Rendering and event handling are intentionally left as stubs; this file focuses on game mechanics.
 */
class Game(val cfg: Config = Config.load()) {
    var human: HumanPlayer? = null
    var hunter: HunterCPU? = null
    var target: TargetCPU? = null

    var turnOrder: MutableList<Actor> = mutableListOf()
    var turnIdx: Int = 0
    var winner: String? = null
    var stepCounter: Int = 0

    var obstaclesEnabled: Boolean = cfg.obstaclesEnabledDefault
    var obstacles: MutableSet<Vec> = mutableSetOf()
    var obstaclesStyles: MutableMap<Vec, String> = mutableMapOf()
    var fire: FireSystem? = null
    val powerups: MutableList<PowerUp> = mutableListOf()

    fun initWorld() {
        val (hp, hp2, tp) = pickStartPositions(cfg.gridW, cfg.gridH, cfg.minStartDist)
        human = HumanPlayer("HUMAN", cfg.colors["human"]!!, hp)
        hunter = HunterCPU("HUNTER", cfg.colors["hunter"]!!, hp2)
        target = TargetCPU("TARGET", cfg.colors["target"]!!, tp)
        if (obstaclesEnabled) {
            val excl = setOf(hp, hp2, tp)
            val (obs, styles) = generateObstacles(cfg.gridW, cfg.gridH, cfg.obstacleDensity, excl, cfg.treeRatio)
            obstacles = obs.toMutableSet()
            obstaclesStyles = styles.toMutableMap()
        } else {
            obstacles.clear(); obstaclesStyles.clear()
        }
        fire = FireSystem(cfg, cfg.gridW, cfg.gridH)
        fire?.clear()
        powerups.clear()
        turnOrder = mutableListOf(human!!, hunter!!, human!!, hunter!!, target!!)
        turnIdx = 0
        winner = null
        stepCounter = 0
    }

    fun inBounds(p: Vec) = p.first in 0 until cfg.gridW && p.second in 0 until cfg.gridH

    fun killActor(actor: Actor) {
        if (actor.dead) return
        actor.deaths += 1
        actor.dead = true
        actor.respawnTicks = cfg.respawnDelay
        actor.lastDeathPos = actor.pos
    }

    private fun findSafeSpawn(around: Vec): Vec {
        val livePositions = mutableSetOf<Vec>()
        listOf(human, hunter, target).forEach { a ->
            if (a != null && a.alive) livePositions.add(a.pos)
        }
        for (r in 0 until max(cfg.gridW, cfg.gridH)) {
            for (dx in -r..r) {
                for (dy in -r..r) {
                    if (max(abs(dx), abs(dy)) != r) continue
                    val q = vec(around.first + dx, around.second + dy)
                    if (!inBounds(q)) continue
                    if (obstaclesEnabled && q in obstacles) continue
                    if (fire?.cellInFire(q) == true) continue
                    if (q in livePositions) continue
                    return q
                }
            }
        }
        return vec(cfg.gridW/2, cfg.gridH/2)
    }

    private fun decrementRespawns() {
        listOf(human, hunter, target).forEach { a ->
            if (a != null && a.dead && a.respawnTicks > 0) {
                a.respawnTicks -= 1
                if (a.respawnTicks <= 0) {
                    val where = a.lastDeathPos ?: a.pos
                    a.setPosition(findSafeSpawn(where))
                    a.dead = false
                    a.respawnTicks = 0
                }
            }
        }
    }

    private fun checkFireKills() {
        val f = fire ?: return
        listOf(human, hunter, target).forEach { a ->
            if (a != null && a.alive && f.cellInFire(a.pos)) killActor(a)
        }
    }

    private fun maybeSpawnPowerup() {
        if (powerups.size >= cfg.powerupMax) return
        if (Random.nextDouble() >= cfg.powerupSpawnChance) return
        val occupied = mutableSetOf<Vec>()
        listOf(human, hunter, target).forEach { a -> if (a != null) occupied.add(a.pos) }
        if (obstaclesEnabled) occupied.addAll(obstacles)
        occupied.addAll(powerups.map { it.pos })
        repeat(20) {
            val pos = vec(Random.nextInt(cfg.gridW), Random.nextInt(cfg.gridH))
            if (pos in occupied) return@repeat
            if (fire?.cellInFire(pos) == true) return@repeat
            val cls = if (Random.nextBoolean()) SpeedPowerUp::class else TimeStopPowerUp::class
            val pu = when (cls) {
                SpeedPowerUp::class -> SpeedPowerUp(pos)
                else -> TimeStopPowerUp(pos)
            }
            powerups.add(pu); return
        }
    }

    fun postStep() {
        fire?.update(stepCounter)
        fire?.maybeSpawn(stepCounter, obstacles, obstaclesStyles)
        checkFireKills()
        maybeSpawnPowerup()
        decrementRespawns()
    }
}

