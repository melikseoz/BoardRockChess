package com.boardrockchess

import kotlin.math.abs
import kotlin.math.max
import kotlin.random.Random

// 2D integer vector represented as a pair

typealias Vec = Pair<Int, Int>

val DIRS_8: List<Vec> = listOf(
    Pair(-1, -1), Pair(0, -1), Pair(1, -1),
    Pair(-1, 0),                 Pair(1, 0),
    Pair(-1, 1),  Pair(0, 1),   Pair(1, 1)
)

fun add(a: Vec, b: Vec): Vec = Pair(a.first + b.first, a.second + b.second)

fun vec(x: Int, y: Int): Vec = Pair(x, y)

fun inBounds(p: Vec, w: Int, h: Int): Boolean = p.first in 0 until w && p.second in 0 until h

fun cheb(a: Vec, b: Vec): Int = max(abs(a.first - b.first), abs(a.second - b.second))

fun legalNeighbors(p: Vec, w: Int, h: Int, obstacles: Set<Vec>, obstaclesEnabled: Boolean): List<Vec> {
    val opts = mutableListOf<Vec>()
    for (d in DIRS_8) {
        val q = add(p, d)
        if (inBounds(q, w, h) && (!obstaclesEnabled || q !in obstacles)) {
            opts.add(q)
        }
    }
    return opts
}

// --- Starts & obstacles ---

private fun randomInQuadrant(q: Int, w: Int, h: Int): Vec {
    // Quadrants: 0=TL, 1=TR, 2=BL, 3=BR
    val wq = w / 2
    val hq = h / 2
    val x0 = if (q == 0 || q == 2) 0 else wq
    val y0 = if (q == 0 || q == 1) 0 else hq
    val margin = 3
    val x = Random.nextInt(x0 + margin, x0 + wq - margin)
    val y = Random.nextInt(y0 + margin, y0 + hq - margin)
    return vec(x, y)
}

fun pickStartPositions(w: Int, h: Int, minStartDist: Int): Triple<Vec, Vec, Vec> {
    val opposite = mapOf(0 to 3, 1 to 2, 2 to 1, 3 to 0)
    var human: Vec
    var hunter: Vec
    while (true) {
        val qh = Random.nextInt(0, 4)
        val qH = opposite[qh]!!
        human = randomInQuadrant(qh, w, h)
        hunter = randomInQuadrant(qH, w, h)
        if (cheb(human, hunter) >= minStartDist) break
    }
    val cx = w / 2
    val cy = h / 2
    val minDist = max(6, minStartDist / 2)
    var target: Vec? = null
    for (radius in 4..(min(w, h) / 2)) {
        val candidates = mutableListOf<Vec>()
        for (x in (cx - radius)..(cx + radius)) {
            for (y in (cy - radius)..(cy + radius)) {
                val p = vec(x, y)
                if (!inBounds(p, w, h)) continue
                if (p == human || p == hunter) continue
                if (cheb(p, vec(cx, cy)) <= radius && cheb(p, human) >= minDist && cheb(p, hunter) >= minDist) {
                    candidates.add(p)
                }
            }
        }
        if (candidates.isNotEmpty()) {
            target = candidates.random()
            break
        }
    }
    if (target == null) {
        val center = vec(cx, cy)
        if (center != human && center != hunter && inBounds(center, w, h)) {
            target = center
        } else {
            outer@ for (r in 1..max(w, h)) {
                val ring = mutableListOf<Vec>()
                for (x in (cx - r)..(cx + r)) {
                    for (y in (cy - r)..(cy + r)) {
                        val p = vec(x, y)
                        if (!inBounds(p, w, h)) continue
                        if (p == human || p == hunter) continue
                        if (cheb(p, vec(cx, cy)) == r) ring.add(p)
                    }
                }
                if (ring.isNotEmpty()) {
                    target = ring.random(); break@outer
                }
            }
        }
    }
    return Triple(human, hunter, target!!)
}

fun generateObstacles(w: Int, h: Int, density: Double, exclude: Set<Vec>, treeRatio: Double = 0.5): Pair<Set<Vec>, Map<Vec, String>> {
    val obstacles = mutableSetOf<Vec>()
    val styles = mutableMapOf<Vec, String>()
    for (y in 0 until h) {
        for (x in 0 until w) {
            val p = vec(x, y)
            if (p in exclude) continue
            if (Random.nextDouble() < density) {
                obstacles.add(p)
                styles[p] = if (Random.nextDouble() < treeRatio) "tree" else "rock"
            }
        }
    }
    val ringClear = mutableSetOf<Vec>()
    for (e in exclude) {
        for (dx in -1..1) {
            for (dy in -1..1) {
                val q = vec(e.first + dx, e.second + dy)
                if (inBounds(q, w, h)) ringClear.add(q)
            }
        }
    }
    val filtered = obstacles.filter { it !in ringClear }.toSet()
    val filteredStyles = styles.filterKeys { it in filtered }
    return Pair(filtered, filteredStyles)
}

private fun min(a: Int, b: Int): Int = if (a < b) a else b

