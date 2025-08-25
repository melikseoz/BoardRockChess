package com.boardrockchess

import com.badlogic.gdx.ApplicationAdapter
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import com.badlogic.gdx.graphics.Color as GdxColor

/**
 * Simple libGDX front-end to visualize the core game logic.
 * Human player uses QWE/ASD/ZXC keys to move like the Python version.
 */
class BoardRockApp : ApplicationAdapter() {
    private lateinit var game: Game
    private lateinit var renderer: ShapeRenderer
    private lateinit var cfg: Config

    private val keyToDir = mapOf(
        Input.Keys.Q to vec(-1, -1),
        Input.Keys.W to vec(0, -1),
        Input.Keys.E to vec(1, -1),
        Input.Keys.A to vec(-1, 0),
        Input.Keys.S to null,
        Input.Keys.D to vec(1, 0),
        Input.Keys.Z to vec(-1, 1),
        Input.Keys.X to vec(0, 1),
        Input.Keys.C to vec(1, 1)
    )

    override fun create() {
        cfg = Config.load()
        game = Game(cfg)
        game.initWorld()
        renderer = ShapeRenderer()
    }

    private fun toColor(c: Color) = GdxColor(c.first / 255f, c.second / 255f, c.third / 255f, 1f)

    private fun handleTurns() {
        if (game.winner != null) return
        val actor = game.turnOrder[game.turnIdx]
        when (actor) {
            is HumanPlayer -> {
                if (!actor.alive) {
                    game.advanceTurn(); game.postStep(); return
                }
                for ((key, dir) in keyToDir) {
                    if (Gdx.input.isKeyJustPressed(key)) {
                        if (dir != null) {
                            actor.tryMove(dir, cfg.gridW, cfg.gridH, game.obstacles, game.obstaclesEnabled)
                        }
                        actor.move(actor.pos, game)
                        game.checkWinAfterMove()
                        game.advanceTurn()
                        game.postStep()
                        break
                    }
                }
            }
            is HunterCPU -> {
                if (actor.alive && game.target != null) {
                    val nxt = actor.decide(game.target!!.pos, cfg.gridW, cfg.gridH, game.obstacles, game.obstaclesEnabled)
                    actor.move(nxt, game)
                }
                game.checkWinAfterMove()
                game.advanceTurn()
                game.postStep()
            }
            is TargetCPU -> {
                val human = game.human
                val hunter = game.hunter
                if (actor.alive && human != null && hunter != null) {
                    val nxt = actor.decide(human.pos, hunter.pos, cfg.gridW, cfg.gridH, game.obstacles, game.obstaclesEnabled)
                    actor.move(nxt, game)
                }
                game.checkWinAfterMove()
                game.advanceTurn()
                game.postStep()
            }
        }
    }

    override fun render() {
        handleTurns()
        Gdx.gl.glClearColor(0f, 0f, 0f, 1f)
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT)
        renderer.begin(ShapeRenderer.ShapeType.Filled)
        val cell = cfg.cell.toFloat()
        if (game.obstaclesEnabled) {
            renderer.color = toColor(cfg.colors["obstacle"]!!)
            game.obstacles.forEach { (x, y) ->
                renderer.rect(x * cell, y * cell, cell, cell)
            }
        }
        game.target?.takeIf { it.alive }?.let {
            renderer.color = toColor(it.color)
            renderer.rect(it.pos.first * cell, it.pos.second * cell, cell, cell)
        }
        game.hunter?.takeIf { it.alive }?.let {
            renderer.color = toColor(it.color)
            renderer.rect(it.pos.first * cell, it.pos.second * cell, cell, cell)
        }
        game.human?.takeIf { it.alive }?.let {
            renderer.color = toColor(it.color)
            renderer.rect(it.pos.first * cell, it.pos.second * cell, cell, cell)
        }
        renderer.end()
    }

    override fun dispose() {
        renderer.dispose()
    }
}
