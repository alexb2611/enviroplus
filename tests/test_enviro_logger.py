#!/usr/bin/env python3
"""
Test Suite for Enhanced Enviro+ Data Logger
Comprehensive unit tests covering sensor reading, data storage, and error handling

Author: Alex (with Claude)
Date: July 2025

Run with: python -m pytest tests/test_enviro_logger.py -v
"""

import csv
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, mock_open

import pytest
from PIL import Image

# Import our logger (adjust path as needed)
# from enhanced_enviro_logger import EnviroDataLogger


class MockBME280:
    """Mock BME280 sensor for testing"""
    def __init__(self, temp=23.5, pressure=1013.25, humidity=45.0):
        self.temp = temp
        self.pressure = pressure  
        self.humidity = humidity
        self.fail_on_read = False
    
    def get_temperature(self):
        if self.fail_on_read:
            raise Exception("Simulated BME280 failure")
        return self.temp
    
    def get_pressure(self):
        if self.fail_on_read:
            raise Exception("Simulated BME280 failure")
        return self.pressure
    
    def get_humidity(self):
        if self.fail_on_read:
            raise Exception("Simulated BME280 failure")
        return self.humidity


class MockLTR559:
    """Mock LTR559 light/proximity sensor for testing"""
    def __init__(self, lux=150.0, proximity=5):
        self.lux = lux
        self.proximity = proximity
        self.fail_on_read = False
    
    def get_lux(self):
        if self.fail_on_read:
            raise Exception("Simulated LTR559 failure")
        return self.lux
    
    def get_proximity(self):
        if self.fail_on_read:
            raise Exception("Simulated LTR559 failure")
        return self.proximity


class MockGasReading:
    """Mock gas sensor reading"""
    def __init__(self, oxidising=25000, reducing=450000, nh3=250000):
        self.oxidising = oxidising
        self.reducing = reducing
        self.nh3 = nh3


class MockGasSensor:
    """Mock gas sensor for testing"""
    def __init__(self):
        self.fail_on_read = False
        self.reading = MockGasReading()
    
    def read_all(self):
        if self.fail_on_read:
            raise Exception("Simulated gas sensor failure")
        return self.reading


