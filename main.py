import os
import time
import ftplib
import requests
import json
from datetime import datetime
from io import BytesIO

# Configuration - Set these as environment variables
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
FTP_HOST = os.getenv('FTP_HOST')
FTP_PORT = int(os.getenv('FTP_PORT', '34231'))
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')
DISCORD_LOG_PATH = os.getenv('DISCORD_LOG_PATH', '/Lua/discord_events.log')  # Path to mod's log file
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))  # 10 seconds for near real-time
SKILL_NOTIFICATIONS = os.getenv('SKILL_NOTIFICATIONS', 'milestones')  # 'all', 'milestones', or 'none'
PLAYER_STATS_FILE = 'player_stats.json'

# Track last processed position per file
file_positions = {}
last_events = set()  # Prevent duplicate notifications
player_stats = {}  # Complete player statistics
unsaved_changes = False  # Track if we have unsaved data

# Skill milestone levels (for notifications)
SKILL_MILESTONES = [5, 10]

def load_player_stats():
    """Load player statistics from file"""
    global player_stats, file_positions
    try:
        if os.path.exists(PLAYER_STATS_FILE):
            with open(PLAYER_STATS_FILE, 'r') as f:
                data = json.load(f)
                player_stats = data.get('player_stats', {})
                file_positions = data.get('file_positions', {})
            print(f"✓ Loaded stats for {len(player_stats)} players")
    except Exception as e:
        print(f"⚠️ Could not load player stats: {e}")
        player_stats = {}
        file_positions = {}

def save_player_stats():
    """Save player statistics to file"""
    global unsaved_changes
    try:
        with open(PLAYER_STATS_FILE, 'w') as f:
            json.dump({
                'player_stats': player_stats,
                'file_positions': file_positions
            }, f, indent=2)
        unsaved_changes = False
        print("💾 Stats saved")
    except Exception as e:
        print(f"⚠️ Could not save player stats: {e}")

def init_player(username, steam_id):
    """Initialize a new player in the stats system"""
    if username not in player_stats:
        player_stats[username] = {
            'steam_id': steam_id,
            'total_deaths': 0,
            'total_respawns': 0,
            'current_character': {
                'alive': False,
                'spawn_time': None,
                'hours_survived': 0,
                'last_location': [0, 0, 0],
                'skills': {}
            },
            'lifetime_stats': {
                'total_hours_survived': 0,
                'longest_survival': 0,
                'skill_milestones': {}
            }
        }

def format_time(hours):
    """Convert hours to readable format (X days, Y hours)"""
    days = int(hours // 24)
    remaining_hours = int(hours % 24)
    
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}, {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
    else:
        return f"{remaining_hours} hour{'s' if remaining_hours != 1 else ''}"

def get_death_ordinal(count):
    """Convert death count to ordinal (1st, 2nd, 3rd, etc.)"""
    if 10 <= count % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(count % 10, 'th')
    return f"{count}{suffix}"

def get_death_emoji(count):
    """Get emoji based on death count"""
    if count == 1:
        return "💀"
    elif count <= 3:
        return "☠️"
    elif count <= 5:
        return "⚰️"
    elif count <= 10:
        return "👻"
    else:
        return "🏴‍☠️"

def send_discord_notification(embed_data):
    """Generic function to send any embed to Discord"""
    payload = {
        "username": "Zomboid Stats Tracker",
        "embeds": [embed_data]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"✗ Discord notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error sending notification: {e}")
        return False

def parse_skills_string(skills_str):
    """Parse skill string from mod (format: 'Skill1=5,Skill2=3')"""
    skills = {}
    if not skills_str:
        return skills
    
    skill_pairs = skills_str.split(',')
    for pair in skill_pairs:
        if '=' in pair:
            skill, level = pair.split('=')
            skills[skill.strip()] = int(level.strip())
    return skills

def send_death_notification(username, hours_survived, coordinates, skills_str):
    """Send enhanced death notification"""
    player = player_stats[username]
    death_count = player['total_deaths']
    
    ordinal = get_death_ordinal(death_count)
    emoji = get_death_emoji(death_count)
    
    # Parse and get top skills
    skills = parse_skills_string(skills_str)
    top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:3]
    top_skills_text = ", ".join([f"{skill} {level}" for skill, level in top_skills if level > 0])
    
    # Build description
    details = []
    details.append(f"⏱️ **Survived:** {format_time(hours_survived)}")
    details.append(f"📍 **Location:** {coordinates}")
    if top_skills_text:
        details.append(f"🎯 **Peak Skills:** {top_skills_text}")
    details.append("")
    details.append(f"**Total Deaths:** {death_count}")
    details.append(f"**Longest Survival:** {format_time(player['lifetime_stats']['longest_survival'])}")
    
    # Choose color based on death count
    if death_count == 1:
        color = 0xFF0000
    elif death_count <= 3:
        color = 0xFF6600
    elif death_count <= 5:
        color = 0xFF9900
    elif death_count <= 10:
        color = 0xFFCC00
    else:
        color = 0x990000
    
    embed = {
        "title": f"{emoji} {username} has died for the {ordinal} time!",
        "description": "\n".join(details),
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Rest in pieces 💀"}
    }
    
    return send_discord_notification(embed)

