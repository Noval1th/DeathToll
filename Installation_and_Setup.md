# 🎮 DeathToll - Discord Events Tracker

## 📁 Complete Mod Structure

Create this exact folder structure:

```
DeathToll/
├── mod.info
└── media/
    └── lua/
        └── server/
            └── DeathToll.lua
```

## 📄 File Contents

### 1. mod.info

Create `DeathToll/mod.info`:

```
name=DeathToll
id=DeathToll
description=Tracks server events and outputs them to a log file for Discord integration. Monitors deaths, respawns, level-ups, logins, and day/night cycles.
poster=poster.png
require=
```

**Optional:** Add a `poster.png` (512x512) image in the root folder for Workshop appearance.

### 2. DeathToll.lua

The Lua code is in the artifact above. Place it at:
```
DeathToll/media/lua/server/DeathToll.lua
```

**Important:** The file MUST be in the `server/` subdirectory, not `shared/` or `client/`.

## 🚀 Installation Methods

### Method 1: G-Portal FTP Installation (Your Setup)

**Your specific G-Portal directory structure:**
```
/Zomboid/
├── /Server/
│   └── servertest.ini
├── /Saves/
├── /mods/              ← Place DeathToll here
└── /Logs/
```

**Installation steps:**

1. **Connect to your server via FTP**
   - FTP home directory starts at `/Zomboid/`

2. **Check if `/mods/` folder exists**
   - If not, create it manually in `/Zomboid/mods/`

3. **Upload the entire `DeathToll/` folder to `/Zomboid/mods/`**
   - Final structure: `/Zomboid/mods/DeathToll/`
   - Inside should be: `mod.info` and `media/` folder

4. **Edit `/Zomboid/Server/servertest.ini`**
   - Find the line that starts with `Mods=`
   - Add `DeathToll` to the list (semicolon-separated, no spaces)
   
   **Example:**
   ```ini
   Mods=DeathToll
   
   # Or if you have other mods:
   Mods=ExistingMod;DeathToll;AnotherMod
   ```

5. **⚠️ IMPORTANT: Do NOT use G-Portal web control panel after this!**
   - G-Portal's web interface **overwrites FTP changes**
   - Make ALL future edits via FTP only
   - Or keep a backup of `servertest.ini` to restore after using web panel

6. **Restart the server**

### Method 2: Local Installation (Testing)

1. **Find your mods folder:**
   - **Windows:** `C:\Users\[USERNAME]\Zomboid\mods\`
   - **Linux:** `~/Zomboid/mods/`

2. **Copy the entire `DeathToll/` folder there**

3. **Enable the mod in your save's configuration**

### Method 3: Other Hosting Providers

For other hosts (not G-Portal):
- **Windows Self-Hosted:** `C:\Users\[USERNAME]\Zomboid\mods\`
- **Linux Self-Hosted:** `~/Zomboid/mods/`
- **Other Managed Hosts:** Check provider documentation for exact path

Then edit `servertest.ini` to add:
```ini
Mods=DeathToll
```

### Method 4: Steam Workshop (For Distribution)

1. **Create Workshop item** using the in-game Workshop tool

2. **Upload your mod folder** with proper structure

3. **Subscribe to your mod** on the server

4. **Server will auto-download** the mod on startup

## ✅ Verification Steps

### Step 1: Verify File Structure via FTP

Connect to FTP and confirm this exact structure:
```
/Zomboid/
└── mods/
    └── DeathToll/
        ├── mod.info
        └── media/
            └── lua/
                └── server/
                    └── DeathToll.lua
