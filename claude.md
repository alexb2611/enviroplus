# Enviro+ Indoor Air Quality & Smart Home Project

## Project Overview

**Owner:** Alex  
**Hardware:** Raspberry Pi Zero W + Pimoroni Enviro+ HAT  
**Focus Areas:**
- Indoor air quality monitoring
- Smart home integration (MQTT/Home Assistant)
- Data logging and analysis
- Learning web development, databases, IoT platforms

## Hardware Configuration

### Current Setup
- **Platform:** Raspberry Pi Zero W (hostname: zero.local)
- **HAT:** Pimoroni Enviro+ 
- **Python Environment:** ~/home/pi/pyenv (venv sourced at startup)
- **Scripts Location:** ~/home/pi/pyenv/python
- **Status:** ✅ Basic examples working

### Available Sensors
- **BME280:** Temperature, pressure, humidity
- **LTR-559:** Ambient light (lux) and proximity detection  
- **MICS6814:** Gas sensor (CO, NO₂, NH₃, hydrogen, ethanol, hydrocarbons)
- **MEMS Microphone:** Sound level monitoring
- **0.96" Colour LCD:** 160×80 pixel display
- **❌ PMS5003:** Particulate matter sensor (not installed)

## Project Architecture Plan

### Phase 1: Foundation (In Progress)
- [x] Hardware setup and basic examples
- [x] Enhanced data collection script with logging
- [x] Local data storage (SQLite + CSV)
- [x] Comprehensive unit test suite
- [ ] Sensor calibration and baseline establishment
- [ ] Initial data quality assessment

### Phase 2: Data Management
- [ ] Robust logging system with error handling
- [ ] Data validation and quality checks
- [ ] CSV export functionality
- [ ] Basic web dashboard (local)

### Phase 3: Smart Home Integration
- [ ] MQTT broker setup
- [ ] Home Assistant integration
- [ ] Alert system for air quality thresholds
- [ ] Mobile notifications

### Phase 4: Advanced Features
- [ ] Historical data analysis
- [ ] Predictive trends
- [ ] Multi-room sensor network
- [ ] Weather data integration

## Available Code Examples

From Pimoroni repository:
- `all-in-one.py` - Complete sensor display with LCD
- `all-in-one-no-pm.py` - All sensors except particulate matter
- `combined.py` - Enhanced version with warning thresholds
- `weather.py` - Basic BME280 readings
- `gas.py` - MICS6814 gas sensor
- `light.py` - LTR-559 light/proximity
- `lcd.py` - Display control
- `mqtt-all.py` - MQTT publishing example
- `sensorcommunity.py` - Citizen science integration

## Key Technical Considerations

### Sensor Calibration
- **Temperature:** CPU heat compensation (factor = 2.25)
- **Gas sensors:** Require 48h burn-in period for stability
- **Humidity:** Correlation with temperature needed
- **Pressure:** Altitude compensation for local area

### Data Quality
- Moving averages for noisy readings
- Outlier detection and filtering
- Sensor failure detection
- Environmental corrections

### Performance
- Reading frequency vs power consumption
- Display update optimization
- Efficient data compression
- Appropriate sleep cycles

## Development Environment

### Current Tools
- Python 3.x with virtual environment
- Pimoroni enviroplus-python library
- SQLite for local storage (planned)
- Basic web framework (to be selected)

### Planned Additions
- MQTT broker (Mosquitto)
- Home Assistant
- InfluxDB (time-series database)
- Grafana (dashboards)
- Flask/FastAPI (web framework)

## Air Quality Thresholds & Standards

### Indoor Air Quality Guidelines
- **Temperature:** 18-24°C optimal
- **Humidity:** 40-60% optimal (mould prevention)
- **CO₂ equivalent:** <1000ppm good, >1500ppm poor
- **Pressure trends:** Rapid changes indicate weather shifts

### Gas Sensor Interpretation
- **Reducing gases:** Alcohol, hydrogen, ammonia
- **Oxidising gases:** NO₂, ozone
- **NH₃:** Cleaning products, biological processes

## Testing Strategy