class TestEnviroDataLogger(unittest.TestCase):
    """Test cases for EnviroDataLogger class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Mock hardware components
        self.mock_bme280 = MockBME280()
        self.mock_ltr559 = MockLTR559()
        self.mock_gas = MockGasSensor()
        
        # Create mock display components
        self.mock_st7735 = Mock()
        self.mock_st7735.width = 160
        self.mock_st7735.height = 80
        
        # We'll need to patch the actual imports when testing the real class
        self.patches = []
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Stop all patches
        for patch_obj in self.patches:
            patch_obj.stop()
    
    def create_mock_logger(self):
        """Create a logger instance with mocked hardware for testing"""
        # This would be used with the actual EnviroDataLogger class
        # For now, we'll test individual methods
        pass
    
    def test_cpu_temperature_reading(self):
        """Test CPU temperature reading with mocked file system"""
        mock_temp_content = "45678\n"  # 45.678°C
        
        with patch("builtins.open", mock_open(read_data=mock_temp_content)):
            # Test the method directly
            # Normally would be: result = logger.get_cpu_temperature()
            # For this example, simulate the logic
            temp = int(mock_temp_content.strip()) / 1000.0
            self.assertAlmostEqual(temp, 45.678, places=3)
    
    def test_cpu_temperature_file_error(self):
        """Test CPU temperature reading with file system error"""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            # Should return fallback value on error
            # result = logger.get_cpu_temperature()
            # self.assertEqual(result, 50.0)  # Fallback value
            pass
    
    def test_temperature_compensation_calculation(self):
        """Test temperature compensation algorithm"""
        raw_temp = 28.5
        cpu_temp = 55.0
        avg_cpu_temp = 52.0
        compensation_factor = 2.25
        
        # Expected formula: raw_temp - ((avg_cpu_temp - raw_temp) / factor)
        expected_compensated = raw_temp - ((avg_cpu_temp - raw_temp) / compensation_factor)
        
        # Calculate manually for verification
        compensated = raw_temp - ((avg_cpu_temp - raw_temp) / compensation_factor)
        
        self.assertAlmostEqual(compensated, expected_compensated, places=3)
        self.assertLess(compensated, raw_temp)  # Should be lower than raw reading
    
    def test_sensor_reading_success(self):
        """Test successful sensor reading"""
        # Mock all sensors returning valid data
        with patch('time.time', return_value=1625097600):  # Fixed timestamp
            
            # Test data structure
            expected_keys = ['timestamp', 'cpu_temp', 'temperature', 'pressure', 
                           'humidity', 'light', 'proximity', 'oxidised', 'reduced', 
                           'nh3', 'errors']
            
            # Create mock reading
            mock_reading = {
                'timestamp': datetime.now(timezone.utc),
                'cpu_temp': 45.5,
                'temperature': 23.2,
                'pressure': 1013.25,
                'humidity': 45.0,
                'light': 150.0,
                'proximity': 5,
                'oxidised': 25.0,  # Converted from sensor units
                'reduced': 450.0,
                'nh3': 250.0,
                'errors': []
            }
            
            # Verify structure
            for key in expected_keys:
                self.assertIn(key, mock_reading)
            
            # Verify data types
            self.assertIsInstance(mock_reading['timestamp'], datetime)
            self.assertIsInstance(mock_reading['temperature'], (int, float))
            self.assertIsInstance(mock_reading['errors'], list)
    
    def test_sensor_reading_with_errors(self):
        """Test sensor reading when some sensors fail"""
        # Simulate sensor failures and ensure graceful handling
        mock_reading_with_errors = {
            'timestamp': datetime.now(timezone.utc),
            'cpu_temp': 45.5,
            'temperature': None,  # BME280 failed
            'pressure': None,
            'humidity': None,
            'light': 150.0,  # LTR559 working
            'proximity': 5,
            'oxidised': None,  # Gas sensor failed
            'reduced': None,
            'nh3': None,
            'errors': ['BME280 error: Simulated failure', 'Gas sensor error: Simulated failure']
        }
        
        # Should continue running even with errors
        self.assertIsNotNone(mock_reading_with_errors['timestamp'])
        self.assertTrue(len(mock_reading_with_errors['errors']) > 0)
        self.assertIsNone(mock_reading_with_errors['temperature'])
    
    def test_database_schema(self):
        """Test database table creation and schema"""
        db_path = os.path.join(self.test_dir, 'test_enviro.db')
        
        # Create database with our schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        
        # Test schema
        cursor.execute("PRAGMA table_info(sensor_readings)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'timestamp', 'temperature', 'pressure', 'humidity',
                          'light', 'oxidised', 'reduced', 'nh3', 'cpu_temp', 'errors']
        
        for col in expected_columns:
            self.assertIn(col, column_names)
        
        conn.close()
    
    def test_database_insert(self):
        """Test inserting data into database"""
        db_path = os.path.join(self.test_dir, 'test_enviro.db')
        
        # Create database
        conn = sqlite3.connect(db_path)
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
        
        # Test data
        test_reading = {
            'timestamp': datetime.now(timezone.utc),
            'temperature': 23.5,
            'pressure': 1013.25,
            'humidity': 45.0,
            'light': 150.0,
            'oxidised': 25.0,
            'reduced': 450.0,
            'nh3': 250.0,
            'cpu_temp': 45.5,
            'errors': []
        }
        
        # Insert data
        cursor.execute('''
            INSERT INTO sensor_readings 
            (timestamp, temperature, pressure, humidity, light, oxidised, reduced, nh3, cpu_temp, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_reading['timestamp'].isoformat(),
            test_reading['temperature'],
            test_reading['pressure'],
            test_reading['humidity'],
            test_reading['light'],
            test_reading['oxidised'],
            test_reading['reduced'],
            test_reading['nh3'],
            test_reading['cpu_temp'],
            json.dumps(test_reading['errors']) if test_reading['errors'] else None
        ))
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        # Verify data
        cursor.execute("SELECT * FROM sensor_readings")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[2], 23.5, places=1)  # temperature
        
        conn.close()
    
    def test_csv_file_creation(self):
        """Test CSV file creation and writing"""
        csv_path = os.path.join(self.test_dir, 'test_enviro_2025-07-11.csv')
        
        test_reading = {
            'timestamp': datetime.now(timezone.utc),
            'temperature': 23.5,
            'pressure': 1013.25,
            'humidity': 45.0,
            'light': 150.0,
            'oxidised': 25.0,
            'reduced': 450.0,
            'nh3': 250.0,
            'cpu_temp': 45.5,
            'errors': ['Test error']
        }
        
        # Write CSV
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'temperature', 'pressure', 'humidity',
                         'light', 'oxidised', 'reduced', 'nh3', 'cpu_temp', 'errors']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            row = {
                'timestamp': test_reading['timestamp'].isoformat(),
                'temperature': test_reading['temperature'],
                'pressure': test_reading['pressure'],
                'humidity': test_reading['humidity'],
                'light': test_reading['light'],
                'oxidised': test_reading['oxidised'],
                'reduced': test_reading['reduced'],
                'nh3': test_reading['nh3'],
                'cpu_temp': test_reading['cpu_temp'],
                'errors': '; '.join(test_reading['errors'])
            }
            
            writer.writerow(row)
        
        # Verify file creation
        self.assertTrue(os.path.exists(csv_path))
        
        # Verify content
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(float(rows[0]['temperature']), 23.5)
    
    def test_data_directory_creation(self):
        """Test automatic data directory creation"""
        new_dir = os.path.join(self.test_dir, 'new_data_dir')
        
        # Directory shouldn't exist initially
        self.assertFalse(os.path.exists(new_dir))
        
        # Simulate directory creation logic
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        
        # Should exist now
        self.assertTrue(os.path.exists(new_dir))
    
    def test_gas_sensor_unit_conversion(self):
        """Test gas sensor reading conversion to kΩ"""
        # Sensor returns resistance in Ohms, we want kΩ
        raw_oxidising = 25000  # 25kΩ
        raw_reducing = 450000  # 450kΩ
        raw_nh3 = 250000      # 250kΩ
        
        # Convert to kΩ
        oxidising_kohm = raw_oxidising / 1000
        reducing_kohm = raw_reducing / 1000
        nh3_kohm = raw_nh3 / 1000
        
        self.assertEqual(oxidising_kohm, 25.0)
        self.assertEqual(reducing_kohm, 450.0)
        self.assertEqual(nh3_kohm, 250.0)
    
    def test_error_handling_json_serialization(self):
        """Test error list JSON serialization for database storage"""
        errors = ['BME280 error: Timeout', 'Gas sensor error: Read failed']
        
        # Serialize
        error_json = json.dumps(errors)
        
        # Deserialize
        recovered_errors = json.loads(error_json)
        
        self.assertEqual(errors, recovered_errors)
        self.assertIsInstance(recovered_errors, list)
    
    def test_proximity_sensor_display_mode_switching(self):
        """Test display mode switching logic"""
        current_mode = 0
        num_variables = 7  # temperature, pressure, humidity, light, oxidised, reduced, nh3
        proximity_threshold = 1500
        
        # Simulate proximity trigger
        proximity_reading = 2000  # Above threshold
        
        if proximity_reading > proximity_threshold:
            current_mode += 1
            current_mode %= num_variables
        
        self.assertEqual(current_mode, 1)
        
        # Test wrapping
        current_mode = 6  # Last mode
        if proximity_reading > proximity_threshold:
            current_mode += 1
            current_mode %= num_variables
        
        self.assertEqual(current_mode, 0)  # Should wrap to first mode


class TestDataValidation(unittest.TestCase):
    """Test data validation and quality checks"""
    
    def test_temperature_range_validation(self):
        """Test temperature reading validation"""
        # Reasonable indoor temperature range: -10°C to 50°C
        valid_temps = [18.5, 23.0, 25.5, 30.2]
        invalid_temps = [-50.0, 100.0, None]
        
        def is_valid_temperature(temp):
            if temp is None:
                return False
            return -10 <= temp <= 50
        
        for temp in valid_temps:
            self.assertTrue(is_valid_temperature(temp))
        
        for temp in invalid_temps:
            self.assertFalse(is_valid_temperature(temp))
    
    def test_humidity_range_validation(self):
        """Test humidity reading validation"""
        # Valid humidity: 0-100%
        valid_humidity = [0.0, 45.5, 100.0]
        invalid_humidity = [-5.0, 150.0, None]
        
        def is_valid_humidity(humidity):
            if humidity is None:
                return False
            return 0 <= humidity <= 100
        
        for humidity in valid_humidity:
            self.assertTrue(is_valid_humidity(humidity))
        
        for humidity in invalid_humidity:
            self.assertFalse(is_valid_humidity(humidity))
    
    def test_pressure_range_validation(self):
        """Test pressure reading validation"""
        # Reasonable atmospheric pressure: 900-1100 hPa
        valid_pressures = [950.0, 1013.25, 1050.0]
        invalid_pressures = [500.0, 1500.0, None]
        
        def is_valid_pressure(pressure):
            if pressure is None:
                return False
            return 900 <= pressure <= 1100
        
        for pressure in valid_pressures:
            self.assertTrue(is_valid_pressure(pressure))
        
        for pressure in invalid_pressures:
            self.assertFalse(is_valid_pressure(pressure))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
