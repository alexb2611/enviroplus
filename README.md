# Enviro+ Indoor Air Quality Monitor & Smart Home Integration

A comprehensive environmental monitoring system built with the Pimoroni Enviro+ HAT for Raspberry Pi, designed for indoor air quality monitoring, data logging, and smart home integration.

## 🌟 Features

- **Real-time Environmental Monitoring**
  - Temperature (CPU heat compensated)
  - Humidity
  - Barometric pressure
  - Light levels
  - Gas concentrations (CO, NO₂, NH₃, hydrocarbons)
  - Proximity detection

- **Data Storage & Analysis**
  - SQLite database for structured queries
  - Daily CSV exports for Excel analysis
  - Comprehensive error logging
  - Timestamped data with timezone support

- **Smart Home Ready**
  - MQTT support for Home Assistant integration
  - Configurable alerting thresholds
  - Web dashboard (planned)
  - Mobile notifications (planned)

- **Robust & Reliable**
  - Comprehensive unit test suite
  - Graceful error handling - continues running if sensors fail
  - 24/7 operation capability
  - Clean shutdown procedures

## 🛠️ Hardware Requirements

- **Raspberry Pi Zero 2W** (or compatible)
- **Pimoroni Enviro+ HAT**
- MicroSD card (16GB+ recommended)
- Power supply

### Sensors Included
- **BME280**: Temperature, pressure, humidity
- **LTR-559**: Ambient light and proximity
- **MICS6814**: Gas sensor (multiple gas types)
- **MEMS Microphone**: Sound level monitoring
- **0.96" Colour LCD**: Real-time display

*Note: This project doesn't require the optional PMS5003 particulate matter sensor*

## 🌡️ Temperature Calibration (IMPORTANT!)

**Critical Finding: Pi Zero 2W requires much more aggressive temperature compensation than standard Pimoroni examples.**

### Calibration Results
- **Standard Pimoroni factor**: 2.25
- **Pi Zero 2W optimized factor**: 1.4 (38% more aggressive)
- **Heat compensation**: Removes ~10°C of CPU heat soak
- **Accuracy achieved**: ±0.1°C (verified with DHT11 reference sensor)

### Calibration Process
1. **Reference sensor**: DHT11 placed in same location as Enviro+
2. **Iterative testing**: Started with factor 2.25, adjusted to 3.2, then 2.0, finally 1.4
3. **Verification**: Enviro+ 26.1°C vs DHT11 26.0°C = 0.1°C accuracy

### Why Different?
- **Compact form factor**: Pi Zero 2W generates concentrated heat
- **Sensor placement**: BME280 positioned directly above CPU
- **Limited airflow**: Sensor enclosed by HAT assembly
- **Continuous operation**: Steady heat generation during 24/7 monitoring

### Debug Output Added
```
Temperature compensation: Raw=35.6°C, CPU=49.5°C, Compensated=26.1°C, Factor=1.4
```

**If you're using Pi Zero 2W + Enviro+, start with compensation factor 1.4 for accurate readings!**

---

## 🚀 Quick Start

### 1. Hardware Setup
1. Attach the Enviro+ HAT to your Raspberry Pi
2. Install Raspberry Pi OS and enable I2C/SPI
3. Connect to your Pi via SSH

### 2. Software Installation
```bash
# Clone the repository
git clone https://github.com/your-username/enviroplus.git
cd enviroplus

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Pimoroni libraries (on Raspberry Pi)
curl https://get.pimoroni.com/enviroplus | bash
```

### 3. Run the Data Logger
```bash
python enhanced_enviro_logger.py
```

The system will:
- Display real-time readings on the LCD
- Log data every 60 seconds to SQLite database and CSV files
- Handle sensor errors gracefully
- Create data files in `./data/` directory

### 4. Interact with the Display
- **Proximity sensor**: Wave your hand near the sensor to cycle through different readings
- **Ctrl+C**: Cleanly shutdown and turn off display

## 📊 Data Output

