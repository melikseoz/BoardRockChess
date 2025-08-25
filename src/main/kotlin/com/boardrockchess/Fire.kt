package com.boardrockchess

import kotlin.random.Random

data class Fire(val topLeft: Vec, val cells: List<Vec>, val expiresAt: Int)

class FireSystem(private val cfg: Config, private val w: Int, private val h: Int) {
    val fires: MutableList<Fire> = mutableListOf()

    fun clear() = fires.clear()

    fun update(stepCounter: Int) {
        fires.removeIf { stepCounter >= it.expiresAt }
    }

    private fun rectCells(topLeft: Vec): List<Vec> {
        val (x,y) = topLeft
        return listOf(vec(x,y), vec(x+1,y), vec(x,y+1), vec(x+1,y+1))
    }

    fun cellInFire(p: Vec): Boolean = fires.any { p in it.cells }

    private fun canPlaceFire(topLeft: Vec, obstaclesStyles: Map<Vec,String>): Boolean {
        val (x,y) = topLeft
        if (x < 0 || y < 0 || x+1 >= w || y+1 >= h) return false
        val cells = rectCells(topLeft)
        // avoid overlap
        for (f in fires) if (cells.any { it in f.cells }) return false
        val treeCells = obstaclesStyles.filter { it.value == "tree" }.keys
        if (treeCells.isEmpty()) return false
        for (c in cells) if (treeCells.any { cheb(c, it) <= 8 }) return true
        return false
    }

    fun spawnAt(topLeft: Vec, stepCounter: Int, obstacles: MutableSet<Vec>, obstaclesStyles: MutableMap<Vec, String>): Boolean {
        if (!canPlaceFire(topLeft, obstaclesStyles)) return false
        val cells = rectCells(topLeft)
        for (c in cells) {
            if (c in obstacles && obstaclesStyles[c] == "tree") {
                obstacles.remove(c)
                obstaclesStyles.remove(c)
            }
        }
        fires.add(Fire(topLeft, cells, stepCounter + cfg.fireLifetime))
        return true
    }

    fun maybeSpawn(stepCounter: Int, obstacles: MutableSet<Vec>, obstaclesStyles: MutableMap<Vec, String>): Boolean {
        if (fires.size >= cfg.fireMax) return false
        if (Random.nextDouble() > cfg.fireSpawnChance) return false
        repeat(30) {
            val x = Random.nextInt(0, w - 1)
            val y = Random.nextInt(0, h - 1)
            if (spawnAt(vec(x,y), stepCounter, obstacles, obstaclesStyles)) return true
        }
        return false
    }

    fun draw(screen: Any?, cfg: Config, stepCounter: Int) { /* drawing not implemented */ }
}

