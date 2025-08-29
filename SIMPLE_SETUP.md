# 🚀 Simple Setup Guide - LaCentrale Scraper

Quick and easy setup for your LaCentrale scraper project using virtual environment.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database (local installation)

## ⚡ Quick Start

### 1. Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

**Option A: Use Existing Database (Recommended)**
```bash
# Update your database credentials in optimized_scraping.py (line 32)
# connection_string = "postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/lacentrale_db"
```

**Option B: Create New Database**
```bash
# Install PostgreSQL locally
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt install postgresql

# Create database
createdb lacentrale_db
```

### 3. Configuration

**Simple Configuration (Edit optimized_scraping.py)**
```python
# Line 32 - Update your database password:
connection_string = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/lacentrale_db"

# Lines 48-51 - Configure scraping:
start_page = 1          # Starting page
end_page = 50           # Ending page  
num_workers = 2         # Parallel workers (2-3 recommended)
incremental_mode = True # Only scrape new cars
```

**Advanced Configuration (Using .env file)**
```bash
# Create .env file from template
cp env.example .env

# Edit .env file with your settings
# Uncomment lines 40-44 in optimized_scraping.py to use .env
```

### 4. Run the Scraper

```bash
# Make sure virtual environment is activated
python optimized_scraping.py
```

## 🔧 Environment File Configuration

Create a `.env` file for advanced configuration:

```env
# Database
POSTGRES_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lacentrale_db
DB_USER=postgres

# Scraping Settings
SCRAPING_MODE=optimized
START_PAGE=1
END_PAGE=50
NUM_WORKERS=2
INCREMENTAL_MODE=true
DATABASE_APPROACH=normalized

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## 📊 Database Access

### PostgreSQL Command Line
```bash
# Access database
psql -U postgres -d lacentrale_db

# View data
SELECT make, model, price FROM car_listings_flat LIMIT 10;

# Count total cars
SELECT COUNT(*) FROM car_listings;
```

### Database Statistics
```bash
# Run the scraper to see statistics
python optimized_scraping.py

# Or check database directly
psql -U postgres -d lacentrale_db -c "SELECT COUNT(*) as total_cars FROM car_listings;"
```

## 🚨 Troubleshooting

### "Connection refused" error
```bash
# Check if PostgreSQL is running
# Windows: Check Services or Task Manager
# Mac: brew services list | grep postgres
# Linux: sudo systemctl status postgresql

# Start PostgreSQL if stopped
# Mac: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

### "Password authentication failed"
```bash
# Reset PostgreSQL password
sudo -u postgres psql
\password postgres

# Or check your password in optimized_scraping.py matches your database
```

### Chrome/Selenium issues
```bash
# Update Chrome driver
pip install --upgrade undetected-chromedriver

# Reduce number of workers if issues persist
# Edit optimized_scraping.py: num_workers = 1
```

### Virtual Environment Issues
```bash
# Deactivate and recreate if needed
deactivate
rm -rf venv  # or rmdir /s venv on Windows
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## 📈 Performance Tips

### For Personal Use
- **Workers**: Use 2-3 workers max to avoid detection
- **Pages**: Start with 10-50 pages for testing
- **Mode**: Use "optimized" for faster scraping
- **Incremental**: Enable to avoid re-scraping existing cars

### Resource Usage
- **Memory**: 1-2GB RAM
- **CPU**: 1-2 cores per worker
- **Disk**: ~100MB per 1,000 cars
- **Network**: 10-50 MB/hour depending on pages

## 📁 Project Structure

```
lacentrale-scraper/
├── optimized_scraping.py    # Main scraper (edit database config here)
├── requirements.txt         # Python dependencies
├── .env                     # Your configuration (optional)
├── SIMPLE_SETUP.md         # This guide
├── README.md               # Full documentation
├── data/                   # Scraped data and state
│   ├── scraping_state.json
│   └── backup/
├── database/               # Database utilities
│   ├── db_utils.py
│   └── schema.py
├── scraping/               # Scraping engine
│   ├── hybrid_scraper.py
│   └── utils.py
└── logs/                   # Application logs
```

## 🎯 What You Need to Edit

**Minimum required changes:**
1. **Database Password**: Line 32 in `optimized_scraping.py`
2. **Page Range**: Lines 48-49 in `optimized_scraping.py` (optional)
3. **Workers**: Line 56 in `optimized_scraping.py` (optional)

**Everything else works out of the box!**

## 📞 Common Commands

```bash
# Start scraping (full setup)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python optimized_scraping.py

# Quick restart (environment already setup)
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
python optimized_scraping.py

# Check database
psql -U postgres -d lacentrale_db -c "SELECT COUNT(*) FROM car_listings;"

# Update dependencies
pip install --upgrade -r requirements.txt
```

## ✅ Success Indicators

You'll know everything is working when you see:
- ✅ "HYBRID SCRAPER INITIALIZED"
- ✅ "Database setup completed successfully!"
- ✅ "Incremental mode enabled!" (if using incremental mode)
- ✅ "Starting MAXIMUM SPEED scraping..."
- ✅ Cars being found and saved to database

---

🎉 **Happy scraping!** Start with small page ranges (1-10) to test everything works before scaling up.