### Database Storage
SQLite database: `data/enviro_data.db`
```sql
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    temperature REAL,
    pressure REAL,
    humidity REAL,
    light REAL,
    oxidised REAL,    -- Gas sensor readings in kΩ
    reduced REAL,
    nh3 REAL,
    cpu_temp REAL,    -- For temperature compensation
    errors TEXT       -- JSON array of any sensor failures
);
```

### CSV Export
Daily files: `data/enviro_data_YYYY-MM-DD.csv`
- Excel compatible
- Timestamps in ISO format
- Error information included

## 🧪 Testing

Comprehensive test suite with mocked hardware for reliable testing:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
./test_runner.sh all

# Quick tests (no hardware needed)
./test_runner.sh quick

# Coverage report
./test_runner.sh coverage

# Help
./test_runner.sh help
```

### Test Coverage
- Sensor reading functions with mocked hardware
- Database operations and schema validation
- CSV file creation and data integrity
- Error handling and graceful degradation
- Temperature compensation algorithms
- Data validation and range checking

## 📱 Smart Home Integration (Planned)

### MQTT Support
- Publish sensor data to MQTT broker
- Home Assistant auto-discovery
- Configurable update intervals
- Alert thresholds

### Web Dashboard
- Real-time sensor readings
- Historical data visualization
- Configuration management
- Mobile-responsive design

## 🔧 Configuration

Key settings can be adjusted in the `EnviroDataLogger` class:

```python
# Logging interval (seconds)
enviro_logger.run(log_interval=60)

# Temperature compensation factor (calibrated for Pi Zero 2W)
self.temp_compensation_factor = 1.4  # Removes ~10°C CPU heat

# Data directory
data_dir = '/home/pi/pyenv/python/data'
```

## 📈 Air Quality Interpretation

### Temperature
- **Optimal**: 18-24°C
- **CPU Heat Compensation**: Applied automatically using 5-point moving average
- **Pi Zero 2W Factor**: 1.4 (removes ~10°C heat soak)
- **Accuracy**: ±0.1°C with proper calibration

### Humidity
- **Optimal**: 40-60%
- **< 40%**: Too dry, potential respiratory issues
- **> 60%**: Risk of mould growth

### Gas Sensors (in kΩ)
- **Reducing gases**: Lower resistance = higher concentration
- **Oxidising gases**: Higher resistance = higher concentration  
- **Baseline establishment**: Requires 24-48 hours for stability

### Pressure Trends
- **Rising**: Generally improving weather
- **Falling**: Potential storm systems approaching
- **Rapid changes**: Significant weather events

## 🛡️ Error Handling

The system is designed for 24/7 operation with robust error handling:

- **Sensor failures**: Continue with remaining sensors, log errors
- **File system errors**: Retry operations, fallback strategies
- **Database issues**: Continue with CSV logging
- **Display problems**: Continue data logging in background

## 🔄 Development Workflow

1. **Make changes** to the code
2. **Run tests**: `./test_runner.sh quick`
3. **Check coverage**: `./test_runner.sh coverage`
4. **Test on hardware**: Deploy to Raspberry Pi
5. **Monitor logs**: Check for any issues

## 📝 Project Structure

```
enviroplus/
├── enhanced_enviro_logger.py  # Main application
├── tests/
│   └── test_enviro_logger.py  # Test suite
├── data/                      # Data storage (created at runtime)
├── requirements.txt           # Main dependencies
├── requirements-test.txt      # Test dependencies
├── pytest.ini               # Test configuration
├── test_runner.sh           # Test runner script
├── claude.md               # Project documentation
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run the test suite
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Pimoroni** for the excellent Enviro+ HAT and examples
- **Raspberry Pi Foundation** for the platform
- Built on the foundation of Pimoroni's example code

## 📞 Support

For issues and questions:
1. Check the test suite output for hardware issues
2. Review the log files in `data/enviro_data.log`
3. Open an issue on GitHub

---

**Happy Monitoring! 🌱**
