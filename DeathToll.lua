-- DeathToll.lua - Discord Events Tracker for Project Zomboid
-- Writes JSON events to a log file for external monitoring
-- Version: 1.0
-- Author: Your Name

if not isServer() then return end

local DeathToll = {}

-- Configuration
DeathToll.LOG_FILE = "discord_events.log"
DeathToll.MOD_ID = "DeathToll"

-- Track light state for sunrise/sunset detection
DeathToll.lastLightLevel = nil
DeathToll.SUNRISE_THRESHOLD = 0.3
DeathToll.SUNSET_THRESHOLD = 0.2

-- Track last event times to prevent spam
DeathToll.lastSunriseTime = 0
DeathToll.lastSunsetTime = 0
DeathToll.EVENT_COOLDOWN = 3600  -- 1 hour in game ticks

-- Helper: Write event to log file
function DeathToll.writeEvent(eventType, data)
    local writer = getModFileWriter(DeathToll.MOD_ID, DeathToll.LOG_FILE, true, true)
    if not writer then
        print("[DeathToll] ERROR: Could not open log file")
        return false
    end
    
    -- Build JSON manually to avoid dependencies
    local jsonData = "{"
    local first = true
    for k, v in pairs(data) do
        if not first then jsonData = jsonData .. "," end
        first = false
        
        if type(v) == "string" then
            -- Escape quotes in strings
            local escapedValue = v:gsub('"', '\\"')
            jsonData = jsonData .. string.format('"%s":"%s"', k, escapedValue)
        elseif type(v) == "number" then
            jsonData = jsonData .. string.format('"%s":%s', k, tostring(v))
        elseif type(v) == "boolean" then
            jsonData = jsonData .. string.format('"%s":%s', k, tostring(v))
        end
    end
    jsonData = jsonData .. "}"
    
    local logLine = string.format(
        '{"timestamp":"%s","type":"%s","data":%s}\n',
        os.date("%Y-%m-%d %H:%M:%S"),
        eventType,
        jsonData
    )
    
    writer:write(logLine)
    writer:close()
    
    print(string.format("[DeathToll] Event logged: %s", eventType))
    return true
end

