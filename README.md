# 🚀 LaCentrale Car Scraper

A high-performance web scraper for LaCentrale car listings with PostgreSQL database storage and intelligent duplicate detection.

## ✨ Features

- **🔥 High Performance**: Parallel processing with up to 20-30x speed improvement
- **🎯 Smart Scraping**: Undetected Chrome driver with anti-detection measures
- **💾 Database Storage**: Direct PostgreSQL insertion with optimized schema
- **🔄 Incremental Mode**: Only scrape new listings to avoid duplicates
- **📊 Real-time Stats**: Live progress tracking and comprehensive reporting
- **🛡️ Error Handling**: Automatic retries and graceful failure recovery
- **🔍 Data Validation**: Comprehensive car data validation before storage

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd lacentrale-scraper

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure database (edit line 32 in optimized_scraping.py)
# connection_string = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/lacentrale_db"

# 6. Run the scraper
python optimized_scraping.py
```

## ⚙️ Configuration

### Basic Configuration (optimized_scraping.py)

```python
# Database connection
connection_string = "postgresql://postgres:your_password@localhost:5432/lacentrale_db"

# Scraping settings
start_page = 1              # Starting page
end_page = 50               # Ending page
num_workers = 2             # Parallel workers (2-3 recommended)
incremental_mode = True     # Only scrape new cars
```

### Advanced Configuration (.env file)

Create a `.env` file from `env.example`:

```bash
cp env.example .env
```

Edit `.env` with your settings:
```env
POSTGRES_PASSWORD=your_secure_password_here
START_PAGE=1
END_PAGE=50
NUM_WORKERS=2
INCREMENTAL_MODE=true
```

Then uncomment lines 40-44 in `optimized_scraping.py` to use environment variables.

## 🏗️ Database Schema

### Normalized Approach (Recommended)
- **manufacturers**: Car manufacturers (Toyota, BMW, etc.)
- **car_models**: Car models per manufacturer
- **vehicles**: Vehicle specifications
- **dealers**: Dealer information
- **car_listings**: Main listings table

### Denormalized Approach (Simpler)
- **car_listings_flat**: All data in single table

## 📊 Performance Features

### Speed Optimizations
- **Parallel Processing**: Multiple Chrome instances working simultaneously
- **Optimized Chrome**: Disabled images, plugins, and unnecessary features
- **Fast Delays**: Reduced wait times (0.1-0.3 seconds)
- **Smart Buffering**: 3000-car memory buffer before database flush
- **Direct DB Insertion**: No intermediate JSON files

### Anti-Detection
- **Undetected ChromeDriver**: Bypasses most detection systems
- **Random Delays**: Human-like browsing patterns
- **User Agent Rotation**: Multiple browser signatures
- **Stealth Mode**: Hidden automation indicators

## 🔄 Incremental Scraping

The scraper supports intelligent incremental mode:

```python
incremental_mode = True  # Enable in optimized_scraping.py
```

**Benefits:**
- Only processes NEW car listings
- Skips existing cars automatically
- Maintains state between sessions
- Saves time and resources
- Perfect for daily updates

**How it works:**
1. Loads existing car references from database
2. Compares scraped cars against known cars
3. Only processes truly new listings
4. Updates state file automatically

## 📈 Usage Examples

### Basic Scraping
```bash
# Scrape pages 1-10 with default settings
python optimized_scraping.py
```

### Custom Page Range
Edit `optimized_scraping.py`:
```python
start_page = 100
end_page = 200
```

### High-Speed Scraping
```python
num_workers = 4        # More parallel workers
end_page = 1000       # Larger page range
```

### Daily Updates
```python
incremental_mode = True  # Only new cars
start_page = 1
end_page = 50           # Check recent pages
```

## 📊 Database Queries

### Basic Statistics
```sql
-- Total cars
SELECT COUNT(*) FROM car_listings;

-- Price statistics  
SELECT MIN(price), MAX(price), AVG(price) FROM car_listings;

-- Popular manufacturers
SELECT m.name, COUNT(*) 
FROM car_listings cl 
JOIN vehicles v ON cl.vehicle_id = v.id 
JOIN manufacturers m ON v.manufacturer_id = m.id 
GROUP BY m.name 
ORDER BY COUNT(*) DESC 
LIMIT 10;
```

### Advanced Queries
```sql
-- Cars under 20k euros
SELECT * FROM car_listings WHERE price < 20000;

-- BMW cars with low mileage
SELECT cl.*, m.name as make, cm.name as model 
FROM car_listings cl
JOIN vehicles v ON cl.vehicle_id = v.id
JOIN manufacturers m ON v.manufacturer_id = m.id  
JOIN car_models cm ON v.car_model_id = cm.id
WHERE m.name = 'BMW' AND cl.mileage < 50000;

-- Recent listings
SELECT * FROM car_listings 
WHERE first_online_date >= CURRENT_DATE - INTERVAL '7 days';
```

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
# Windows: Check Services
# Mac: brew services list | grep postgres  
# Linux: sudo systemctl status postgresql

# Verify credentials in optimized_scraping.py
```

**Chrome/Selenium Issues**
```bash
# Update ChromeDriver
pip install --upgrade undetected-chromedriver

# Reduce workers if detection issues
num_workers = 1  # In optimized_scraping.py
```

**Memory Issues**
```bash
# Reduce buffer size in hybrid_scraper.py
self.buffer_size = 1000  # Default is 3000
```

**Performance Issues**
```bash
# Enable all optimizations
optimized_mode = True
parallel_mode = True
num_workers = 2  # Start with 2, increase gradually
```

## 📁 Project Structure

```
lacentrale-scraper/
├── optimized_scraping.py      # Main entry point
├── requirements.txt           # Dependencies
├── env.example               # Configuration template
├── SIMPLE_SETUP.md          # Quick setup guide
├── README.md                # This file
├── data/                    # Scraped data and state
│   ├── scraping_state.json  # Incremental mode state
│   └── backup/             # Emergency backups
├── database/               # Database layer
│   ├── db_utils.py         # Database operations
│   └── schema.py          # Table definitions
├── scraping/              # Scraping engine
│   ├── hybrid_scraper.py  # Main scraper class
│   └── utils.py          # Utilities and helpers
├── logs/                 # Application logs
└── tests/               # Test files
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_scraper.py
```

### Code Quality
```bash
# Format code
black .

# Lint code  
flake8 .

# Type checking
mypy .
```

## 📊 Performance Metrics

### Speed Comparison
- **Normal Mode**: ~1 car per second
- **Optimized Mode**: ~20-30 cars per second
- **Parallel Mode**: ~60-100 cars per second (3 workers)

### Resource Usage
- **Memory**: 1-2GB RAM (depends on workers)
- **CPU**: 1-2 cores per worker
- **Storage**: ~100MB per 1,000 cars
- **Network**: 10-50 MB/hour

### Recommended Settings
```python
# Personal use
num_workers = 2
buffer_size = 2000
optimized_mode = True

# Production use  
num_workers = 3-4
buffer_size = 3000
optimized_mode = True
incremental_mode = True
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This scraper is for educational and personal use only. Please respect LaCentrale's robots.txt and terms of service. Use responsibly and don't overload their servers.

## 📞 Support

- **Documentation**: See SIMPLE_SETUP.md for quick start
- **Issues**: Check existing issues or create new ones
- **Performance**: Start with small page ranges to test setup

---

🎉 **Happy scraping!** Remember to start small and scale up gradually.