def send_respawn_notification(username, character_num):
    """Send respawn notification"""
    player = player_stats[username]
    
    details = []
    details.append(f"💀 **Death Count:** {player['total_deaths']}")
    if player['total_deaths'] > 0:
        avg_survival = player['lifetime_stats']['total_hours_survived'] / player['total_deaths']
        details.append(f"📊 **Average Survival:** {format_time(avg_survival)}")
    details.append(f"🎮 **Character #{character_num}**")
    
    embed = {
        "title": f"🔄 {username} is back in the game!",
        "description": "\n".join(details),
        "color": 0x00FF00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Good luck out there!"}
    }
    
    return send_discord_notification(embed)

def send_skill_notification(username, skill, level, hours_survived):
    """Send skill level-up notification"""
    embed = {
        "title": f"🎉 {username} leveled up!",
        "description": f"**{skill}** reached level **{level}**\n⏱️ After {format_time(hours_survived)} survived",
        "color": 0xFFD700,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Keep grinding! 💪"}
    }
    
    return send_discord_notification(embed)

def send_sunrise_notification(event_data):
    """Send sunrise notification"""
    game_day = event_data.get('game_day', 0)
    light_level = event_data.get('light_level', 0)
    
    embed = {
        "title": "🌅 The sun is rising...",
        "description": f"**Day {game_day + 1}** begins.\n\n🔆 Light Level: {light_level:.2f}\n\nStay alert. Stay alive.",
        "color": 0xFFD700,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Good morning, survivor"}
    }
    
    return send_discord_notification(embed)

def send_sunset_notification(event_data):
    """Send sunset notification"""
    game_day = event_data.get('game_day', 0)
    light_level = event_data.get('light_level', 0)
    
    embed = {
        "title": "🌙 Darkness falls...",
        "description": f"**Night {game_day + 1}** approaches.\n\n🌑 Light Level: {light_level:.2f}\n\nThe dead are more dangerous in the dark.",
        "color": 0x191970,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Stay safe out there"}
    }
    
    return send_discord_notification(embed)

