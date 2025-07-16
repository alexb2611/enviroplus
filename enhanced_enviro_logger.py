#!/usr/bin/env python3
"""
Enhanced Enviro+ Data Logger
Built on Pimoroni's all-in-one-no-pm.py example
Adds persistent data logging, error handling, and preparation for smart home integration

Author: Alex (with Claude)
Date: July 2025
"""

import colorsys
import csv
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import st7735

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from fonts.ttf import RobotoMedium as UserFont
from PIL import Image, ImageDraw, ImageFont
from enviroplus import gas

# Logging configuration
logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler('./enviro_data.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnviroDataLogger:
    def __init__(self, data_dir='./data'):
        """
        Initialize the Enviro+ data logger
        
        Args:
            data_dir (str): Directory to store data files
        """
        self.data_dir = data_dir
        self.ensure_data_directory()
        
        # Initialize sensors
        self.bme280 = BME280()
        self.init_display()
        
        # CPU temperature tracking for compensation
        self.cpu_temps = [self.get_cpu_temperature()] * 5
        # Compensation factor calibrated with DHT11 reference sensor
        # Pi Zero 2W generates significant heat - factor 1.4 removes ~10°C CPU heat soak
        self.temp_compensation_factor = 1.4
        
        # Display control
        self.delay = 0.5  # Debounce for proximity tap
        self.mode = 0     # Current display mode
        self.last_page = 0
        
        # Display power management
        self.display_timeout = 300  # 5 minutes in seconds
        self.display_on = True
        self.last_activity_time = time.time()
        self.proximity_wake_threshold = 1500  # Proximity value to wake display
        
        # Create sensor variables and display data storage
        self.variables = ["temperature", "pressure", "humidity", "light", 
                         "oxidised", "reduced", "nh3"]
        self.units = ["°C", "hPa", "%", "Lux", "kΩ", "kΩ", "kΩ"]
        
        # Display graph data
        self.values = {}
        for v in self.variables:
            self.values[v] = [1] * self.WIDTH
            
        # Data logging setup
        self.setup_database()
        self.csv_filename = None
        
        logger.info("Enhanced Enviro+ Data Logger initialized")
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")
    
    def init_display(self):
        """Initialize the LCD display"""
        self.st7735 = st7735.ST7735(
            port=0,
            cs=1,
            dc="GPIO9",
            backlight="GPIO12",
            rotation=270,
            spi_speed_hz=10000000
        )
        
        self.st7735.begin()
        self.WIDTH = self.st7735.width
        self.HEIGHT = self.st7735.height
        
        # Set up canvas and font
        self.img = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        font_size = 20
        self.font = ImageFont.truetype(UserFont, font_size)
        self.top_pos = 25
        
        logger.info("Display initialized")
    
    def setup_database(self):
        """Initialize SQLite database for data storage"""
        self.db_path = os.path.join(self.data_dir, 'enviro_data.db')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
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
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def get_cpu_temperature(self):
        """Get CPU temperature for heat compensation"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = f.read()
                temp = int(temp) / 1000.0
            return temp
        except Exception as e:
            logger.error(f"Failed to read CPU temperature: {e}")
            return 50.0  # Fallback value
    
    def read_sensors(self, verbose_temp_debug=False):
        """
        Read all sensor values with error handling
        
        Returns:
            dict: Sensor readings with timestamp
        """
        timestamp = datetime.now(timezone.utc)
        errors = []
        
        # Initialize reading dict
        reading = {
            'timestamp': timestamp,
            'cpu_temp': None,
            'temperature': None,
            'pressure': None,
            'humidity': None,
            'light': None,
            'proximity': None,
            'oxidised': None,
            'reduced': None,
            'nh3': None,
            'errors': []
        }
        
        try:
            # CPU temperature and compensation
            cpu_temp = self.get_cpu_temperature()
            reading['cpu_temp'] = cpu_temp
            
            # Smooth CPU temperature for compensation
            self.cpu_temps = self.cpu_temps[1:] + [cpu_temp]
            avg_cpu_temp = sum(self.cpu_temps) / float(len(self.cpu_temps))
            
            # BME280 readings
            try:
                raw_temp = self.bme280.get_temperature()
                compensated_temp = raw_temp - ((avg_cpu_temp - raw_temp) / self.temp_compensation_factor)
                reading['temperature'] = compensated_temp
                
                # Debug output for temperature compensation monitoring (only when requested)
                if verbose_temp_debug:
                    logger.info(f"Temperature compensation: Raw={raw_temp:.1f}°C, CPU={avg_cpu_temp:.1f}°C, Compensated={compensated_temp:.1f}°C, Factor={self.temp_compensation_factor}")
                
                reading['pressure'] = self.bme280.get_pressure()
                reading['humidity'] = self.bme280.get_humidity()
                
            except Exception as e:
                errors.append(f"BME280 error: {e}")
                logger.error(f"BME280 sensor error: {e}")
            
            # Light sensor readings
            try:
                proximity = ltr559.get_proximity()
                reading['proximity'] = proximity
                
                if proximity < 10:
                    reading['light'] = ltr559.get_lux()
                else:
                    reading['light'] = 1  # Sensor blocked
                    
            except Exception as e:
                errors.append(f"LTR559 error: {e}")
                logger.error(f"Light sensor error: {e}")
            
            # Gas sensor readings
            try:
                gas_data = gas.read_all()
                reading['oxidised'] = gas_data.oxidising / 1000  # Convert to kΩ
                reading['reduced'] = gas_data.reducing / 1000
                reading['nh3'] = gas_data.nh3 / 1000
                
            except Exception as e:
                errors.append(f"Gas sensor error: {e}")
                logger.error(f"Gas sensor error: {e}")
                
        except Exception as e:
            errors.append(f"General sensor error: {e}")
            logger.error(f"General sensor reading error: {e}")
        
        reading['errors'] = errors
        return reading
    
    def save_to_database(self, reading):
        """Save reading to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sensor_readings 
                (timestamp, temperature, pressure, humidity, light, oxidised, reduced, nh3, cpu_temp, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reading['timestamp'].isoformat(),
                reading['temperature'],
                reading['pressure'],
                reading['humidity'],
                reading['light'],
                reading['oxidised'],
                reading['reduced'],
                reading['nh3'],
                reading['cpu_temp'],
                json.dumps(reading['errors']) if reading['errors'] else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
    
    def save_to_csv(self, reading):
        """Save reading to daily CSV file"""
        try:
            # Create daily CSV filename
            date_str = reading['timestamp'].strftime('%Y-%m-%d')
            csv_filename = os.path.join(self.data_dir, f'enviro_data_{date_str}.csv')
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_filename)
            
            with open(csv_filename, 'a', newline='') as csvfile:
                fieldnames = ['timestamp', 'temperature', 'pressure', 'humidity', 
                             'light', 'oxidised', 'reduced', 'nh3', 'cpu_temp', 'errors']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                # Prepare row data
                row = {
                    'timestamp': reading['timestamp'].isoformat(),
                    'temperature': reading['temperature'],
                    'pressure': reading['pressure'],
                    'humidity': reading['humidity'],
                    'light': reading['light'],
                    'oxidised': reading['oxidised'],
                    'reduced': reading['reduced'],
                    'nh3': reading['nh3'],
                    'cpu_temp': reading['cpu_temp'],
                    'errors': '; '.join(reading['errors']) if reading['errors'] else ''
                }
                
                writer.writerow(row)
                
        except Exception as e:
            logger.error(f"CSV save error: {e}")
    
    def turn_display_off(self):
        """Turn off the display backlight and clear screen"""
        try:
            self.st7735.set_backlight(0)
            # Clear the display to black
            self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), (0, 0, 0))
            self.st7735.display(self.img)
            self.display_on = False
            logger.info("Display turned off after timeout")
        except Exception as e:
            logger.error(f"Error turning off display: {e}")
    
    def turn_display_on(self):
        """Turn on the display backlight"""
        try:
            self.st7735.set_backlight(1)
            self.display_on = True
            self.last_activity_time = time.time()
            logger.info("Display turned on by proximity detection")
        except Exception as e:
            logger.error(f"Error turning on display: {e}")
    
    def check_display_timeout(self):
        """Check if display should be turned off due to timeout"""
        current_time = time.time()
        if (self.display_on and 
            current_time - self.last_activity_time > self.display_timeout):
            self.turn_display_off()
    
    def handle_proximity_wake(self, proximity):
        """Handle proximity sensor for waking display"""
        if (not self.display_on and 
            proximity and proximity > self.proximity_wake_threshold):
            self.turn_display_on()
            return True
        return False
    
    def display_text(self, variable, data, unit):
        """Display sensor data on LCD with graph"""
        # Only update display if it's on
        if not self.display_on:
            return
            
        # Maintain length of list
        self.values[variable] = self.values[variable][1:] + [data]
        
        # Scale the values for the variable between 0 and 1
        vmin = min(self.values[variable])
        vmax = max(self.values[variable])
        
        if vmax > vmin:
            colours = [(v - vmin + 1) / (vmax - vmin + 1) for v in self.values[variable]]
        else:
            colours = [0.5] * len(self.values[variable])
        
        # Format the variable name and value
        if data is not None:
            message = f"{variable[:4]}: {data:.1f} {unit}"
        else:
            message = f"{variable[:4]}: ERROR"
            
        logger.info(message)
        
        # Clear screen
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), (255, 255, 255))
        
        # Draw graph
        for i in range(len(colours)):
            # Convert the values to colours from red to blue
            colour = (1.0 - colours[i]) * 0.6
            r, g, b = [int(x * 255.0) for x in colorsys.hsv_to_rgb(colour, 1.0, 1.0)]
            
            # Draw a 1-pixel wide rectangle of colour
            self.draw.rectangle((i, self.top_pos, i + 1, self.HEIGHT), (r, g, b))
            
            # Draw a line graph in black
            line_y = self.HEIGHT - (self.top_pos + (colours[i] * (self.HEIGHT - self.top_pos))) + self.top_pos
            self.draw.rectangle((i, line_y, i + 1, line_y + 1), (0, 0, 0))
        
        # Write the text at the top in black
        self.draw.text((0, 0), message, font=self.font, fill=(0, 0, 0))
        self.st7735.display(self.img)
    
    def run(self, log_interval=60):
        """
        Main running loop
        
        Args:
            log_interval (int): Seconds between data logging (default: 60)
        """
        logger.info(f"Starting data collection with {log_interval}s logging interval")
        logger.info("Press Ctrl+C to exit cleanly")
        
        last_log_time = 0
        
        try:
            while True:
                current_time = time.time()
                
                # Read sensors
                reading = self.read_sensors()
                
                # Handle proximity sensor for display wake and page cycling
                proximity = reading.get('proximity', 0)
                
                # Check if proximity should wake the display
                display_woken = self.handle_proximity_wake(proximity)
                
                # Handle display cycling with proximity sensor (only if display is on)
                if (self.display_on and proximity and proximity > 1500 and 
                    current_time - self.last_page > self.delay and not display_woken):
                    self.mode += 1
                    self.mode %= len(self.variables)
                    self.last_page = current_time
                    self.last_activity_time = current_time  # Reset activity timer
                
                # Check for display timeout
                self.check_display_timeout()
                
                # Display current mode (only if display is on)
                if self.display_on:
                    var_name = self.variables[self.mode]
                    var_value = reading.get(var_name.replace('oxidised', 'oxidised').replace('reduced', 'reduced'))
                    var_unit = self.units[self.mode]
                    
                    self.display_text(var_name, var_value, var_unit)
                
                # Log data at specified interval
                if current_time - last_log_time >= log_interval:
                    # Get fresh reading with verbose temperature debug for logging
                    log_reading = self.read_sensors(verbose_temp_debug=True)
                    
                    self.save_to_database(log_reading)
                    self.save_to_csv(log_reading)
                    last_log_time = current_time
                    
                    # Log summary to console
                    if log_reading['errors']:
                        logger.warning(f"Errors: {', '.join(log_reading['errors'])}")
                    else:
                        logger.info(f"Data logged: T={log_reading['temperature']:.1f}°C, "
                                  f"P={log_reading['pressure']:.1f}hPa, "
                                  f"H={log_reading['humidity']:.1f}%, "
                                  f"L={log_reading['light']:.0f}lux")
                
                time.sleep(1)  # Update display every second
                
        except KeyboardInterrupt:
            logger.info("Shutting down cleanly...")
            self.cleanup()
    
    def cleanup(self):
        """Clean shutdown"""
        try:
            # Turn off display backlight
            self.st7735.set_backlight(0)
            logger.info("Display backlight turned off")
        except:
            pass
        
        logger.info("Shutdown complete")

def main():
    """Main entry point"""
    # Create logger instance
    enviro_logger = EnviroDataLogger()
    
    # Run with 60-second logging interval (adjust as needed)
    enviro_logger.run(log_interval=60)

if __name__ == "__main__":
    main()