### Test Coverage Areas
- **Sensor Reading Functions:** Mocked hardware for reliable testing
- **Data Validation:** Range checks and error handling
- **Database Operations:** SQLite schema and data integrity  
- **File I/O:** CSV creation and writing
- **Error Handling:** Graceful degradation when sensors fail
- **Algorithms:** Temperature compensation and unit conversions

### Test Types
- **Unit Tests:** Individual function testing with mocked dependencies
- **Integration Tests:** Component interaction testing
- **Hardware Tests:** Real sensor testing (marked for optional execution)
- **Data Validation Tests:** Range and type checking

### Running Tests
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
./test_runner.sh all

# Quick tests (no hardware needed)
./test_runner.sh quick

# Coverage report
./test_runner.sh coverage

# Watch mode for development
./test_runner.sh watch
```

### Test Files
- `test_enviro_logger.py` - Main test suite
- `requirements-test.txt` - Testing dependencies
- `pytest.ini` - Pytest configuration
- `test_runner.sh` - Convenient test runner script

## Enhanced Data Logger Features

### Data Storage
- **SQLite Database:** `~/pyenv/python/data/enviro_data.db` - structured data for queries
- **Daily CSV Files:** `~/pyenv/python/data/enviro_data_YYYY-MM-DD.csv` - Excel compatible
- **Log Files:** `~/pyenv/python/enviro_data.log` - system logs and errors

### Key Improvements Over Basic Examples
- Configurable logging intervals (default: 60 seconds)
- Comprehensive error handling - continues running if sensors fail
- Timestamped data with timezone awareness
- Clean shutdown handling (Ctrl+C turns off display)
- Structured object-oriented design for easy extension

### Data Schema
**Database Fields:**
- timestamp, temperature, pressure, humidity, light
- oxidised, reduced, nh3 (gas sensor readings in kΩ)
- cpu_temp (for monitoring compensation)
- errors (JSON array of any sensor failures)

## Learning Objectives

### Technical Skills to Develop
- [ ] MQTT protocol and broker setup
- [ ] Home Assistant configuration
- [ ] Time-series database design
- [ ] Web dashboard creation
- [ ] API development
- [ ] IoT security best practices

### Domain Knowledge
- [ ] Indoor air quality standards
- [ ] Sensor physics and limitations
- [ ] Environmental data interpretation
- [ ] Smart home ecosystems

## Progress Log

### Session 1 (Current)
- ✅ Hardware confirmed working
- ✅ Example scripts reviewed
- ✅ Project scope defined
- ✅ Documentation framework created
- ✅ Enhanced data logger created with dual storage (SQLite + CSV)
- ✅ Comprehensive unit test suite with mocked hardware
- ✅ Test runner and configuration setup
- 🎯 **Next:** Deploy enhanced logger, run tests, establish baseline readings

## Useful Resources

### Documentation
- [Pimoroni Enviro+ Documentation](https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-enviro-plus)
- [BME280 Datasheet](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)
- [MICS6814 Gas Sensor Datasheet](https://www.sgxsensortech.com/content/uploads/2015/02/1143_Datasheet-MiCS-6814-rev-8.pdf)

### Standards & Guidelines
- [WHO Air Quality Guidelines](https://www.who.int/publications/i/item/9789240034228)
- [UK Building Regulations Part F](https://www.gov.uk/government/publications/ventilation-approved-document-f)

## Ideas for Extensions

### Educational
- Weather prediction based on pressure trends
- Air quality science experiments
- Simple alerting system for room conditions
- Data visualization projects

### Home Applications
- Cooking detection and ventilation control
- Humidity monitoring for condensation prevention
- Air quality alerts during cleaning
- Sleep environment optimization

### Technical Challenges
- Solar power integration
- Wireless sensor network
- Machine learning for pattern recognition
- Integration with external weather APIs

## Notes & Decisions

- Using existing Pimoroni examples as foundation
- SQLite for initial data storage (simple, embedded)
- Will build web dashboard before Home Assistant integration
- Focus on reliability and data quality first

---

**Last Updated:** July 11, 2025  
**Current Status:** Foundation phase - basic setup complete