def send_daily_survivor_report(event_data):
    """Send daily report of all active survivors at sunrise"""
    survivors = event_data.get('survivors', [])
    game_day = event_data.get('game_day', 0)
    
    if not survivors:
        return
    
    # Sort by hours survived (descending)
    survivors.sort(key=lambda s: s.get('hours', 0), reverse=True)
    
    lines = []
    lines.append(f"**☀️ Day {game_day + 1} Dawn Report**\n")
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, survivor in enumerate(survivors[:15]):
        username = survivor.get('username', 'Unknown')
        hours = survivor.get('hours', 0)
        location = f"({survivor.get('x', 0)}, {survivor.get('y', 0)}, {survivor.get('z', 0)})"
        
        medal = medals[i] if i < 3 else f"**{i+1}.**"
        lines.append(f"{medal} **{username}** - {format_time(hours)}")
        if i < 5:
            lines.append(f"      📍 {location}")
    
    if len(survivors) > 15:
        lines.append(f"\n*...and {len(survivors) - 15} more survivors*")
    
    embed = {
        "title": "🌅 Daily Survivor Status Report",
        "description": "\n".join(lines),
        "color": 0x00FF00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"Total survivors currently online: {len(survivors)}"}
    }
    
    return send_discord_notification(embed)

def send_leaderboard(leaderboard_type="death"):
    """Send various leaderboards to Discord"""
    if not player_stats:
        return
    
    if leaderboard_type == "death":
        sorted_players = sorted(
            [(name, data) for name, data in player_stats.items() if data['total_deaths'] > 0],
            key=lambda x: x[1]['total_deaths'],
            reverse=True
        )[:10]
        
        if not sorted_players:
            return
        
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (name, data) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            deaths = data['total_deaths']
            avg = data['lifetime_stats']['total_hours_survived'] / deaths if deaths > 0 else 0
            lines.append(f"{medal} {name}: **{deaths}** death{'s' if deaths != 1 else ''} (avg: {format_time(avg)})")
        
        embed = {
            "title": "💀 Death Leaderboard 💀",
            "description": "\n".join(lines),
            "color": 0x9900FF,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"Total tracked players: {len(player_stats)}"}
        }
    
    elif leaderboard_type == "survival":
        sorted_players = sorted(
            [(name, data) for name, data in player_stats.items()],
            key=lambda x: x[1]['lifetime_stats']['longest_survival'],
            reverse=True
        )[:10]
        
        if not sorted_players:
            return
        
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (name, data) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            longest = data['lifetime_stats']['longest_survival']
            if longest == 0:
                continue
            alive_marker = " 🟢" if data['current_character']['alive'] else ""
            lines.append(f"{medal} {name}: {format_time(longest)}{alive_marker}")
        
        if not lines:
            return
        
        embed = {
            "title": "⏱️ Longest Survival Streaks ⏱️",
            "description": "\n".join(lines) + "\n\n🟢 = Currently Alive",
            "color": 0x00BFFF,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Survival of the fittest!"}
        }
    
    elif leaderboard_type == "hours":
        sorted_players = sorted(
            [(name, data) for name, data in player_stats.items() if data['lifetime_stats']['total_hours_survived'] > 0],
            key=lambda x: x[1]['lifetime_stats']['total_hours_survived'],
            reverse=True
        )[:10]
        
        if not sorted_players:
            return
        
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (name, data) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            total_hours = data['lifetime_stats']['total_hours_survived']
            lines.append(f"{medal} {name}: {format_time(total_hours)}")
        
        embed = {
            "title": "🏆 Most Experienced Survivors 🏆",
            "description": "\n".join(lines),
            "color": 0xFFD700,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Total playtime across all lives"}
        }
    
    elif leaderboard_type.startswith("skill_"):
        skill_name = leaderboard_type.replace("skill_", "")
        
        players_with_skill = []
        for name, data in player_stats.items():
            if data['current_character']['alive']:
                skill_level = data['current_character']['skills'].get(skill_name, 0)
                if skill_level > 0:
                    players_with_skill.append((name, skill_level))
            
            milestone = data['lifetime_stats']['skill_milestones'].get(skill_name, 0)
            if milestone > 0 and not data['current_character']['alive']:
                players_with_skill.append((name, milestone))
        
        if not players_with_skill:
            return
        
        sorted_players = sorted(players_with_skill, key=lambda x: x[1], reverse=True)[:10]
        
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (name, level) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            lines.append(f"{medal} {name}: Level **{level}**")
        
        skill_emoji = {
            "Aiming": "🎯",
            "Fitness": "💪",
            "Strength": "🏋️",
            "Cooking": "🍳",
            "Farming": "🌾",
            "Mechanics": "🔧",
            "Carpentry": "🔨"
        }
        
        emoji = skill_emoji.get(skill_name, "📊")
        
        embed = {
            "title": f"{emoji} Top {skill_name} Masters {emoji}",
            "description": "\n".join(lines),
            "color": 0x1E90FF,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"Highest {skill_name} levels"}
        }
    
    return send_discord_notification(embed)

