import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from io import BytesIO

# Import the main module (assuming it's named main.py)
import main


class TestHelperFunctions(unittest.TestCase):
    """Test utility and helper functions"""
    
    def test_format_time_hours_only(self):
        """Test formatting hours when less than a day"""
        result = main.format_time(5.5)
        self.assertEqual(result, "5 hours")
    
    def test_format_time_single_hour(self):
        """Test singular 'hour' formatting"""
        result = main.format_time(1.0)
        self.assertEqual(result, "1 hour")
    
    def test_format_time_days_and_hours(self):
        """Test formatting with both days and hours"""
        result = main.format_time(25.0)  # 1 day, 1 hour
        self.assertEqual(result, "1 day, 1 hour")
    
    def test_format_time_multiple_days(self):
        """Test formatting with multiple days"""
        result = main.format_time(50.5)  # 2 days, 2 hours
        self.assertEqual(result, "2 days, 2 hours")
    
    def test_get_death_ordinal_first(self):
        """Test 1st ordinal"""
        self.assertEqual(main.get_death_ordinal(1), "1st")
    
    def test_get_death_ordinal_second(self):
        """Test 2nd ordinal"""
        self.assertEqual(main.get_death_ordinal(2), "2nd")
    
    def test_get_death_ordinal_third(self):
        """Test 3rd ordinal"""
        self.assertEqual(main.get_death_ordinal(3), "3rd")
    
    def test_get_death_ordinal_fourth(self):
        """Test 4th ordinal"""
        self.assertEqual(main.get_death_ordinal(4), "4th")
    
    def test_get_death_ordinal_teens(self):
        """Test teen ordinals (11th, 12th, 13th)"""
        self.assertEqual(main.get_death_ordinal(11), "11th")
        self.assertEqual(main.get_death_ordinal(12), "12th")
        self.assertEqual(main.get_death_ordinal(13), "13th")
    
    def test_get_death_ordinal_twenty_first(self):
        """Test 21st ordinal"""
        self.assertEqual(main.get_death_ordinal(21), "21st")
    
    def test_get_death_emoji(self):
        """Test death emoji selection"""
        self.assertEqual(main.get_death_emoji(1), "💀")
        self.assertEqual(main.get_death_emoji(2), "☠️")
        self.assertEqual(main.get_death_emoji(5), "⚰️")
        self.assertEqual(main.get_death_emoji(8), "👻")
        self.assertEqual(main.get_death_emoji(15), "🏴‍☠️")
    
    def test_parse_skills_string_empty(self):
        """Test parsing empty skills string"""
        result = main.parse_skills_string("")
        self.assertEqual(result, {})
    
    def test_parse_skills_string_single_skill(self):
        """Test parsing single skill"""
        result = main.parse_skills_string("Aiming=5")
        self.assertEqual(result, {"Aiming": 5})
    
    def test_parse_skills_string_multiple_skills(self):
        """Test parsing multiple skills"""
        result = main.parse_skills_string("Aiming=5,Fitness=3,Strength=2")
        self.assertEqual(result, {
            "Aiming": 5,
            "Fitness": 3,
            "Strength": 2
        })
    
    def test_parse_skills_string_with_spaces(self):
        """Test parsing skills with extra spaces"""
        result = main.parse_skills_string("Aiming = 5 , Fitness = 3")
        self.assertEqual(result, {
            "Aiming": 5,
            "Fitness": 3
        })


class TestPlayerInitialization(unittest.TestCase):
    """Test player initialization and stats management"""
    
    def setUp(self):
        """Reset player stats before each test"""
        main.player_stats = {}
    
    def test_init_player_new(self):
        """Test initializing a new player"""
        main.init_player("TestPlayer", "12345")
        
        self.assertIn("TestPlayer", main.player_stats)
        player = main.player_stats["TestPlayer"]
        
        self.assertEqual(player['steam_id'], "12345")
        self.assertEqual(player['total_deaths'], 0)
        self.assertEqual(player['total_respawns'], 0)
        self.assertFalse(player['current_character']['alive'])
    
    def test_init_player_existing(self):
        """Test that init_player doesn't overwrite existing player"""
        main.init_player("TestPlayer", "12345")
        main.player_stats["TestPlayer"]['total_deaths'] = 5
        
        main.init_player("TestPlayer", "12345")
        
        # Should still have 5 deaths, not reset to 0
        self.assertEqual(main.player_stats["TestPlayer"]['total_deaths'], 5)


