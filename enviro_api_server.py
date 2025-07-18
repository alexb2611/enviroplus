#!/usr/bin/env python3
"""
Enviro+ API Server for Dashboard Integration
Serves real-time environmental data via REST API compatible with existing Streamlit dashboard

Author: Alex (with Claude)
Date: July 2025
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import glob
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = "./data"  # Where your enviro data is stored
DB_PATH = os.path.join(DATA_DIR, "enviro_data.db")
CSV_PATTERN = os.path.join(DATA_DIR, "enviro_data_*.csv")

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

class EnviroAPIServer:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "enviro_data.db")
        
    def get_latest_reading(self):
        """Get the most recent sensor reading from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest reading
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
                # Convert to format compatible with dashboard
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
                    'battery': 4.1,  # Enviro+ is USB powered
                    'power_source': 'USB',
                    'rssi': -65,  # Not applicable for Enviro+ but required by dashboard
                    'snr': 10.0,   # Not applicable for Enviro+ but required by dashboard
                    'transmitter_type': 'enviro_plus',
                    'charging': 'N/A',  # Not applicable for Enviro+
                    'interval': None,
                    'uptime': None,
                    'sensor_type': 'enviro_plus',
                    'location': 'living_room',  # Update as needed
                    'errors': json.loads(row[9]) if row[9] else []
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting latest reading: {e}")
            return None
    
    def get_recent_readings(self, hours=24):
        """Get recent readings for trends."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate cutoff time
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Query recent readings
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
                # Convert timestamps
                df['datetime'] = pd.to_datetime(df['timestamp'])
                df['time'] = df['datetime'].dt.strftime('%H:%M:%S')
                
                # Convert to list of dictionaries
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
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent readings: {e}")
            return []
    
    def get_daily_stats(self, days=7):
        """Get daily statistics for the specified number of days."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate cutoff time
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Query for daily stats
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as readings_count,
                    AVG(temperature) as avg_temp,
                    MIN(temperature) as min_temp,
                    MAX(temperature) as max_temp,
                    AVG(humidity) as avg_humidity,
                    MIN(humidity) as min_humidity,
                    MAX(humidity) as max_humidity,
                    AVG(pressure) as avg_pressure,
                    MIN(pressure) as min_pressure,
                    MAX(pressure) as max_pressure,
                    AVG(light) as avg_light,
                    MIN(light) as min_light,
                    MAX(light) as max_light
                FROM sensor_readings 
                WHERE timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """
            
            df = pd.read_sql_query(query, conn, params=[cutoff_time])
            conn.close()
            
            if not df.empty:
                # Round numeric values
                numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
                df[numeric_columns] = df[numeric_columns].round(2)
                
                return df.to_dict('records')
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []
    
    def get_system_status(self):
        """Get system status and health information."""
        try:
            # Count total readings
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            total_readings = cursor.fetchone()[0]
            
            # Get latest timestamp
            cursor.execute("SELECT MAX(timestamp) FROM sensor_readings")
            latest_timestamp = cursor.fetchone()[0]
            
            # Get data age
            if latest_timestamp:
                latest_time = datetime.fromisoformat(latest_timestamp)
                data_age_minutes = (datetime.now() - latest_time).total_seconds() / 60
            else:
                data_age_minutes = float('inf')
            
            conn.close()
            
            # Check CSV files
            csv_files = glob.glob(CSV_PATTERN)
            
            return {
                'total_readings': total_readings,
                'latest_timestamp': latest_timestamp,
                'data_age_minutes': round(data_age_minutes, 1),
                'csv_files_count': len(csv_files),
                'system_type': 'enviro_plus',
                'location': 'living_room',
                'status': 'online' if data_age_minutes < 5 else 'offline',
                'uptime_hours': None,  # Not tracked for Enviro+
                'database_path': self.db_path,
                'data_directory': self.data_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Initialize API server
api_server = EnviroAPIServer()

# API Routes - Compatible with existing dashboard
@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get latest sensor reading - compatible with dashboard format."""
    try:
        latest_reading = api_server.get_latest_reading()
        
        if latest_reading:
            return jsonify({
                'status': 'success',
                'data': latest_reading,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No data available'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in /api/latest: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/recent', methods=['GET'])
def get_recent():
    """Get recent readings for trends."""
    try:
        hours = request.args.get('hours', 24, type=int)
        recent_readings = api_server.get_recent_readings(hours)
        
        return jsonify({
            'status': 'success',
            'data': recent_readings,
            'count': len(recent_readings),
            'hours': hours
        })
        
    except Exception as e:
        logger.error(f"Error in /api/recent: {e}")
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get daily statistics."""
    try:
        days = request.args.get('days', 7, type=int)
        daily_stats = api_server.get_daily_stats(days)
        
        return jsonify({
            'status': 'success',
            'data': daily_stats,
            'days': days
        })
        
    except Exception as e:
        logger.error(f"Error in /api/stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status."""
    try:
        system_status = api_server.get_system_status()
        
        return jsonify({
            'status': 'success',
            'data': system_status
        })
        
    except Exception as e:
        logger.error(f"Error in /api/status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'enviro_plus_api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Enviro+-specific endpoints
@app.route('/api/enviro/gas', methods=['GET'])
def get_gas_readings():
    """Get recent gas sensor readings."""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = sqlite3.connect(api_server.db_path)
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = """
            SELECT timestamp, oxidised, reduced, nh3
            FROM sensor_readings 
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """
        
        df = pd.read_sql_query(query, conn, params=[cutoff_time])
        conn.close()
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'])
            readings = df.to_dict('records')
        else:
            readings = []
        
        return jsonify({
            'status': 'success',
            'data': readings,
            'count': len(readings)
        })
        
    except Exception as e:
        logger.error(f"Error in /api/enviro/gas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/enviro/temperature-compensation', methods=['GET'])
def get_temperature_compensation():
    """Get temperature compensation data."""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = sqlite3.connect(api_server.db_path)
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = """
            SELECT timestamp, temperature, cpu_temp
            FROM sensor_readings 
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """
        
        df = pd.read_sql_query(query, conn, params=[cutoff_time])
        conn.close()
        
        if not df.empty:
            # Calculate compensation difference
            df['compensation_delta'] = df['cpu_temp'] - df['temperature']
            readings = df.to_dict('records')
        else:
            readings = []
        
        return jsonify({
            'status': 'success',
            'data': readings,
            'count': len(readings)
        })
        
    except Exception as e:
        logger.error(f"Error in /api/enviro/temperature-compensation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Enviro+ API Server...")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Database path: {DB_PATH}")
    
    # Verify data directory exists
    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory {DATA_DIR} does not exist!")
        exit(1)
    
    # Verify database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database {DB_PATH} does not exist!")
        exit(1)
    
    # Start the server
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=8080,       # Use same port as your dashboard expects
        debug=False,     # Set to True for development
        threaded=True
    )
