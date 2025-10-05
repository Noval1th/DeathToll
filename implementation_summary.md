# 🎮 Project Zomboid Discord Integration - Complete Implementation Guide

## 📋 What You're Building

A complete Discord notification system for your Project Zomboid server that tracks:

1. ✅ **Player Deaths** - With survival time, location, and skill stats
2. ✅ **Skill Level-ups** - Configurable notifications (all levels or milestones)
3. ✅ **New Characters** - When players respawn
4. ✅ **Player Logins** - Track when players join
5. ✅ **Sunrise/Sunset** - Based on actual in-game light levels
6. ✅ **Daily Survivor Reports** - Every sunrise, lists all online players
7. ✅ **Leaderboards** - Deaths, survival time, total hours, skills

## 🏗️ Architecture Overview

```
[Project Zomboid Server]
         ↓
   [Lua Mod - Server Side]
         ↓
   Writes JSON events to:
   discord_events.log
         ↓
   [Python Script via FTP]
         ↓
   Reads events & sends to:
   [Discord Webhook]
```

## 🚀 Implementation Steps

### Step 1: Create the Lua Mod

1. **Create folder structure:**
   ```
   DiscordEventsTracker/
   ├── mod.info
   └── media/
       └── lua/
           └── server/
               └── DiscordEvents.lua
   ```

2. **Create `mod.info`:**
   ```
   name=Discord Events Tracker
   id=DiscordEventsTracker
   description=Tracks server events for Discord integration
   ```

3. **Copy the Lua code** from the "Project Zomboid Discord Events Mod" artifact into `DiscordEvents.lua`

4. **Install the mod:**
   - **Option A (Local):** Place in `%UserProfile%/Zomboid/mods/`
   - **Option B (Steam Workshop):** Upload to Workshop for easy distribution
   - **Option C (Server):** Place in server's mods directory

5. **Enable the mod:**
   - Add to server startup: `-mod=DiscordEventsTracker`
   - Or add to server's mod list in config

### Step 2: Verify Log File Location

The mod writes to: `Zomboid/Lua/discord_events.log`

**Find the exact path:**

**Windows Server:**
```
C:\Users\[USERNAME]\Zomboid\Server\[SERVER_NAME]\Lua\discord_events.log
```

**Linux Server:**
```
/home/[USERNAME]/Zomboid/Server/[SERVER_NAME]/Lua/discord_events.log
```

**Via FTP:** Check if it's at:
- `/Lua/discord_events.log`
- `/Server/Lua/discord_events.log`
- Or relative to your `LOG_BASE_PATH`

### Step 3: Update Python Script

1. **Add new functions** from the "Complete Python Integration Code" artifact to your `main.py`:
   - `parse_discord_event()`
   - `send_sunrise_notification()`
   - `send_sunset_notification()`
   - `send_daily_survivor_report()`
   - `handle_discord_event()`
   - `monitor_discord_events_log()`

2. **Update `monitor_server()` function** with the enhanced version that monitors both PerkLog AND discord_events.log

3. **Adjust FTP paths** in `monitor_discord_events_log()` to match your server structure

4. **(Optional) Lower polling interval** for more real-time updates:
   ```python
   CHECK_INTERVAL = 10  # Instead of 30
   ```

### Step 4: Testing

1. **Start the server** with mod enabled
2. **Check server console** for:
   ```
   [DiscordEvents] Discord Events Tracker initialized
   [DiscordEvents] Log file: Zomboid/Lua/discord_events.log
   ```

3. **Verify log file exists** at expected location

4. **Start Python script** and check for:
   ```
   📝 Will also monitor discord_events.log from mod
   ```

5. **Trigger test events:**
   - Kill a player → Should see death notification in Discord
   - Level up a skill → Should see level-up notification
   - Wait for sunrise → Should see sunrise + daily report
   - Wait for sunset → Should see sunset notification

### Step 5: Fine-Tuning

**Configure notifications:**
```python
# In your .env or config
SKILL_NOTIFICATIONS = 'milestones'  # 'all', 'milestones', or 'none'
CHECK_INTERVAL = 10  # Polling frequency in seconds
```

**Adjust sunrise/sunset thresholds** in Lua if needed:
```lua
local SUNRISE_THRESHOLD = 0.3  -- Adjust if triggering too early/late
local SUNSET_THRESHOLD = 0.2
```