class TestEventHandlers(unittest.TestCase):
    """Test event handling functions"""
    
    def setUp(self):
        """Reset player stats and unsaved changes before each test"""
        main.player_stats = {}
        main.unsaved_changes = False
    
    @patch('main.send_death_notification')
    def test_handle_death_event(self, mock_send):
        """Test handling a death event"""
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'hours_survived': 24.5,
            'x': 100,
            'y': 200,
            'z': 0,
            'skills': 'Aiming=5,Fitness=3'
        }
        
        main.handle_death_event(event_data)
        
        player = main.player_stats['TestPlayer']
        self.assertEqual(player['total_deaths'], 1)
        self.assertFalse(player['current_character']['alive'])
        self.assertEqual(player['current_character']['hours_survived'], 24.5)
        self.assertEqual(player['lifetime_stats']['total_hours_survived'], 24.5)
        self.assertEqual(player['lifetime_stats']['longest_survival'], 24.5)
        self.assertTrue(main.unsaved_changes)
        mock_send.assert_called_once()
    
    def test_handle_death_event_updates_longest_survival(self):
        """Test that death event updates longest survival correctly"""
        # First death
        main.handle_death_event({
            'username': 'TestPlayer',
            'steam_id': '12345',
            'hours_survived': 10.0,
            'x': 100, 'y': 200, 'z': 0,
            'skills': ''
        })
        
        # Second death with longer survival
        main.handle_death_event({
            'username': 'TestPlayer',
            'steam_id': '12345',
            'hours_survived': 25.0,
            'x': 100, 'y': 200, 'z': 0,
            'skills': ''
        })
        
        player = main.player_stats['TestPlayer']
        self.assertEqual(player['total_deaths'], 2)
        self.assertEqual(player['lifetime_stats']['longest_survival'], 25.0)
        self.assertEqual(player['lifetime_stats']['total_hours_survived'], 35.0)
    
    @patch('main.send_respawn_notification')
    def test_handle_spawn_event(self, mock_send):
        """Test handling a spawn event"""
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'x': 100,
            'y': 200,
            'z': 0
        }
        
        main.handle_spawn_event(event_data)
        
        player = main.player_stats['TestPlayer']
        self.assertEqual(player['total_respawns'], 1)
        self.assertTrue(player['current_character']['alive'])
        self.assertEqual(player['current_character']['hours_survived'], 0)
        self.assertTrue(main.unsaved_changes)
        mock_send.assert_called_once()
    
    @patch('main.send_skill_notification')
    def test_handle_level_up_event_milestone(self, mock_send):
        """Test handling a level up event at milestone"""
        main.SKILL_NOTIFICATIONS = 'milestones'
        
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'skill': 'Aiming',
            'level': 5,
            'hours_survived': 10.0
        }
        
        main.handle_level_up_event(event_data)
        
        player = main.player_stats['TestPlayer']
        self.assertEqual(player['current_character']['skills']['Aiming'], 5)
        self.assertEqual(player['lifetime_stats']['skill_milestones']['Aiming'], 5)
        self.assertTrue(main.unsaved_changes)
        mock_send.assert_called_once()
    
    @patch('main.send_skill_notification')
    def test_handle_level_up_event_non_milestone(self, mock_send):
        """Test that non-milestone levels don't send notifications"""
        main.SKILL_NOTIFICATIONS = 'milestones'
        
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'skill': 'Aiming',
            'level': 3,
            'hours_survived': 5.0
        }
        
        main.handle_level_up_event(event_data)
        
        player = main.player_stats['TestPlayer']
        self.assertEqual(player['current_character']['skills']['Aiming'], 3)
        mock_send.assert_not_called()
    
    @patch('main.send_skill_notification')
    def test_handle_level_up_event_all_mode(self, mock_send):
        """Test that 'all' mode sends notification for any level"""
        main.SKILL_NOTIFICATIONS = 'all'
        
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'skill': 'Aiming',
            'level': 3,
            'hours_survived': 5.0
        }
        
        main.handle_level_up_event(event_data)
        
        mock_send.assert_called_once()
    
    def test_handle_login_event(self):
        """Test handling a login event"""
        event_data = {
            'username': 'TestPlayer',
            'steam_id': '12345',
            'hours_survived': 15.0,
            'skills': 'Aiming=5,Fitness=3'
        }
        
        main.handle_login_event(event_data)
        
        player = main.player_stats['TestPlayer']
        self.assertTrue(player['current_character']['alive'])
        self.assertEqual(player['current_character']['hours_survived'], 15.0)
        self.assertEqual(player['current_character']['skills']['Aiming'], 5)
        self.assertTrue(main.unsaved_changes)