def handle_death_event(data):
    """Handle a player death event"""
    global unsaved_changes
    username = data.get('username')
    steam_id = data.get('steam_id')
    hours_survived = float(data.get('hours_survived', 0))
    x, y, z = data.get('x', 0), data.get('y', 0), data.get('z', 0)
    coordinates = f"({x}, {y}, {z})"
    skills_str = data.get('skills', '')
    
    init_player(username, steam_id)
    
    player = player_stats[username]
    player['total_deaths'] += 1
    player['current_character']['alive'] = False
    player['current_character']['hours_survived'] = hours_survived
    player['current_character']['last_location'] = [x, y, z]
    
    # Update skills from death event
    player['current_character']['skills'] = parse_skills_string(skills_str)
    
    # Update lifetime stats
    player['lifetime_stats']['total_hours_survived'] += hours_survived
    if hours_survived > player['lifetime_stats']['longest_survival']:
        player['lifetime_stats']['longest_survival'] = hours_survived
    
    unsaved_changes = True
    
    print(f"💀 Death: {username} survived {format_time(hours_survived)} (Death #{player['total_deaths']})")
    send_death_notification(username, hours_survived, coordinates, skills_str)

def handle_spawn_event(data):
    """Handle a new character spawn event"""
    global unsaved_changes
    username = data.get('username')
    steam_id = data.get('steam_id')
    x, y, z = data.get('x', 0), data.get('y', 0), data.get('z', 0)
    
    init_player(username, steam_id)
    
    player = player_stats[username]
    player['total_respawns'] += 1
    player['current_character'] = {
        'alive': True,
        'spawn_time': datetime.now().isoformat(),
        'hours_survived': 0,
        'last_location': [x, y, z],
        'skills': {}
    }
    
    unsaved_changes = True
    
    character_num = player['total_respawns']
    print(f"🔄 Respawn: {username} (Character #{character_num})")
    send_respawn_notification(username, character_num)

def handle_level_up_event(data):
    """Handle a skill level-up event"""
    global unsaved_changes
    username = data.get('username')
    steam_id = data.get('steam_id')
    skill = data.get('skill')
    level = int(data.get('level', 0))
    hours_survived = float(data.get('hours_survived', 0))
    
    init_player(username, steam_id)
    
    player = player_stats[username]
    player['current_character']['skills'][skill] = level
    player['current_character']['hours_survived'] = hours_survived
    
    # Update lifetime milestone if this is the highest they've reached
    current_milestone = player['lifetime_stats']['skill_milestones'].get(skill, 0)
    if level > current_milestone:
        player['lifetime_stats']['skill_milestones'][skill] = level
    
    unsaved_changes = True
    
    print(f"📈 Level Up: {username} - {skill} level {level}")
    
    # Send notification based on settings
    should_notify = False
    if SKILL_NOTIFICATIONS == 'all':
        should_notify = True
    elif SKILL_NOTIFICATIONS == 'milestones' and level in SKILL_MILESTONES:
        should_notify = True
    
    if should_notify:
        send_skill_notification(username, skill, level, hours_survived)