**Customize event cooldowns** to prevent spam:
```lua
local EVENT_COOLDOWN = 3600  -- 1 hour in ticks
```

## 📊 Event Examples

### Death Event
```json
{
  "timestamp": "2025-01-15 14:30:45",
  "type": "death",
  "data": {
    "username": "Player1",
    "steam_id": "76561198012345678",
    "hours_survived": 24.5,
    "x": 10500,
    "y": 9000,
    "z": 0,
    "skills": "Aiming=5,Fitness=3,Strength=2"
  }
}
```

### Sunrise Event
```json
{
  "timestamp": "2025-01-15 06:00:00",
  "type": "sunrise",
  "data": {
    "game_time": 0.25,
    "light_level": 0.35,
    "game_day": 3
  }
}
```

### Daily Survivors Report
```json
{
  "timestamp": "2025-01-15 06:00:05",
  "type": "daily_survivors",
  "data": {
    "game_day": 3,
    "survivor_count": 5,
    "survivors": [
      {"username": "Player1", "hours": 24.5, "x": 10500, "y": 9000, "z": 0},
      {"username": "Player2", "hours": 18.0, "x": 10600, "y": 9100, "z": 0}
    ]
  }
}
```

## 🔧 Troubleshooting

### Mod Not Loading
- ✅ Check mod is in correct directory
- ✅ Verify `-mod=DiscordEventsTracker` in startup
- ✅ Check server console for Lua errors
- ✅ Ensure file structure is correct (server/ folder matters!)

### Log File Not Created
- ✅ Check server has write permissions to Lua folder
- ✅ Verify mod is running server-side (check console)
- ✅ Trigger an event manually (death, level-up) to force write

### Events Not Appearing in Discord
- ✅ Check Python script is reading correct FTP path
- ✅ Verify `file_positions` is tracking the log file
- ✅ Check for JSON parsing errors in Python console
- ✅ Verify Discord webhook URL is correct

### Duplicate Notifications
- ✅ Mod has cooldowns for sunrise/sunset (expected)
- ✅ Python uses event deduplication via `last_events`
- ✅ Check if multiple Python instances are running

### Missing Sunrise/Sunset Events
- ✅ Adjust threshold values if triggering at wrong times
- ✅ Verify `EveryTenMinutes` event is firing (check console)
- ✅ Wait for full day/night cycle transition

## 🎯 Advantages of This Approach

1. **Clean separation** - Mod handles game events, Python handles Discord
2. **Easy to extend** - Just add new event types in Lua, handle in Python
3. **Reuses your infrastructure** - Same FTP monitoring you already have
4. **No HTTP dependencies** - Lua doesn't need networking libraries
5. **JSON format** - Easy to parse, extend, and debug
6. **Server-only** - No client-side requirements
7. **Lightweight** - Minimal performance impact

## 🔮 Future Enhancements

### Admin Commands
Add in-game commands to trigger actions:
```lua
-- /discord leaderboard death
-- /discord report
-- etc.
```

### Additional Events
- Helicopter events
- Player kill counts
- Horde migrations
- Safe house breaches
- Vehicle repairs/damages
- Custom meta events

### Configuration File
Make settings configurable via INI/JSON:
```lua
-- DiscordEventsConfig.lua
return {
    enableSunrise = true,
    enableSunset = true,
    enableDailyReport = true,
    reportTime = 6.0,  -- Game hour for reports
    -- etc.
}
```

### Database Integration
Store events in SQLite for historical analysis:
```python
# Track long-term statistics
# Generate weekly/monthly reports
# Custom queries and analytics
```

## 📝 Notes

- **Performance:** Minimal overhead - only writes on events
- **File Growth:** Log file grows over time; add rotation in Python if needed
- **Compatibility:** Works with other mods (no known conflicts)
- **Multiplayer:** Fully compatible, tracks all players
- **Singleplayer:** Won't activate (server-side only)

## ✅ Success Checklist

- [ ] Mod files created and installed
- [ ] Mod enabled in server startup
- [ ] Log file created at expected location
- [ ] Python script updated with new functions
- [ ] FTP path configured correctly
- [ ] Discord webhook tested
- [ ] Death events working
- [ ] Level-up events working
- [ ] Login events working
- [ ] Sunrise/sunset working
- [ ] Daily reports working
- [ ] Leaderboards working

---

**You're all set! Your Discord integration will provide rich, real-time notifications for your Project Zomboid server! 🎉**
