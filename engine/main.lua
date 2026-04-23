-- Lutro main.lua - SNES TV Renderer
-- Loads ROM sprites/tilemaps, renders 90s TV scenes

local gfx = require "gfx"
local inp = require "inp"
local sys = require "sys"

-- Asset paths (shared with Python)
SPRITES_DIR = "assets/sprites"
TILEMAPS_DIR = "assets/backgrounds"

-- Scene state
current_scene = "news_desk"
sprite_index = 1
sprites = {}
tilemap = nil
frame = 0

function load_assets()
  -- Load PNG sprites as textures
  local files = sys.dir(SPRITES_DIR .. "/*.png")
  for _, file in ipairs(files) do
    local name = file:gsub(".png", "")
    sprites[name] = gfx.loadpng(SPRITES_DIR .. "/" .. file)
    print("Loaded sprite: " .. name)
  end
  
  -- Load tilemap (bin → texture)
  tilemap = gfx.loadpng("assets/backgrounds/news_studio.bin.png")  -- Converted bin
  print("Loaded " .. #sprites .. " sprites, tilemap ready")
end

function love.load()
  love.window.setTitle("T3MPLATE TV - Lutro Edition")
  love.window.setMode(512, 448, {fullscreen=false, vsync=true})
  load_assets()
end

function love.draw()
  frame = frame + 1
  
  -- CRT scanlines
  love.graphics.setColor(0.1, 0.1, 0.2)
  love.graphics.rectangle("fill", 0, 0, 512, 448)
  
  -- Mode7 background (tilemap rotate)
  love.graphics.setColor(1,1,1)
  love.graphics.draw(tilemap, 256, 224, frame * 0.01, 1 + math.sin(frame*0.05)*0.1, 1, tilemap:getWidth()/2, tilemap:getHeight()/2)
  
  -- Active sprite (cycle)
  local names = {}
  for k,_ in pairs(sprites) do table.insert(names, k) end
  local name = names[(sprite_index % #names) + 1]
  local spr = sprites[name]
  if spr then
    love.graphics.draw(spr, 256, 224)
    love.graphics.print(name:upper(), 256 - spr:getWidth()/2, 224 - 40)
  end
  
  -- Gary ticker
  love.graphics.setColor(0,1,0)
  love.graphics.print("GARY: Ratings up - Crossover special!", 10, 418)
  
  -- HUD
  love.graphics.setColor(0,1,1)
  love.graphics.print("T3MPLATE TV v1.0 - ALL ROMs Live", 10, 10)
end

function love.update(dt)
  if inp.isDown(inp.BTN_LEFT) then sprite_index = sprite_index - 1 end
  if inp.isDown(inp.BTN_RIGHT) then sprite_index = sprite_index + 1 end
end