# 🚀 Simple Setup Guide - Personal Project

Quick and easy setup for your LaCentrale scraper personal project.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database
- OR Docker (for easier database setup)

## ⚡ Quick Start (2 methods)

### Method 1: Use Existing Database (Recommended)

```bash
# 1. Update your database credentials in optimized_scraping.py (line 32)
# connection_string = "postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/lacentrale_db"

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Enable incremental scraping (to add to existing 79k cars)
# In optimized_scraping.py, set: incremental_mode = True

# 4. Run the scraper
python optimized_scraping.py
```

### Method 2: Docker Tools Only (Optional)

```bash
# 1. Start PgAdmin to view your existing database
docker-compose up -d pgadmin

# 2. Access web interface: http://localhost:8080
# Email: admin@lacentrale.com / Password: admin123

# 3. Add your existing database server in PgAdmin:
# Host: host.docker.internal (Windows/Mac) or 172.17.0.1 (Linux)
# Port: 5432
# Database: lacentrale_db
# Username: postgres
# Password: your_actual_password
```

### Method 2: Local PostgreSQL

```bash
# 1. Install PostgreSQL locally
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt install postgresql

# 2. Create database
createdb lacentrale_db

# 3. Update password in optimized_scraping.py (line 32)
# connection_string = "postgresql://postgres:your_password@localhost:5432/lacentrale_db"

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run the scraper
python optimized_scraping.py
```

## 🔧 Configuration

### Simple Password Setup

**Option A: Direct edit (simplest)**
```python
# In optimized_scraping.py line 32, change:
connection_string = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/lacentrale_db"
```

**Option B: Environment file (recommended)**
```bash
# Create .env file
echo "POSTGRES_PASSWORD=your_password_here" > .env

# Uncomment lines 37-41 in optimized_scraping.py
```

### Scraping Settings

Edit in `optimized_scraping.py`:
```python
start_page = 1          # Starting page
end_page = 50           # Ending page  
num_workers = 2         # Parallel workers (2-3 for personal use)
incremental_mode = True # Only scrape new cars
```

## 📊 Database Access

### With Docker
```bash
# Access database
docker-compose exec postgres psql -U postgres -d lacentrale_db

# View data
SELECT make, model, price FROM car_listings_flat LIMIT 10;
```

### Local PostgreSQL
```bash
# Access database
psql -U postgres -d lacentrale_db

# View data
SELECT make, model, price FROM car_listings_flat LIMIT 10;
```

### PgAdmin (Web Interface)
```bash
# Start with Docker
docker-compose up -d pgladmin

# Access: http://localhost:8080
# Email: admin@lacentrale.com
# Password: (from your .env file)
```

## 🚨 Troubleshooting

### "Connection refused" error
```bash
# Make sure PostgreSQL is running
docker-compose ps  # Check if postgres container is up

# Or for local PostgreSQL
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # Mac
```

### "Password authentication failed"
```bash
# Check your password in optimized_scraping.py matches your .env file
# Or reset PostgreSQL password
```

### Chrome/Selenium issues
```bash
# Update Chrome driver
pip install --upgrade undetected-chromedriver

# Or run in Docker mode
docker-compose up selenium-chrome
```

## 📈 Performance Tips

### For Personal Use
- **Workers**: Use 2-3 workers max
- **Pages**: Start with 10-50 pages for testing
- **Mode**: Use "optimized" for faster scraping
- **Incremental**: Enable to avoid re-scraping

### Resource Usage
- **Memory**: 1-2GB RAM
- **CPU**: 1-2 cores
- **Disk**: 1GB for 10,000 cars
- **Network**: 10-100 MB/hour

## 📁 Project Structure (Simplified)

```
lacentrale-scraper/
├── optimized_scraping.py    # Main scraper (edit password here)
├── requirements.txt         # Python dependencies
├── .env                     # Your passwords (create from env.example)
├── docker-compose.yml       # Database setup
├── data/                    # Scraped data
├── database/               # Database code
│   ├── db_utils.py
│   └── schema.py
└── scraping/               # Scraping engine
    ├── hybrid_scraper.py
    └── utils.py
```

## 🎯 What You Need to Edit

1. **Password**: Line 32 in `optimized_scraping.py`
2. **Pages**: Lines 80-81 in `optimized_scraping.py` 
3. **Workers**: Line 91 in `optimized_scraping.py`

That's it! Everything else works out of the box.

## 📞 Need Help?

1. **Database issues**: Check PostgreSQL is running
2. **Scraping issues**: Reduce number of workers
3. **Performance**: Enable incremental mode
4. **Data access**: Use PgAdmin web interface

---

🎉 **Happy scraping!** Start with small page ranges (1-10) to test everything works.
