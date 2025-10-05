-- Discord Events Tracker for Project Zomboid
-- Writes JSON events to a log file for external monitoring

local DiscordEvents = {}

-- Configuration
local LOG_FILE = "discord_events.log"
local MOD_ID = "DiscordEventsTracker"

-- Track light state for sunrise/sunset detection
local lastLightLevel = nil
local SUNRISE_THRESHOLD = 0.3  -- Light level threshold for sunrise
local SUNSET_THRESHOLD = 0.2   -- Light level threshold for sunset

-- Track last event times to prevent spam
local lastSunriseTime = 0
local lastSunsetTime = 0
local EVENT_COOLDOWN = 3600  -- 1 hour in game ticks (at 1 tick/sec)

-- Helper: Write event to log file
local function writeEvent(eventType, data)
    if not isServer() then return end
    
    local writer = getModFileWriter(MOD_ID, LOG_FILE, true, true)
    if not writer then
        print("ERROR: Could not open discord events log file")
        return
    end
    
    -- Build JSON manually to avoid dependencies
    local jsonData = "{"
    local first = true
    for k, v in pairs(data) do
        if not first then jsonData = jsonData .. "," end
        first = false
        
        if type(v) == "string" then
            jsonData = jsonData .. string.format('"%s":"%s"', k, v:gsub('"', '\\"'))
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
    
    print(string.format("[DiscordEvents] Logged: %s", eventType))
end

-- Helper: Get player's top skills
local function getTopSkills(player, count)
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
local function skillsToString(skills)
    local parts = {}
    for name, level in pairs(skills) do
        table.insert(parts, string.format("%s=%d", name, level))
    end
    return table.concat(parts, ",")
end

-- Event 1: Player Death
local function onPlayerDeath(player)
    if not player then return end
    
    local username = player:getUsername()
    local hours = player:getHoursSurvived()
    local x, y, z = player:getX(), player:getY(), player:getZ()
    
    -- Get top 5 skills
    local topSkills = getTopSkills(player, 5)
    
    writeEvent("death", {
        username = username,
        steam_id = tostring(player:getSteamID()),
        hours_survived = hours,
        x = math.floor(x),
        y = math.floor(y),
        z = math.floor(z),
        skills = skillsToString(topSkills)
    })
end

-- Event 2: Skill Level Up
local function onLevelPerk(player, perk, level, levelUp)
    if not player or not levelUp then return end
    
    local username = player:getUsername()
    local skillName = perk:getName()
    local hours = player:getHoursSurvived()
    
    writeEvent("level_up", {
        username = username,
        steam_id = tostring(player:getSteamID()),
        skill = skillName,
        level = level,
        hours_survived = hours
    })
end

-- Event 3: New Character Creation (Player Spawn)
local function onCreatePlayer(index, player)
    if not player then return end
    
    local username = player:getUsername()
    local x, y, z = player:getX(), player:getY(), player:getZ()
    
    writeEvent("character_created", {
        username = username,
        steam_id = tostring(player:getSteamID()),
        character_index = index,
        x = math.floor(x),
        y = math.floor(y),
        z = math.floor(z)
    })
end

-- Event 4: Player Login
local function onClientCommand(module, command, player, args)
    if module == "Players" and command == "PlayerConnect" then
        if not player then return end
        
        local username = player:getUsername()
        local hours = player:getHoursSurvived()
        
        -- Get current skills
        local skills = getTopSkills(player, 10)
        
        writeEvent("login", {
            username = username,
            steam_id = tostring(player:getSteamID()),
            hours_survived = hours,
            skills = skillsToString(skills)
        })
    end
end

-- Event 5: Sunrise/Sunset Detection
local function checkDayNightCycle()
    if not isServer() then return end
    
    local currentTime = getGameTime():getTimeOfDay()
    local lightLevel = getClimateManager():getDayLightStrength()
    
    if lastLightLevel == nil then
        lastLightLevel = lightLevel
        return
    end
    
    local currentTick = getTimestamp()
    
    -- Detect sunrise (transitioning from dark to light)
    if lastLightLevel < SUNRISE_THRESHOLD and lightLevel >= SUNRISE_THRESHOLD then
        if currentTick - lastSunriseTime > EVENT_COOLDOWN then
            writeEvent("sunrise", {
                game_time = currentTime,
                light_level = lightLevel,
                game_day = getGameTime():getNightsSurvived()
            })
            lastSunriseTime = currentTick
            
            -- Also send daily survivor report at sunrise
            sendDailySurvivorReport()
        end
    end
    
    -- Detect sunset (transitioning from light to dark)
    if lastLightLevel > SUNSET_THRESHOLD and lightLevel <= SUNSET_THRESHOLD then
        if currentTick - lastSunsetTime > EVENT_COOLDOWN then
            writeEvent("sunset", {
                game_time = currentTime,
                light_level = lightLevel,
                game_day = getGameTime():getNightsSurvived()
            })
            lastSunsetTime = currentTick
        end
    end
    
    lastLightLevel = lightLevel
end

-- Event 7: Daily Survivor Report (at sunrise)
function sendDailySurvivorReport()
    if not isServer() then return end
    
    local onlinePlayers = getOnlinePlayers()
    if not onlinePlayers or onlinePlayers:size() == 0 then
        return
    end
    
    local survivors = {}
    for i = 0, onlinePlayers:size() - 1 do
        local player = onlinePlayers:get(i)
        if player then
            local username = player:getUsername()
            local hours = player:getHoursSurvived()
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
        local writer = getModFileWriter(MOD_ID, LOG_FILE, true, true)
        if writer then
            local logLine = string.format(
                '{"timestamp":"%s","type":"daily_survivors","data":{"game_day":%d,"survivor_count":%d,"survivors":%s}}\n',
                os.date("%Y-%m-%d %H:%M:%S"),
                getGameTime():getNightsSurvived(),
                #survivors,
                survivorsJson
            )
            writer:write(logLine)
            writer:close()
            print(string.format("[DiscordEvents] Daily survivor report: %d players", #survivors))
        end
    end
end

-- Event 6: Leaderboard request (triggered by admin command)
local function onServerCommand(module, command, player, args)
    if module ~= "DiscordEvents" then return end
    
    if command == "RequestLeaderboard" then
        local leaderboardType = args.type or "death"
        
        writeEvent("leaderboard_request", {
            type = leaderboardType,
            requested_by = player:getUsername()
        })
    end
end

-- Register all event handlers
local function initEvents()
    -- Only run on server
    if not isServer() then return end
    
    Events.OnPlayerDeath.Add(onPlayerDeath)
    Events.LevelPerk.Add(onLevelPerk)
    Events.OnCreatePlayer.Add(onCreatePlayer)
    Events.OnClientCommand.Add(onClientCommand)
    Events.OnServerCommand.Add(onServerCommand)
    
    -- Check day/night cycle every 10 seconds (every ~10 ticks)
    Events.EveryTenMinutes.Add(checkDayNightCycle)
    
    print("[DiscordEvents] Discord Events Tracker initialized")
    print(string.format("[DiscordEvents] Log file: Zomboid/Lua/%s", LOG_FILE))
end

Events.OnGameBoot.Add(initEvents)

return DiscordEvents