```

### Step 2: Verify Configuration

Open `/Zomboid/Server/servertest.ini` and confirm:
```ini
Mods=DeathToll
# Or with other mods:
Mods=YourOtherMod;DeathToll
```

**Note:** Make sure there are:
- ✅ NO spaces after semicolons
- ✅ NO semicolon at the end of the line
- ✅ Exact capitalization: `DeathToll` (not `deathtoll` or `DEATHTOLL`)

### Step 3: Check Server Console

Start your server and look for these messages:

```
==================================================
[DeathToll] Initializing Discord Events Tracker
[DeathToll] Version 1.0
==================================================
[DeathToll] Log file: Zomboid/Lua/discord_events.log
[DeathToll] Events: Death, Level-Up, Character Creation, Login, Sunrise/Sunset, Daily Reports
[DeathToll] Initialization complete!
==================================================
```

### Step 4: Verify Log File Creation

The log file should be created at:

**For G-Portal (Your Setup):**
```
/Zomboid/Lua/discord_events.log
```

**For Other Setups:**
- **Windows:** `C:\Users\[USERNAME]\Zomboid\Server\[SERVER_NAME]\Lua\discord_events.log`
- **Linux:** `/home/[USERNAME]/Zomboid/Server/[SERVER_NAME]/Lua/discord_events.log`

**Note:** The `/Lua/` folder and log file may not exist until the first event occurs!

### Step 5: Update Python Script Configuration

In your Python script's environment variables, set:

```bash
# For G-Portal FTP access:
DISCORD_LOG_PATH='/Lua/discord_events.log'

# The path is relative to your FTP root, which is /Zomboid/
```

If the path doesn't work, try these alternatives:
```bash
DISCORD_LOG_PATH='/Zomboid/Lua/discord_events.log'
# or
DISCORD_LOG_PATH='Lua/discord_events.log'
```

Test by checking if your FTP client can navigate to and see the file!

### Step 3: Trigger Test Event

1. **Join the server**
2. **Kill your character** (or gain a skill level)
3. **Check the log file** for a JSON entry

**Expected log entry:**
```json
{"timestamp":"2025-01-15 14:30:45","type":"death","data":{"username":"YourName","steam_id":"76561198012345678","hours_survived":0.5,"x":10500,"y":9000,"z":0,"skills":"Aiming=1"}}
```

## 🔧 Configuration

### Adjust Sunrise/Sunset Thresholds

Edit `DeathToll.lua` if sunrise/sunset triggers at wrong times:

```lua
DeathToll.SUNRISE_THRESHOLD = 0.3  -- Increase if triggering too early
DeathToll.SUNSET_THRESHOLD = 0.2   -- Decrease if triggering too late
```

### Change Event Cooldown

Prevent spam by adjusting cooldown (default: 1 hour):

```lua
DeathToll.EVENT_COOLDOWN = 3600  -- In game ticks (1 tick = ~1 second)
```

### Modify Check Frequency

Day/night checks happen every 10 game minutes by default. To change:

```lua
-- In DeathToll.init(), change:
Events.EveryTenMinutes.Add(DeathToll.checkDayNightCycle)

-- To one of:
Events.EveryOneMinute.Add(DeathToll.checkDayNightCycle)
Events.EveryHours.Add(DeathToll.checkDayNightCycle)
Events.EveryDays.Add(DeathToll.checkDayNightCycle)
```

## 🐛 Troubleshooting

### Issue: Mod not loading

**Check:**
- [ ] Folder structure is correct (DeathToll/media/lua/server/)
- [ ] File is named exactly `DeathToll.lua` (case-sensitive on Linux)
- [ ] `-mod=DeathToll` is in server startup command
- [ ] No syntax errors in Lua file

**Debug:**
```bash
# Check server console for error messages
# Look for lines starting with [DeathToll]
```

### Issue: Log file not created

**Check:**
- [ ] Server has write permissions to Lua folder
- [ ] At least one event has occurred (death, login, etc.)
- [ ] Check server console for "[DeathToll] ERROR: Could not open log file"

**Fix:**
```bash
# Manually create Lua directory if it doesn't exist
mkdir -p ~/Zomboid/Server/[SERVER_NAME]/Lua

# Set permissions (Linux)
chmod 755 ~/Zomboid/Server/[SERVER_NAME]/Lua
```

### Issue: Events not logging

**Check:**
- [ ] Mod initialization message appeared in console
- [ ] You're triggering events on the server (not singleplayer)
- [ ] Player is actually on the server (not main menu)

**Test manually:**
```lua
-- Add to DeathToll.init() for testing:
DeathToll.writeEvent("test", {message = "Mod is working!"})
```

### Issue: Sunrise/Sunset not triggering

**Possible causes:**
- Server time is not progressing (paused or frozen)
- Threshold values need adjustment
- Server hasn't been running long enough for a full day cycle

**Debug:**
```lua
-- Add to DeathToll.checkDayNightCycle():
print(string.format("[DeathToll] Light level: %.3f", lightLevel))
```

### Issue: JSON parsing errors in Python

**Check log file format:**
```bash
# View log file
cat ~/Zomboid/Server/[SERVER_NAME]/Lua/discord_events.log