class TestDiscordEventRouting(unittest.TestCase):
    """Test event routing from mod events"""
    
    def setUp(self):
        main.player_stats = {}
    
    @patch('main.handle_death_event')
    def test_handle_discord_event_death(self, mock_handler):
        """Test routing death events"""
        event = {
            'type': 'death',
            'data': {
                'username': 'TestPlayer',
                'steam_id': '12345',
                'hours_survived': 24.5,
                'x': 100,
                'y': 200,
                'z': 0,
                'skills': 'Aiming=5'
            }
        }
        
        main.handle_discord_event(event)
        mock_handler.assert_called_once()
    
    @patch('main.handle_level_up_event')
    def test_handle_discord_event_level_up(self, mock_handler):
        """Test routing level up events"""
        event = {
            'type': 'level_up',
            'data': {
                'username': 'TestPlayer',
                'steam_id': '12345',
                'skill': 'Aiming',
                'level': 5,
                'hours_survived': 10.0
            }
        }
        
        main.handle_discord_event(event)
        mock_handler.assert_called_once()
    
    @patch('main.send_sunrise_notification')
    def test_handle_discord_event_sunrise(self, mock_send):
        """Test routing sunrise events"""
        event = {
            'type': 'sunrise',
            'data': {
                'game_day': 5,
                'light_level': 0.35
            }
        }
        
        main.handle_discord_event(event)
        mock_send.assert_called_once_with({'game_day': 5, 'light_level': 0.35})
    
    @patch('main.send_daily_survivor_report')
    def test_handle_discord_event_daily_survivors(self, mock_send):
        """Test routing daily survivor report events"""
        event = {
            'type': 'daily_survivors',
            'data': {
                'game_day': 5,
                'survivor_count': 3,
                'survivors': [
                    {'username': 'Player1', 'hours': 24, 'x': 100, 'y': 200, 'z': 0},
                    {'username': 'Player2', 'hours': 12, 'x': 150, 'y': 250, 'z': 0}
                ]
            }
        }
        
        main.handle_discord_event(event)
        mock_send.assert_called_once()


class TestStatsFilePersistence(unittest.TestCase):
    """Test saving and loading player stats"""
    
    def setUp(self):
        """Create a temporary file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_filename = self.temp_file.name
        self.temp_file.close()
        main.PLAYER_STATS_FILE = self.temp_filename
        main.player_stats = {}
        main.file_positions = {}
    
    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_save_and_load_player_stats(self):
        """Test saving and loading player stats"""
        # Create some test data
        main.player_stats = {
            'TestPlayer': {
                'steam_id': '12345',
                'total_deaths': 5,
                'total_respawns': 6,
                'current_character': {
                    'alive': True,
                    'hours_survived': 10.5,
                    'skills': {'Aiming': 5}
                },
                'lifetime_stats': {
                    'total_hours_survived': 50.0,
                    'longest_survival': 15.0
                }
            }
        }
        main.file_positions = {'/Lua/discord_events.log': 1024}
        
        # Save
        main.save_player_stats()
        
        # Clear memory
        main.player_stats = {}
        main.file_positions = {}
        
        # Load
        main.load_player_stats()
        
        # Verify
        self.assertIn('TestPlayer', main.player_stats)
        self.assertEqual(main.player_stats['TestPlayer']['total_deaths'], 5)
        self.assertEqual(main.file_positions['/Lua/discord_events.log'], 1024)
    
    def test_load_player_stats_missing_file(self):
        """Test loading when file doesn't exist"""
        main.PLAYER_STATS_FILE = 'nonexistent_file.json'
        main.load_player_stats()
        
        # Should initialize empty
        self.assertEqual(main.player_stats, {})
        self.assertEqual(main.file_positions, {})


class TestDiscordNotifications(unittest.TestCase):
    """Test Discord notification formatting"""
    
    def setUp(self):
        main.player_stats = {}
        main.init_player("TestPlayer", "12345")
    
    @patch('main.send_discord_notification')
    def test_send_death_notification_first_death(self, mock_send):
        """Test death notification for first death"""
        main.player_stats['TestPlayer']['total_deaths'] = 1
        main.player_stats['TestPlayer']['lifetime_stats']['longest_survival'] = 24.5
        
        result = main.send_death_notification("TestPlayer", 24.5, "(100, 200, 0)", "Aiming=5")
        
        # Check that notification was sent
        mock_send.assert_called_once()
        
        # Check embed structure
        call_args = mock_send.call_args[0][0]
        self.assertIn("1st time", call_args['title'])
        self.assertEqual(call_args['color'], 0xFF0000)  # Red for first death
    
    @patch('main.send_discord_notification')
    def test_send_respawn_notification(self, mock_send):
        """Test respawn notification"""
        main.player_stats['TestPlayer']['total_deaths'] = 3
        main.player_stats['TestPlayer']['lifetime_stats']['total_hours_survived'] = 60.0
        
        result = main.send_respawn_notification("TestPlayer", 4)
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("back in the game", call_args['title'])
        self.assertEqual(call_args['color'], 0x00FF00)
    
    @patch('main.send_discord_notification')
    def test_send_sunrise_notification(self, mock_send):
        """Test sunrise notification"""
        event_data = {
            'game_day': 5,
            'light_level': 0.35
        }
        
        result = main.send_sunrise_notification(event_data)
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("sun is rising", call_args['title'])
        self.assertIn("Day 6", call_args['description'])  # game_day + 1


