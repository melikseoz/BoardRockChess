package com.boardrockchess

import java.io.File

typealias Color = Triple<Int, Int, Int>

/**
 * Basic configuration with a naive JSON loader that understands
 * a handful of numeric, boolean and color fields.
 */
data class Config(
    var gridW: Int = 40,
    var gridH: Int = 40,
    var cell: Int = 18,
    var margin: Int = 1,
    var fps: Int = 60,
    var minStartDist: Int = 12,
    var obstaclesEnabledDefault: Boolean = true,
    var obstacleDensity: Double = 0.10,
    var treeRatio: Double = 0.5,
    var fireMax: Int = 5,
    var fireLifetime: Int = 8,
    var fireSpawnChance: Double = 0.25,
    var respawnDelay: Int = 5,
    var powerupSpawnChance: Double = 0.1,
    var powerupMax: Int = 3,
    var colors: MutableMap<String, Color> = mutableMapOf(
        "bg" to Color(18,18,20),
        "grid" to Color(35,35,40),
        "human" to Color(255,100,90),
        "hunter" to Color(71,130,55),
        "target" to Color(51,168,222),
        "obstacle" to Color(80,80,88),
        "text" to Color(230,230,235),
        "tree_leaf" to Color(46,160,67),
        "tree_trunk" to Color(110,78,48),
        "rock" to Color(120,120,130),
        "fire_core" to Color(255,120,40),
        "fire_glow" to Color(255,200,60),
        "fire_orange" to Color(255,140,60),
        "fire_yellow" to Color(255,210,90),
        "fire_red" to Color(220,70,50),
        "fire_white" to Color(255,245,220)
    )
) {
    companion object {
        fun load(path: String = "config.json"): Config {
            val cfg = Config()
            val file = File(path)
            if (!file.exists()) return cfg
            try {
                val text = file.readText()
                fun findInt(key: String): Int? {
                    val m = Regex("\"$key\"\\s*:\\s*(\\d+)").find(text) ?: return null
                    return m.groupValues[1].toInt()
                }
                fun findDouble(key: String): Double? {
                    val m = Regex("\"$key\"\\s*:\\s*([0-9.]+)").find(text) ?: return null
                    return m.groupValues[1].toDouble()
                }
                fun findBool(key: String): Boolean? {
                    val m = Regex("\"$key\"\\s*:\\s*(true|false)").find(text) ?: return null
                    return m.groupValues[1].toBoolean()
                }
                fun findColor(name: String): Color? {
                    val m = Regex("\"$name\"\\s*:\\s*\\[\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\]").find(text) ?: return null
                    return Color(m.groupValues[1].toInt(), m.groupValues[2].toInt(), m.groupValues[3].toInt())
                }
                findInt("grid_w")?.let { cfg.gridW = it }
                findInt("grid_h")?.let { cfg.gridH = it }
                findInt("cell")?.let { cfg.cell = it }
                findInt("margin")?.let { cfg.margin = it }
                findInt("fps")?.let { cfg.fps = it }
                findInt("min_start_dist")?.let { cfg.minStartDist = it }
                findBool("obstacles_enabled_default")?.let { cfg.obstaclesEnabledDefault = it }
                findDouble("obstacle_density")?.let { cfg.obstacleDensity = it }
                findDouble("tree_ratio")?.let { cfg.treeRatio = it }
                findInt("fire_max")?.let { cfg.fireMax = it }
                findInt("fire_lifetime")?.let { cfg.fireLifetime = it }
                findDouble("fire_spawn_chance")?.let { cfg.fireSpawnChance = it }
                findInt("respawn_delay")?.let { cfg.respawnDelay = it }
                findDouble("powerup_spawn_chance")?.let { cfg.powerupSpawnChance = it }
                findInt("powerup_max")?.let { cfg.powerupMax = it }
                Regex("\"colors\"\\s*:\\s*\\{([^}]*)\\}").find(text)?.groupValues?.get(1)?.let { block ->
                    for (m in Regex("\"([^\"]+)\"\\s*:\\s*\\[\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*\\]").findAll(block)) {
                        val name = m.groupValues[1]
                        cfg.colors[name] = Color(m.groupValues[2].toInt(), m.groupValues[3].toInt(), m.groupValues[4].toInt())
                    }
                }
            } catch (e: Exception) {
                println("[Config] Failed to read $path: ${'$'}{e.message}. Using defaults.")
            }
            return cfg
        }
    }
}

