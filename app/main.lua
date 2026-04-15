-- main.lua for Lutro (SNES emu window, load PNG/banks)
-- Save as app/main.lua

function love.load()
    -- Load sprites from PNG/banks
    sprites = {}
    local pngs = {"super_mario_world_mario.png", "super_mario_world_luigi.png", "super_mario_world_yoshi.png", "super_mario_world_bowser.png"}
    for i=1,4 do
        sprites[i] = love.graphics.newImage("assets/authentic_sprites/" .. pngs[i])
    end
    tiles = love.graphics.newQuad(0, 0, 16, 16, sprites[1]:getDimensions())
    snp = love.audio.newSource("assets/audio/super_mario_world_jump_sfx.wav", "static")
    banks = {}
    banks.coin = love.audio.newSource("assets/audio/super_mario_world_coin.wav", "static")
    banks.jump = love.audio.newSource("assets/audio/jump.wav", "static")
end

function love.update(dt)
    -- 60fps loop
    if love.timer.getTime() % (1/60) < dt then
        -- Render from bank/offset stub
        love.graphics.draw(sprites[1], tiles, 100, 100)
    end
    -- Sync audio
    if love.keyboard.isDown("space") then
        snp:play()
    end
end

function love.draw()
    love.graphics.print("SNES Window: Crono Render", 10, 10)
end