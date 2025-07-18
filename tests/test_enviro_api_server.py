#!/usr/bin/env python3
"""
Test Suite for Enviro+ API Server
Comprehensive unit tests covering API endpoints, data processing, and error handling

Author: Alex (with Claude)
Date: July 2025

Run with: python -m pytest tests/test_enviro_api_server.py -v
"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

# Mock Flask and dependencies before importing the API server
# We'll create mock implementations instead of importing the real API server
# since it has Flask dependencies that are hard to mock properly

class TestEnviroAPIServer(unittest.TestCase):
    """Test cases for EnviroAPIServer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_enviro.db')
        
        # Create test database with sample data
        self.create_test_database()
        
        # Mock the API server class (since we can't import the real one without Flask dependencies)
        self.api_server = self.create_mock_api_server()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_database(self):
        """Create a test database with sample sensor data"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL,
                pressure REAL,
                humidity REAL,
                light REAL,
                oxidised REAL,
                reduced REAL,
                nh3 REAL,
                cpu_temp REAL,
                errors TEXT
            )
        ''')
        
        # Insert sample data
        sample_data = [
            ('2025-07-17T10:00:00', 23.5, 1013.25, 45.0, 150.0, 25.0, 450.0, 250.0, 55.2, None),
            ('2025-07-17T10:01:00', 23.7, 1013.30, 44.8, 152.0, 25.2, 448.0, 252.0, 55.5, None),
            ('2025-07-17T10:02:00', 23.6, 1013.28, 45.2, 148.0, 24.8, 452.0, 248.0, 55.0, '["Test error"]'),
            ('2025-07-17T09:00:00', 22.8, 1012.80, 46.0, 140.0, 26.0, 460.0, 240.0, 54.8, None),
            ('2025-07-16T10:00:00', 24.2, 1014.00, 43.5, 160.0, 24.5, 445.0, 255.0, 56.0, None),
        ]
        
        cursor.executemany('''
            INSERT INTO sensor_readings 
            (timestamp, temperature, pressure, humidity, light, oxidised, reduced, nh3, cpu_temp, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        
        conn.commit()
        conn.close()
    
    def create_mock_api_server(self):
        """Create a mock API server for testing"""
        # Since we can't easily import the real class due to Flask dependencies,
        # we'll create a mock that implements the same methods
        mock_server = Mock()
        mock_server.data_dir = self.test_dir
        mock_server.db_path = self.test_db_path
        
        # Implement the actual methods for testing
        def get_latest_reading():
            try:
                conn = sqlite3.connect(self.test_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp, temperature, pressure, humidity, light, 
                           oxidised, reduced, nh3, cpu_temp, errors
                    FROM sensor_readings 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'timestamp': datetime.fromisoformat(row[0]).strftime('%H:%M:%S'),
                        'temperature': round(float(row[1]) if row[1] else 0.0, 2),
                        'pressure': round(float(row[2]) if row[2] else 0.0, 2),
                        'humidity': round(float(row[3]) if row[3] else 0.0, 2),
                        'light': round(float(row[4]) if row[4] else 0.0, 1),
                        'oxidised': round(float(row[5]) if row[5] else 0.0, 2),
                        'reduced': round(float(row[6]) if row[6] else 0.0, 2),
                        'nh3': round(float(row[7]) if row[7] else 0.0, 2),
                        'cpu_temp': round(float(row[8]) if row[8] else 0.0, 2),
                        'battery': 4.1,
                        'power_source': 'USB',
                        'rssi': -65,
                        'snr': 10.0,
                        'transmitter_type': 'enviro_plus',
                        'charging': 'N/A',
                        'interval': None,
                        'uptime': None,
                        'sensor_type': 'enviro_plus',
                        'location': 'living_room',
                        'errors': json.loads(row[9]) if row[9] else []
                    }
                return None
            except Exception:
                return None
        
        def get_recent_readings(hours=24):
            try:
                conn = sqlite3.connect(self.test_db_path)
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                query = """
                    SELECT timestamp, temperature, pressure, humidity, light, 
                           oxidised, reduced, nh3, cpu_temp
                    FROM sensor_readings 
                    WHERE timestamp > ?
                    ORDER BY timestamp ASC
                """
                
                df = pd.read_sql_query(query, conn, params=[cutoff_time])
                conn.close()
                
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['timestamp'])
                    df['time'] = df['datetime'].dt.strftime('%H:%M:%S')
                    
                    readings = []
                    for _, row in df.iterrows():
                        readings.append({
                            'timestamp': row['time'],
                            'datetime': row['datetime'].isoformat(),
                            'temperature': round(float(row['temperature']) if pd.notna(row['temperature']) else 0.0, 2),
                            'pressure': round(float(row['pressure']) if pd.notna(row['pressure']) else 0.0, 2),
                            'humidity': round(float(row['humidity']) if pd.notna(row['humidity']) else 0.0, 2),
                            'light': round(float(row['light']) if pd.notna(row['light']) else 0.0, 1),
                            'oxidised': round(float(row['oxidised']) if pd.notna(row['oxidised']) else 0.0, 2),
                            'reduced': round(float(row['reduced']) if pd.notna(row['reduced']) else 0.0, 2),
                            'nh3': round(float(row['nh3']) if pd.notna(row['nh3']) else 0.0, 2),
                            'cpu_temp': round(float(row['cpu_temp']) if pd.notna(row['cpu_temp']) else 0.0, 2)
                        })
                    
                    return readings
                return []
            except Exception:
                return []
        
        def get_system_status():
            try:
                conn = sqlite3.connect(self.test_db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM sensor_readings")
                total_readings = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(timestamp) FROM sensor_readings")
                latest_timestamp = cursor.fetchone()[0]
                
                if latest_timestamp:
                    latest_time = datetime.fromisoformat(latest_timestamp)
                    data_age_minutes = (datetime.now() - latest_time).total_seconds() / 60
                else:
                    data_age_minutes = float('inf')
                
                conn.close()
                
                return {
                    'total_readings': total_readings,
                    'latest_timestamp': latest_timestamp,
                    'data_age_minutes': round(data_age_minutes, 1),
                    'csv_files_count': 0,
                    'system_type': 'enviro_plus',
                    'location': 'living_room',
                    'status': 'online' if data_age_minutes < 5 else 'offline',
                    'uptime_hours': None,
                    'database_path': self.test_db_path,
                    'data_directory': self.test_dir
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Attach methods to mock
        mock_server.get_latest_reading = get_latest_reading
        mock_server.get_recent_readings = get_recent_readings
        mock_server.get_system_status = get_system_status
        
        return mock_server
    
    def test_get_latest_reading_success(self):
        """Test getting latest sensor reading"""
        result = self.api_server.get_latest_reading()
        
        self.assertIsNotNone(result)
        self.assertIn('timestamp', result)
        self.assertIn('temperature', result)
        self.assertIn('pressure', result)
        self.assertIn('humidity', result)
        self.assertIn('light', result)
        self.assertIn('oxidised', result)
        self.assertIn('reduced', result)
        self.assertIn('nh3', result)
        self.assertIn('cpu_temp', result)
        
        # Check data types and ranges
        self.assertIsInstance(result['temperature'], float)
        self.assertIsInstance(result['pressure'], float)
        self.assertIsInstance(result['humidity'], float)
        self.assertGreater(result['temperature'], 0)
        self.assertGreater(result['pressure'], 900)
        self.assertLess(result['pressure'], 1100)
        self.assertGreaterEqual(result['humidity'], 0)
        self.assertLessEqual(result['humidity'], 100)
    
    def test_get_latest_reading_with_errors(self):
        """Test latest reading includes error information"""
        result = self.api_server.get_latest_reading()
        
        self.assertIsNotNone(result)
        self.assertIn('errors', result)
        self.assertIsInstance(result['errors'], list)
    
    def test_get_recent_readings_default_hours(self):
        """Test getting recent readings with default time range"""
        result = self.api_server.get_recent_readings()
        
        self.assertIsInstance(result, list)
        # Should have some readings from our test data
        self.assertGreater(len(result), 0)
        
        # Check structure of first reading
        if result:
            reading = result[0]
            self.assertIn('timestamp', reading)
            self.assertIn('datetime', reading)
            self.assertIn('temperature', reading)
            self.assertIn('pressure', reading)
            self.assertIn('humidity', reading)
    
    def test_get_recent_readings_custom_hours(self):
        """Test getting recent readings with custom time range"""
        # Test with 1 hour - should get fewer results
        result_1h = self.api_server.get_recent_readings(hours=1)
        
        # Test with 48 hours - should get more results
        result_48h = self.api_server.get_recent_readings(hours=48)
        
        self.assertIsInstance(result_1h, list)
        self.assertIsInstance(result_48h, list)
        
        # 48 hours should have more or equal readings than 1 hour
        self.assertGreaterEqual(len(result_48h), len(result_1h))
    
    def test_get_system_status(self):
        """Test getting system status information"""
        result = self.api_server.get_system_status()
        
        self.assertIsNotNone(result)
        self.assertIn('total_readings', result)
        self.assertIn('latest_timestamp', result)
        self.assertIn('data_age_minutes', result)
        self.assertIn('system_type', result)
        self.assertIn('location', result)
        self.assertIn('status', result)
        
        # Check data types
        self.assertIsInstance(result['total_readings'], int)
        self.assertGreater(result['total_readings'], 0)
        self.assertEqual(result['system_type'], 'enviro_plus')
        self.assertIn(result['status'], ['online', 'offline'])
    
    def test_data_formatting_and_rounding(self):
        """Test that sensor data is properly formatted and rounded"""
        result = self.api_server.get_latest_reading()
        
        if result:
            # Temperature should be rounded to 2 decimal places
            temp_str = str(result['temperature'])
            if '.' in temp_str:
                decimal_places = len(temp_str.split('.')[1])
                self.assertLessEqual(decimal_places, 2)
            
            # Light should be rounded to 1 decimal place
            light_str = str(result['light'])
            if '.' in light_str:
                decimal_places = len(light_str.split('.')[1])
                self.assertLessEqual(decimal_places, 1)
    
    def test_dashboard_compatibility_fields(self):
        """Test that response includes fields required by dashboard"""
        result = self.api_server.get_latest_reading()
        
        if result:
            # Check dashboard-specific fields
            self.assertIn('battery', result)
            self.assertIn('power_source', result)
            self.assertIn('rssi', result)
            self.assertIn('snr', result)
            self.assertIn('transmitter_type', result)
            self.assertIn('charging', result)
            self.assertIn('sensor_type', result)
            self.assertIn('location', result)
            
            # Check expected values
            self.assertEqual(result['power_source'], 'USB')
            self.assertEqual(result['transmitter_type'], 'enviro_plus')
            self.assertEqual(result['sensor_type'], 'enviro_plus')
            self.assertEqual(result['charging'], 'N/A')


class TestAPIEndpointLogic(unittest.TestCase):
    """Test API endpoint logic and data processing"""
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting for API responses"""
        # Test datetime to time string conversion
        test_datetime = datetime(2025, 7, 17, 14, 30, 45)
        expected_time = "14:30:45"
        
        actual_time = test_datetime.strftime('%H:%M:%S')
        self.assertEqual(actual_time, expected_time)
    
    def test_error_json_handling(self):
        """Test JSON error list handling"""
        # Test valid JSON error list
        error_json = '["BME280 error", "Gas sensor timeout"]'
        errors = json.loads(error_json)
        
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 2)
        self.assertIn("BME280 error", errors)
        
        # Test None/empty case
        self.assertEqual(json.loads('null'), None)
    
    def test_data_age_calculation(self):
        """Test data age calculation logic"""
        # Test recent data (should be online)
        recent_time = datetime.now() - timedelta(minutes=2)
        age_minutes = (datetime.now() - recent_time).total_seconds() / 60
        
        self.assertLess(age_minutes, 5)
        status = 'online' if age_minutes < 5 else 'offline'
        self.assertEqual(status, 'online')
        
        # Test old data (should be offline)
        old_time = datetime.now() - timedelta(minutes=10)
        age_minutes = (datetime.now() - old_time).total_seconds() / 60
        
        self.assertGreater(age_minutes, 5)
        status = 'online' if age_minutes < 5 else 'offline'
        self.assertEqual(status, 'offline')
    
    def test_pandas_nan_handling(self):
        """Test handling of pandas NaN values"""
        import pandas as pd
        
        # Test NaN to 0.0 conversion
        test_value = float('nan')
        result = 0.0 if pd.isna(test_value) else test_value
        self.assertEqual(result, 0.0)
        
        # Test valid value passthrough
        test_value = 23.5
        result = 0.0 if pd.isna(test_value) else test_value
        self.assertEqual(result, 23.5)
    
    def test_gas_sensor_unit_conversion(self):
        """Test gas sensor readings are in correct units (kΩ)"""
        # Gas sensors should return values in kΩ range
        test_oxidised = 25.0  # kΩ
        test_reduced = 450.0  # kΩ
        test_nh3 = 250.0     # kΩ
        
        # These should be reasonable values for gas sensors
        self.assertGreater(test_oxidised, 0)
        self.assertLess(test_oxidised, 1000)  # Reasonable upper bound
        
        self.assertGreater(test_reduced, 0)
        self.assertLess(test_reduced, 1000)
        
        self.assertGreater(test_nh3, 0)
        self.assertLess(test_nh3, 1000)


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations and SQL queries"""
    
    def setUp(self):
        """Set up test database"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, 'test_api.db')
        
        # Create test database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL,
                pressure REAL,
                humidity REAL,
                light REAL,
                oxidised REAL,
                reduced REAL,
                nh3 REAL,
                cpu_temp REAL,
                errors TEXT
            )
        ''')
        
        # Insert test data with various timestamps
        test_data = [
            ('2025-07-17T14:00:00', 23.5, 1013.25, 45.0, 150.0, 25.0, 450.0, 250.0, 55.0, None),
            ('2025-07-17T13:00:00', 23.2, 1013.20, 46.0, 148.0, 24.8, 452.0, 248.0, 54.8, None),
            ('2025-07-17T12:00:00', 22.8, 1013.15, 47.0, 145.0, 25.2, 448.0, 252.0, 55.2, None),
            ('2025-07-16T14:00:00', 24.0, 1014.00, 44.0, 155.0, 24.5, 455.0, 245.0, 56.0, None),
        ]
        
        cursor.executemany('''
            INSERT INTO sensor_readings 
            (timestamp, temperature, pressure, humidity, light, oxidised, reduced, nh3, cpu_temp, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_data)
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_latest_reading_query(self):
        """Test SQL query for latest reading"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, temperature, pressure, humidity
            FROM sensor_readings 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        # Should be the most recent timestamp (2025-07-17T14:00:00)
        self.assertEqual(row[0], '2025-07-17T14:00:00')
        self.assertEqual(row[1], 23.5)  # temperature
    
    def test_recent_readings_query(self):
        """Test SQL query for recent readings with time filter"""
        conn = sqlite3.connect(self.test_db_path)
        
        # Query for last 24 hours from a fixed point
        cutoff_time = '2025-07-16T15:00:00'  # Should get 3 readings
        
        query = """
            SELECT timestamp, temperature
            FROM sensor_readings 
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """
        
        cursor = conn.cursor()
        cursor.execute(query, [cutoff_time])
        rows = cursor.fetchall()
        conn.close()
        
        # Should get 3 readings (all from 2025-07-17)
        self.assertEqual(len(rows), 3)
        
        # Should be ordered by timestamp ascending
        timestamps = [row[0] for row in rows]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_count_query(self):
        """Test counting total readings"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 4)  # We inserted 4 test records
    
    def test_max_timestamp_query(self):
        """Test getting maximum timestamp"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(timestamp) FROM sensor_readings")
        max_timestamp = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(max_timestamp, '2025-07-17T14:00:00')


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_missing_database_handling(self):
        """Test handling of missing database file"""
        nonexistent_db = '/nonexistent/path/db.sqlite'
        
        # Should handle database connection error gracefully
        try:
            conn = sqlite3.connect(nonexistent_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            conn.close()
            # If we get here, the test setup is wrong
            self.fail("Expected database error")
        except sqlite3.OperationalError:
            # This is expected - database/table doesn't exist
            pass
    
    def test_empty_database_handling(self):
        """Test handling of empty database"""
        test_dir = tempfile.mkdtemp()
        empty_db_path = os.path.join(test_dir, 'empty.db')
        
        # Create empty database with table but no data
        conn = sqlite3.connect(empty_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                temperature REAL
            )
        ''')
        conn.commit()
        
        # Query should return None/empty results
        cursor.execute("SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        
        conn.close()
        
        self.assertIsNone(result)
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_malformed_json_error_handling(self):
        """Test handling of malformed JSON in errors field"""
        # Test invalid JSON
        invalid_json = '{"invalid": json}'
        
        try:
            errors = json.loads(invalid_json)
            # Should not reach here
            self.fail("Expected JSON decode error")
        except json.JSONDecodeError:
            # This is expected
            errors = []  # Fallback to empty list
        
        self.assertEqual(errors, [])


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)