def handle_login_event(data):
    """Handle a player login event"""
    global unsaved_changes
    username = data.get('username')
    steam_id = data.get('steam_id')
    hours_survived = float(data.get('hours_survived', 0))
    skills_str = data.get('skills', '')
    
    init_player(username, steam_id)
    
    player = player_stats[username]
    player['current_character']['skills'] = parse_skills_string(skills_str)
    player['current_character']['alive'] = True
    player['current_character']['hours_survived'] = hours_survived
    
    unsaved_changes = True
    
    print(f"👋 Login: {username} ({format_time(hours_survived)} survived)")

def handle_discord_event(event):
    """Route events from mod to appropriate handlers"""
    event_type = event.get('type')
    data = event.get('data', {})
    
    if event_type == 'death':
        handle_death_event(data)
    
    elif event_type == 'level_up':
        handle_level_up_event(data)
    
    elif event_type == 'character_created':
        handle_spawn_event(data)
    
    elif event_type == 'login':
        handle_login_event(data)
    
    elif event_type == 'sunrise':
        print(f"🌅 Sunrise on day {data.get('game_day', 0) + 1}")
        send_sunrise_notification(data)
    
    elif event_type == 'sunset':
        print(f"🌙 Sunset on day {data.get('game_day', 0) + 1}")
        send_sunset_notification(data)
    
    elif event_type == 'daily_survivors':
        survivor_count = data.get('survivor_count', 0)
        print(f"📊 Daily report: {survivor_count} survivors online")
        send_daily_survivor_report(data)
    
    elif event_type == 'leaderboard_request':
        leaderboard_type = data.get('type', 'death')
        print(f"📋 Leaderboard requested: {leaderboard_type}")
        send_leaderboard(leaderboard_type)

def download_log_tail(ftp, log_path, from_position=0):
    """Download the log file from FTP starting from last position"""
    try:
        file_size = ftp.size(log_path)
        
        if file_size is None:
            return None, from_position
        
        if file_size < from_position:
            from_position = 0
            print(f"ℹ️ Log file rotated, starting from beginning")
        
        if file_size == from_position:
            return "", from_position
        
        buffer = BytesIO()
        ftp.retrbinary(f'RETR {log_path}', buffer.write, rest=from_position)
        
        content = buffer.getvalue().decode('utf-8', errors='ignore')
        new_position = file_size
        
        return content, new_position
        
    except Exception as e:
        print(f"✗ Error reading {log_path}: {e}")
        return None, from_position

def monitor_discord_events_log(ftp):
    """Monitor the discord_events.log file from the mod"""
    log_path = DISCORD_LOG_PATH
    
    try:
        last_pos = file_positions.get(log_path, 0)
        new_content, new_pos = download_log_tail(ftp, log_path, last_pos)
        
        if new_content:
            file_positions[log_path] = new_pos
            
            lines = new_content.split('\n')
            for line in lines:
                if not line.strip():
                    continue
                
                try:
                    event = json.loads(line.strip())
                    
                    # Create unique event ID
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('type', '')
                    
                    # For level_up, include more specific data in ID to avoid duplicates
                    if event_type == 'level_up':
                        username = event.get('data', {}).get('username', '')
                        skill = event.get('data', {}).get('skill', '')
                        level = event.get('data', {}).get('level', '')
                        event_id = f"{event_type}_{username}_{skill}_{level}_{timestamp}"
                    else:
                        event_id = f"{event_type}_{timestamp}"
                    
                    if event_id not in last_events:
                        last_events.add(event_id)
                        handle_discord_event(event)
                        
                        # Keep only last 1000 events in memory
                        if len(last_events) > 1000:
                            last_events = set(list(last_events)[-1000:])
                
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse event: {line[:100]}... Error: {e}")
                    continue
    
    except ftplib.error_perm as e:
        if "550" in str(e):
            # File not found - mod might not be installed yet or no events yet
            pass
        else:
            print(f"⚠️ FTP error: {e}")
    except Exception as e:
        print(f"⚠️ Error reading discord events log: {e}")