# Check for malformed JSON
python -m json.tool discord_events.log
```

**Common issues:**
- Player names with special characters (quotes, backslashes)
- Very long skill lists
- Corrupted file (delete and let mod recreate)

## 📊 Understanding the Log Format

### Event Structure
```json
{
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "type": "event_type",
  "data": {
    // Event-specific data
  }
}
```

### Event Types

#### Death Event
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

#### Level Up Event
```json
{
  "timestamp": "2025-01-15 15:00:00",
  "type": "level_up",
  "data": {
    "username": "Player1",
    "steam_id": "76561198012345678",
    "skill": "Aiming",
    "level": 6,
    "hours_survived": 25.0
  }
}
```

#### Character Created Event
```json
{
  "timestamp": "2025-01-15 15:30:00",
  "type": "character_created",
  "data": {
    "username": "Player1",
    "steam_id": "76561198012345678",
    "character_index": 0,
    "x": 10600,
    "y": 9100,
    "z": 0
  }
}
```

#### Login Event
```json
{
  "timestamp": "2025-01-15 16:00:00",
  "type": "login",
  "data": {
    "username": "Player1",
    "steam_id": "76561198012345678",
    "hours_survived": 25.5,
    "skills": "Aiming=6,Fitness=3,Strength=2,Cooking=2"
  }
}
```

#### Sunrise Event
```json
{
  "timestamp": "2025-01-15 06:00:00",
  "type": "sunrise",
  "data": {
    "game_time": 0.25,
    "light_level": 0.35,
    "game_day": 5
  }
}
```

#### Sunset Event
```json
{
  "timestamp": "2025-01-15 18:00:00",
  "type": "sunset",
  "data": {
    "game_time": 0.75,
    "light_level": 0.15,
    "game_day": 5
  }
}
```

#### Daily Survivors Event
```json
{
  "timestamp": "2025-01-15 06:00:05",
  "type": "daily_survivors",
  "data": {
    "game_day": 5,
    "survivor_count": 3,
    "survivors": [
      {"username": "Player1", "hours": 25.5, "x": 10500, "y": 9000, "z": 0},
      {"username": "Player2", "hours": 18.0, "x": 10600, "y": 9100, "z": 0},
      {"username": "Player3", "hours": 12.0, "x": 10700, "y": 9200, "z": 0}
    ]
  }
}
```

## 🔒 Security Notes

- **No passwords or sensitive data** are logged
- **Steam IDs are public** information and safe to log
- **Player locations** are game coordinates (not real-world)
- **Log file** should not be publicly accessible (configure FTP carefully)

## 📈 Performance Impact

- **Minimal** - Only writes to file on events
- **File size** - Approximately 200-500 bytes per event
- **Growth rate** - Depends on server activity
  - Small server (5 players): ~1-2 MB/week
  - Large server (50 players): ~10-20 MB/week

**Log rotation recommendation:**
- Implement in Python script
- Or use Linux logrotate
- Or manually archive/delete old logs

## 🎯 Next Steps

1. ✅ Install mod on server
2. ✅ Verify log file creation
3. ✅ Update Python script `DISCORD_LOG_PATH` environment variable
4. ✅ Run Python script
5. ✅ Test with a death or login
6. ✅ Enjoy automated Discord notifications!

## 📝 Version History

**v1.0** (Current)
- Initial release
- Death tracking
- Level-up tracking
- Character creation tracking
- Login tracking
- Sunrise/sunset detection
- Daily survivor reports

**Future planned features:**
- Admin commands for manual leaderboard requests
- Configurable event cooldowns
- Custom event filtering
- Performance optimizations

---

**Need help? Check the main implementation guide or create an issue!** 🚀