class TestLeaderboards(unittest.TestCase):
    """Test leaderboard generation"""
    
    def setUp(self):
        main.player_stats = {
            'Player1': {
                'steam_id': '1',
                'total_deaths': 10,
                'total_respawns': 11,
                'current_character': {'alive': True, 'skills': {'Aiming': 8}},
                'lifetime_stats': {
                    'total_hours_survived': 100.0,
                    'longest_survival': 25.0,
                    'skill_milestones': {'Aiming': 8}
                }
            },
            'Player2': {
                'steam_id': '2',
                'total_deaths': 5,
                'total_respawns': 6,
                'current_character': {'alive': False, 'skills': {}},
                'lifetime_stats': {
                    'total_hours_survived': 50.0,
                    'longest_survival': 15.0,
                    'skill_milestones': {'Aiming': 5}
                }
            },
            'Player3': {
                'steam_id': '3',
                'total_deaths': 15,
                'total_respawns': 16,
                'current_character': {'alive': True, 'skills': {'Aiming': 3}},
                'lifetime_stats': {
                    'total_hours_survived': 150.0,
                    'longest_survival': 30.0,
                    'skill_milestones': {'Aiming': 10}
                }
            }
        }
    
    @patch('main.send_discord_notification')
    def test_send_leaderboard_death(self, mock_send):
        """Test death leaderboard"""
        main.send_leaderboard("death")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("Death Leaderboard", call_args['title'])
        
        # Player3 should be first (15 deaths)
        description = call_args['description']
        self.assertIn("Player3", description)
    
    @patch('main.send_discord_notification')
    def test_send_leaderboard_survival(self, mock_send):
        """Test survival leaderboard"""
        main.send_leaderboard("survival")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("Longest Survival", call_args['title'])
        
        # Player3 should be first (30 hours)
        description = call_args['description']
        self.assertIn("Player3", description)
    
    @patch('main.send_discord_notification')
    def test_send_leaderboard_hours(self, mock_send):
        """Test total hours leaderboard"""
        main.send_leaderboard("hours")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("Most Experienced", call_args['title'])
    
    @patch('main.send_discord_notification')
    def test_send_leaderboard_skill(self, mock_send):
        """Test skill-specific leaderboard"""
        main.send_leaderboard("skill_Aiming")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertIn("Aiming", call_args['title'])


class TestFTPOperations(unittest.TestCase):
    """Test FTP download operations"""
    
    @patch('ftplib.FTP')
    def test_download_log_tail_new_content(self, mock_ftp_class):
        """Test downloading new content from log file"""
        mock_ftp = MagicMock()
        mock_ftp.size.return_value = 1024
        
        # Mock the retrbinary call to write test data
        test_content = b'{"type":"death","data":{}}\n'
        def mock_retrbinary(cmd, callback, rest=0):
            callback(test_content)
        mock_ftp.retrbinary = mock_retrbinary
        
        content, new_pos = main.download_log_tail(mock_ftp, '/test.log', 0)
        
        self.assertIsNotNone(content)
        self.assertEqual(new_pos, 1024)
    
    @patch('ftplib.FTP')
    def test_download_log_tail_no_new_content(self, mock_ftp_class):
        """Test when file hasn't changed"""
        mock_ftp = MagicMock()
        mock_ftp.size.return_value = 1024
        
        content, new_pos = main.download_log_tail(mock_ftp, '/test.log', 1024)
        
        self.assertEqual(content, "")
        self.assertEqual(new_pos, 1024)
    
    @patch('ftplib.FTP')
    def test_download_log_tail_file_rotated(self, mock_ftp_class):
        """Test when file was rotated (new file is smaller)"""
        mock_ftp = MagicMock()
        mock_ftp.size.return_value = 512
        
        test_content = b'{"type":"death","data":{}}\n'
        def mock_retrbinary(cmd, callback, rest=0):
            callback(test_content)
        mock_ftp.retrbinary = mock_retrbinary
        
        # Previous position was 1024, but file is now only 512
        content, new_pos = main.download_log_tail(mock_ftp, '/test.log', 1024)
        
        # Should start from beginning
        self.assertIsNotNone(content)
        self.assertEqual(new_pos, 512)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