def monitor_server():
    """Main monitoring loop"""
    global unsaved_changes
    
    load_player_stats()
    
    print("=" * 60)
    print("🎮 Project Zomboid Discord Stats Tracker")
    print("=" * 60)
    print(f"📡 FTP Server: {FTP_HOST}:{FTP_PORT}")
    print(f"📁 Discord Log Path: {DISCORD_LOG_PATH}")
    print(f"⏱️  Check Interval: {CHECK_INTERVAL}s")
    print(f"💬 Discord Webhook: {DISCORD_WEBHOOK_URL[:40]}...")
    print(f"👥 Tracking: {len(player_stats)} players")
    print(f"🎯 Skill Notifications: {SKILL_NOTIFICATIONS}")
    print("=" * 60)
    print("\n🔍 Monitoring mod events...\n")
    
    consecutive_errors = 0
    max_errors = 5
    check_count = 0
    last_daily_leaderboard_date = None
    last_weekly_leaderboard_date = None
    
    while True:
        try:
            ftp = ftplib.FTP()
            ftp.connect(FTP_HOST, FTP_PORT, timeout=30)
            ftp.login(FTP_USER, FTP_PASS)
            
            # Monitor the mod's discord_events.log
            monitor_discord_events_log(ftp)
            
            ftp.quit()
            consecutive_errors = 0
            
            # Scheduled leaderboards
            current_time = datetime.now()
            current_date = current_time.date()
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_weekday = current_time.weekday()
            
            # Daily leaderboards at noon and midnight
            if current_minute == 0 and last_daily_leaderboard_date != current_date:
                if current_hour == 12 or current_hour == 0:
                    if player_stats:
                        print(f"\n📊 Sending scheduled {'noon' if current_hour == 12 else 'midnight'} leaderboards...")
                        send_leaderboard("death")
                        time.sleep(2)
                        send_leaderboard("survival")
                        time.sleep(2)
                        send_leaderboard("hours")
                        last_daily_leaderboard_date = current_date
            
            # Weekly skill leaderboards (Sunday at midnight)
            if current_weekday == 6 and current_hour == 0 and current_minute == 0:
                if last_weekly_leaderboard_date != current_date and player_stats:
                    print(f"\n📊 Sending weekly skill leaderboards...")
                    top_skills = ['Aiming', 'Fitness', 'Strength', 'Cooking', 'Mechanics']
                    for skill in top_skills:
                        send_leaderboard(f"skill_{skill}")
                        time.sleep(2)
                    last_weekly_leaderboard_date = current_date
            
            # Periodic save (every 20 checks, ~3 minutes at 10s interval)
            check_count += 1
            if check_count % 20 == 0 and unsaved_changes:
                save_player_stats()
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⛔ Stopping stats tracker...")
            if unsaved_changes:
                save_player_stats()
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"✗ Unexpected error: {e}")
            if consecutive_errors >= max_errors:
                print(f"⚠️ Too many consecutive errors ({max_errors}), waiting longer before retry...")
                time.sleep(CHECK_INTERVAL * 3)
                consecutive_errors = 0
            else:
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    required_vars = {
        'DISCORD_WEBHOOK_URL': DISCORD_WEBHOOK_URL,
        'FTP_HOST': FTP_HOST,
        'FTP_USER': FTP_USER,
        'FTP_PASS': FTP_PASS
    }
    
    missing_vars = [name for name, value in required_vars.items() if not value]
    
    if missing_vars:
        print("❌ ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before running.")
        print("\nExample:")
        print("  export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'")
        print("  export FTP_HOST='your.server.com'")
        print("  export FTP_USER='your_username'")
        print("  export FTP_PASS='your_password'")
        print("  export DISCORD_LOG_PATH='/Lua/discord_events.log'")
        exit(1)
    
    print("\n🚀 Starting Project Zomboid Discord Stats Tracker...")
    print("📝 Make sure your Discord Events mod is installed and enabled on the server!\n")
    
    monitor_server()