-- Helper: Get player's top skills
function DeathToll.getTopSkills(player, count)
    local skills = {}
    local perkList = PerkFactory.PerkList
    
    for i = 0, perkList:size() - 1 do
        local perk = perkList:get(i)
        local level = player:getPerkLevel(perk)
        if level > 0 then
            table.insert(skills, {name = perk:getName(), level = level})
        end
    end
    
    table.sort(skills, function(a, b) return a.level > b.level end)
    
    local result = {}
    for i = 1, math.min(count, #skills) do
        result[skills[i].name] = skills[i].level
    end
    
    return result
end

-- Helper: Serialize skills table to string
function DeathToll.skillsToString(skills)
    local parts = {}
    for name, level in pairs(skills) do
        table.insert(parts, string.format("%s=%d", name, level))
    end
    return table.concat(parts, ",")
end

-- Helper: Safely get Steam ID
function DeathToll.getSteamID(player)
    if player.getSteamID then
        local steamID = player:getSteamID()
        if steamID then
            return tostring(steamID)
        end
    end
    -- Fallback to username if Steam ID not available
    return player:getUsername() or "unknown"
end

-- Event 1: Player Death
function DeathToll.onPlayerDeath(player)
    if not player then return end
    
    local username = player:getUsername()
    if not username then return end
    
    local hours = player:getHoursSurvived() or 0
    local x, y, z = player:getX(), player:getY(), player:getZ()
    
    -- Get top 5 skills
    local topSkills = DeathToll.getTopSkills(player, 5)
    
    DeathToll.writeEvent("death", {
        username = username,
        steam_id = DeathToll.getSteamID(player),
        hours_survived = hours,
        x = math.floor(x),
        y = math.floor(y),
        z = math.floor(z),
        skills = DeathToll.skillsToString(topSkills)
    })
end

-- Event 2: Skill Level Up
function DeathToll.onLevelPerk(player, perk, level, levelUp)
    if not player or not levelUp then return end
    if not perk then return end
    
    local username = player:getUsername()
    if not username then return end
    
    local skillName = perk:getName()
    local hours = player:getHoursSurvived() or 0
    
    DeathToll.writeEvent("level_up", {
        username = username,
        steam_id = DeathToll.getSteamID(player),
        skill = skillName,
        level = level,
        hours_survived = hours
    })
end

-- Event 3: New Character Creation (Player Spawn)
function DeathToll.onCreatePlayer(index, player)
    if not player then return end
    
    local username = player:getUsername()
    if not username then return end
    
    local x, y, z = player:getX(), player:getY(), player:getZ()
    
    DeathToll.writeEvent("character_created", {
        username = username,
        steam_id = DeathToll.getSteamID(player),
        character_index = index or 0,
        x = math.floor(x),
        y = math.floor(y),
        z = math.floor(z)
    })
end

-- Event 4: Player Login
function DeathToll.onClientCommand(module, command, player, args)
    if module ~= "Players" or command ~= "PlayerConnect" then return end
    if not player then return end
    
    local username = player:getUsername()
    if not username then return end
    
    local hours = player:getHoursSurvived() or 0
    
    -- Get current skills
    local skills = DeathToll.getTopSkills(player, 10)
    
    DeathToll.writeEvent("login", {
        username = username,
        steam_id = DeathToll.getSteamID(player),
        hours_survived = hours,
        skills = DeathToll.skillsToString(skills)
    })
end

-- Event 5: Sunrise/Sunset Detection
function DeathToll.checkDayNightCycle()
    local gameTime = getGameTime()
    if not gameTime then return end
    
    local climateManager = getClimateManager()
    if not climateManager then return end
    
    local lightLevel = climateManager:getDayLightStrength()
    local currentTime = gameTime:getTimeOfDay()
    
    if DeathToll.lastLightLevel == nil then
        DeathToll.lastLightLevel = lightLevel
        return
    end
    
    local currentTick = getTimestamp()
    
    -- Detect sunrise (transitioning from dark to light)
    if DeathToll.lastLightLevel < DeathToll.SUNRISE_THRESHOLD and 
       lightLevel >= DeathToll.SUNRISE_THRESHOLD then
        if currentTick - DeathToll.lastSunriseTime > DeathToll.EVENT_COOLDOWN then
            DeathToll.writeEvent("sunrise", {
                game_time = currentTime,
                light_level = lightLevel,
                game_day = gameTime:getNightsSurvived()
            })
            DeathToll.lastSunriseTime = currentTick
            
            -- Also send daily survivor report at sunrise
            DeathToll.sendDailySurvivorReport()
        end
    end
    
    -- Detect sunset (transitioning from light to dark)
    if DeathToll.lastLightLevel > DeathToll.SUNSET_THRESHOLD and 
       lightLevel <= DeathToll.SUNSET_THRESHOLD then
        if currentTick - DeathToll.lastSunsetTime > DeathToll.EVENT_COOLDOWN then
            DeathToll.writeEvent("sunset", {
                game_time = currentTime,
                light_level = lightLevel,
                game_day = gameTime:getNightsSurvived()
            })
            DeathToll.lastSunsetTime = currentTick
        end
    end
    
    DeathToll.lastLightLevel = lightLevel
end

-- Event 6: Daily Survivor Report (at sunrise)
function DeathToll.sendDailySurvivorReport()
    local onlinePlayers = getOnlinePlayers()
    if not onlinePlayers or onlinePlayers:size() == 0 then
        return
    end
    
    local survivors = {}
    for i = 0, onlinePlayers:size() - 1 do
        local player = onlinePlayers:get(i)
        if player then
            local username = player:getUsername()
            if username then
                local hours = player:getHoursSurvived() or 0
                local x, y, z = player:getX(), player:getY(), player:getZ()
                
                table.insert(survivors, {
                    username = username,
                    hours = hours,
                    x = math.floor(x),
                    y = math.floor(y),
                    z = math.floor(z)
                })
            end
        end
    end
    
    if #survivors > 0 then
        -- Serialize survivors array manually
        local survivorsJson = "["
        for i, s in ipairs(survivors) do
            if i > 1 then survivorsJson = survivorsJson .. "," end
            survivorsJson = survivorsJson .. string.format(
                '{"username":"%s","hours":%s,"x":%d,"y":%d,"z":%d}',
                s.username, tostring(s.hours), s.x, s.y, s.z
            )
        end
        survivorsJson = survivorsJson .. "]"
        
        -- Write as special event type with raw JSON
        local writer = getModFileWriter(DeathToll.MOD_ID, DeathToll.LOG_FILE, true, true)
        if writer then
            local gameTime = getGameTime()
            local logLine = string.format(
                '{"timestamp":"%s","type":"daily_survivors","data":{"game_day":%d,"survivor_count":%d,"survivors":%s}}\n',
                os.date("%Y-%m-%d %H:%M:%S"),
                gameTime:getNightsSurvived(),
                #survivors,
                survivorsJson
            )
            writer:write(logLine)
            writer:close()
            print(string.format("[DeathToll] Daily survivor report: %d players", #survivors))
        end
    end
end

-- Event 7: Leaderboard request (triggered by admin command)
function DeathToll.onServerCommand(module, command, player, args)
    if module ~= "DeathToll" then return end
    
    if command == "RequestLeaderboard" then
        local leaderboardType = args.type or "death"
        
        DeathToll.writeEvent("leaderboard_request", {
            type = leaderboardType,
            requested_by = player:getUsername()
        })
    end
end

-- Initialize event handlers
function DeathToll.init()
    print(string.rep("=", 50))
    print("[DeathToll] Initializing Discord Events Tracker")
    print("[DeathToll] Version 1.0")
    print(string.rep("=", 50))
    
    Events.OnPlayerDeath.Add(DeathToll.onPlayerDeath)
    Events.LevelPerk.Add(DeathToll.onLevelPerk)
    Events.OnCreatePlayer.Add(DeathToll.onCreatePlayer)
    Events.OnClientCommand.Add(DeathToll.onClientCommand)
    Events.OnServerCommand.Add(DeathToll.onServerCommand)
    
    -- Check day/night cycle every 10 minutes (game time)
    Events.EveryTenMinutes.Add(DeathToll.checkDayNightCycle)
    
    print(string.format("[DeathToll] Log file: Zomboid/Lua/%s", DeathToll.LOG_FILE))
    print("[DeathToll] Events: Death, Level-Up, Character Creation, Login, Sunrise/Sunset, Daily Reports")
    print("[DeathToll] Initialization complete!")
    print(string.rep("=", 50))
end

-- Start the mod when the game boots
Events.OnServerStarted.Add(function()
    print("[DeathToll] OnServerStarted fired")
    DeathToll.init()
end)

Events.OnInitGlobalModData.Add(function()
    print("[DeathToll] OnInitGlobalModData fired")
    DeathToll.init()
end)

-- As absolute fallback, run immediately
-- Comment this out later once events work
-- DeathToll.init()


return DeathToll
