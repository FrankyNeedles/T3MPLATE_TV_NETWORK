-- main.lua: Lutro SNES emulation core for broadcast rendering
love.graphics.setBackgroundColor(0.1, 0.1, 0.3)  -- SNES black

function love.load()
    -- Load authentic sprites from Python IPC
    sprites = {}
end

function love.update(dt)
    -- Tick from station.py IPC
end

function love.draw()
    love.graphics.rectangle('fill', 100, 100, 16, 16)  -- Placeholder Mario sprite
end