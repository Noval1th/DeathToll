# DeathToll
A Mod for Project Zomboid that collects data via a LUA mod into an easily parsible log file, and can then be shared to discord using  an extrenal python script

# Discord Events Tracker - Installation & Setup Guide

## 📁 Mod Structure

Create this folder structure in your Project Zomboid mods directory:

```
DiscordEventsTracker/
├── mod.info
└── media/
    └── lua/
        └── server/
            └── DiscordEvents.lua
```

### mod.info
```
name=Discord Events Tracker
id=DiscordEventsTracker
description=Tracks server events and outputs them to a log file for Discord integration
poster=poster.png
```

### File Locations

**Development/Testing:**
- Workshop mod location: `Steam/steamapps/workshop/content/108600/[mod_id]/`
- Local mod location: `%UserProfile%/Zomboid/mods/DiscordEventsTracker/`

**Server Installation:**
- Subscribe to the mod in Steam Workshop (if published)
- Or manually place in server's mods directory
- Enable in server's `-mod=` startup parameter

**Log File Output:**
- Windows: `C:\Users\[USERNAME]\Zomboid\Server\[SERVER_NAME]\Lua\discord_events.log`
- Linux: `/home/[USERNAME]/Zomboid/Server/[SERVER_NAME]/Lua/discord_events.log`

## 🔧 Python Script Setup

### 1. Update Your FTP Paths

Add to your monitoring paths in `main.py`:

```python
# In get_log_folders_to_check(), also check Lua folder:
def get_lua_folder_path(ftp):
    """Get path to Lua folder where mod writes logs"""
    # This is typically at the same level as Logs
    return "/Lua"  # Adjust based on your FTP structure
```

### 2. Add Discord Events Monitoring

In your `monitor_server()` function, add this after the PerkLog monitoring:

```python
# Monitor mod's discord events log
try:
    lua_folder = "/Lua"  # Adjust to your server's path
    monitor_discord_events_log(ftp, lua_folder)
except Exception as e:
    print(f"⚠️ Error processing discord events: {e}")
```

### 3. Adjust Polling Interval (Optional)

For more real-time notifications:

```python
CHECK_INTERVAL = 10  # Changed from 30 to 10 seconds
```

## 🎮 Testing the Mod

### 1. Install on Test Server
1. Place mod files in mods directory
2. Add to server startup: `-mod=DiscordEventsTracker`
3. Start server and check console for: `[DiscordEvents] Discord Events Tracker initialized`

### 2. Verify Log File Creation
Check that `discord_events.log` is created in:
- Windows: `%UserProfile%/Zomboid/Server/[SERVER_NAME]/Lua/`
- Linux: `~/Zomboid/Server/[SERVER_NAME]/Lua/`

### 3. Trigger Test Events
- **Death**: Kill a player character → Should log death event
- **Level Up**: Gain a skill level → Should log level_up event
- **Login**: Connect to server → Should log login event
- **Sunrise/Sunset**: Wait for day/night cycle → Should log time events

### 4. Check Log Format
Events should look like this:
```json
{"timestamp":"2025-01-15 14:30:45","type":"death","data":{"username":"Player1","steam_id":"76561198012345678","hours_survived":24.5,"x":10500,"y":9000,"z":0,"skills":"Aiming=5,Fitness=3"}}
{"timestamp":"2025-01-15 14:31:00","type":"sunrise","data":{"game_time":0.25,"light_level":0.35,"game_day":3}}
```

## 🐛 Troubleshooting

### Log File Not Created
- Check server console for errors
- Verify mod is loaded: Check server startup logs
- Check file permissions on Lua directory

### Events Not Being Detected
- Verify FTP path in Python script matches actual log location
- Check Python console for parsing errors
- Ensure `last_pos` tracking is working (check `file_positions` dict)

### Duplicate Notifications
- The mod includes event cooldowns for sunrise/sunset
- Python script uses event deduplication via `last_events` set

### Missing Events
- Check that events are server-side only (mod only runs on server)
- Verify event handlers are registered in console output
- Enable debug mode by uncommenting print statements

## 📊 Event Types Reference

| Event Type | Triggers When | Data Included |
|------------|---------------|---------------|
| `death` | Player dies | username, hours_survived, coordinates, skills |
| `level_up` | Player gains skill level | username, skill, level, hours_survived |
| `character_created` | New character spawned | username, coordinates |
| `login` | Player connects | username, hours_survived, skills |
| `sunrise` | Light level crosses sunrise threshold | game_time, light_level, game_day |
| `sunset` | Light level crosses sunset threshold | game_time, light_level, game_day |
| `daily_survivors` | Every sunrise (auto-triggered) | game_day, survivor_count, survivors[] |
| `leaderboard_request` | Admin command (future) | type, requested_by |

## 🎯 Future Enhancements

### Admin Commands
Add in-game commands to trigger leaderboards:
```lua
-- Example: /discord leaderboard death
-- Would need to implement command parsing
```

### Configurable Settings
Create `DiscordEventsConfig.lua`:
```lua
DiscordEventsConfig = {
    enableSunrise = true,
    enableSunset = true,
    enableDailyReport = true,
    sunriseThreshold = 0.3,
    sunsetThreshold = 0.2
}
```

### Additional Events
- Player kill count milestones
- Helicopter events
- Meta events (temperature drops, etc.)
- Custom server events

## 📝 Notes

- **Performance**: The mod is lightweight and only writes to file on events
- **File Size**: Log file grows over time; consider log rotation in Python
- **Multiplayer**: Fully compatible, tracks all players
- **Singleplayer**: Won't activate (server-side only)
- **Compatibility**: Should work with most other mods (no conflicts expected)
