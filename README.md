# 🚗 LaCentrale Scraper

A high-performance, production-ready web scraper for LaCentrale car listings with Docker support, PostgreSQL storage, and advanced anti-detection features.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-compose-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

### 🚀 High Performance
- **Hybrid Scraping**: Direct PostgreSQL insertion with smart buffering
- **Parallel Processing**: Multi-threaded scraping with 2-5 concurrent workers
- **Optimized Mode**: 20-30x faster than standard scraping
- **Incremental Scraping**: Only fetch new listings since last run

### 🛡️ Anti-Detection
- **Undetected Chrome**: Stealth browsing with undetected-chromedriver
- **Human-like Behavior**: Random delays, gradual scrolling, mouse movements
- **Rotating User Agents**: Multiple browser fingerprints
- **Docker Isolation**: Clean browser environments

### 💾 Database Support
- **Dual Schema**: Normalized (data integrity) or Denormalized (performance)
- **Auto-Indexing**: Optimized database indexes for fast queries
- **Bulk Insertion**: Efficient batch processing
- **JSON Backup**: Automatic fallback on database errors

### 🐳 Docker Ready
- **Complete Docker Compose**: PostgreSQL + PgAdmin + Selenium + Jupyter
- **Multi-stage Builds**: Optimized production containers
- **Environment Configuration**: Easy deployment with .env files
- **Health Checks**: Automatic service monitoring

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** Python 3.11+ with PostgreSQL 15+
- **4GB+ RAM** (for Chrome instances)
- **5GB+ disk space** (for data storage)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://gitlab.com/your-username/lacentrale-scraper.git
cd lacentrale-scraper

# Copy environment configuration
cp env.example .env

# Edit .env with your settings
nano .env
```

### 2. Docker Deployment (Recommended)

```bash
# Start core services (PostgreSQL + PgAdmin)
docker-compose up -d postgres pgadmin

# Wait for database to be ready (30-60 seconds)
docker-compose logs postgres

# Run the scraper
docker-compose --profile scraper up scraper

# Or start everything including Jupyter for analysis
docker-compose --profile analysis up -d
```

### 3. Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database (update connection string in optimized_scraping.py)
# Create PostgreSQL database: lacentrale_db

# Run the scraper
python optimized_scraping.py
```

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `your_secure_password` | PostgreSQL password |
| `SCRAPING_MODE` | `optimized` | Scraping mode: optimized/parallel/normal |
| `START_PAGE` | `1` | Starting page number |
| `END_PAGE` | `50` | Ending page number |
| `NUM_WORKERS` | `2` | Parallel workers (2-5 recommended) |
| `INCREMENTAL_MODE` | `true` | Only scrape new listings |
| `DATABASE_APPROACH` | `normalized` | Database schema: normalized/denormalized |

### Scraping Modes

| Mode | Speed | Detection Risk | Use Case |
|------|-------|----------------|----------|
| `normal` | 1x | Low | Safe, long-running |
| `optimized` | 10-20x | Medium | Fast data collection |
| `parallel` | 20-30x | High | Maximum speed |

## 📊 Usage Examples

### Basic Scraping

```bash
# Scrape 100 pages with default settings
docker-compose --profile scraper run --rm scraper

# Custom page range
docker-compose --profile scraper run --rm -e START_PAGE=1 -e END_PAGE=200 scraper

# Maximum speed mode
docker-compose --profile scraper run --rm -e SCRAPING_MODE=parallel -e NUM_WORKERS=5 scraper
```

### Database Operations

```python
# Connect to database
from database.db_utils import DatabaseManager

db = DatabaseManager(
    "postgresql://postgres:password@localhost:5432/lacentrale_db",
    approach="normalized"
)

# Query examples
with db.get_session() as session:
    # Count total cars
    count = session.query(CarListings).count()
    print(f"Total cars: {count}")
    
    # Find cars by make
    bmw_cars = session.query(CarListings).join(Vehicles).join(Manufacturers)\
        .filter(Manufacturers.name == "BMW").all()
```

### Data Analysis

```bash
# Start Jupyter for analysis
docker-compose --profile analysis up -d jupyter

# Access at http://localhost:8888
# Username: jupyter (no password)
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scraper       │────│   PostgreSQL    │────│    PgAdmin      │
│   (Python)      │    │   (Database)    │    │     (UI)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Selenium      │──────────────┘
                        │   (Chrome)      │
                        └─────────────────┘
```

### Data Flow

1. **Scraper** navigates LaCentrale pages using undetected Chrome
2. **Parser** extracts JSON data and validates structure
3. **Buffer** accumulates cars in memory (2000-3000 items)
4. **Database** receives bulk insertions with conflict resolution
5. **Backup** creates JSON files on database errors

### Database Schema

#### Normalized (Recommended)
- `manufacturers` - Car brands (Peugeot, BMW, etc.)
- `car_models` - Models per brand (Golf, A4, etc.)
- `dealers` - Seller information
- `vehicles` - Vehicle specifications
- `car_listings` - Main listing data

#### Denormalized (Performance)
- `car_listings_flat` - All data in single table

## 🔧 Development

### Local Development

```bash
# Development container with extra tools
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests
pytest tests/

# Code formatting
black .
flake8 .
```

### Adding Features

1. **Extend Database Schema**: Modify `database/schema.py`
2. **Add Validation**: Update `data/save_data.py`
3. **Enhance Scraping**: Modify `scraping/hybrid_scraper.py`
4. **Update Docker**: Rebuild containers

### Performance Tuning

```python
# Increase buffer size for high-volume scraping
scraper.buffer_size = 5000

# Optimize database connections
db_manager.engine.pool_size = 20
db_manager.engine.max_overflow = 30

# Enable all optimizations
scraper.enable_optimized_mode()
scraper.enable_incremental_scraping()
```

## 📈 Monitoring

### Service Health

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f scraper
docker-compose logs -f postgres

# Monitor resource usage
docker stats
```

### Database Monitoring

```sql
-- Active connections
SELECT * FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('lacentrale_db'));

-- Index usage
SELECT * FROM pg_stat_user_indexes;
```

### Web Interfaces

- **PgAdmin**: http://localhost:8080 (Database management)
- **Jupyter**: http://localhost:8888 (Data analysis)
- **Selenium VNC**: http://localhost:7900 (Browser debugging)

## 🛡️ Security

### Best Practices

- **Change default passwords** in `.env`
- **Use environment variables** for secrets
- **Enable SSL** for production databases
- **Limit network access** with firewalls
- **Regular backups** of scraped data

### Rate Limiting

The scraper includes built-in rate limiting:
- Random delays: 1.5-3.5 seconds (normal mode)
- Fast delays: 0.1-0.3 seconds (optimized mode)
- Gradual scrolling with human-like patterns
- Browser fingerprint rotation

## 🚨 Troubleshooting

### Common Issues

#### Chrome Driver Issues
```bash
# Check Chrome version
docker-compose exec scraper google-chrome --version

# Reinstall ChromeDriver
docker-compose build --no-cache scraper
```

#### Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Memory Issues
```bash
# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory: 8GB+

# Reduce parallel workers
export NUM_WORKERS=2
```

#### Permission Errors (Linux/macOS)
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod -R 755 .
```

### Debug Mode

```bash
# Enable verbose logging
docker-compose --profile scraper run --rm -e VERBOSE_LOGGING=true scraper

# Access Selenium VNC for browser debugging
# http://localhost:7900 (password: secret)

# Check database directly
docker-compose exec postgres psql -U postgres -d lacentrale_db
```

## 📊 Performance Benchmarks

### Scraping Speed

| Mode | Pages/Hour | Cars/Hour | Memory Usage |
|------|------------|-----------|--------------|
| Normal | 50-100 | 1,000-2,000 | 200MB |
| Optimized | 500-1,000 | 10,000-20,000 | 300MB |
| Parallel (3 workers) | 1,000-1,500 | 20,000-30,000 | 500MB |

### Database Performance

| Schema | Insert Speed | Query Speed | Storage |
|--------|--------------|-------------|---------|
| Normalized | 5,000 cars/min | Medium | Efficient |
| Denormalized | 8,000 cars/min | Fast | Larger |

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- **Follow PEP 8** for Python code style
- **Add tests** for new features
- **Update documentation** for API changes
- **Use semantic versioning** for releases

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Notice

This scraper is for educational and research purposes only. Please:
- **Respect** LaCentrale's robots.txt and terms of service
- **Use reasonable delays** to avoid overloading servers
- **Consider legal implications** in your jurisdiction
- **Obtain permission** for commercial use

## 🙏 Acknowledgments

- **LaCentrale** for providing the car listing data
- **Selenium** and **undetected-chromedriver** communities
- **PostgreSQL** and **Docker** projects
- **Python** web scraping ecosystem

## 📞 Support

- **Issues**: [GitLab Issues](https://gitlab.com/your-username/lacentrale-scraper/-/issues)
- **Documentation**: [Wiki](https://gitlab.com/your-username/lacentrale-scraper/-/wikis/home)
- **Email**: your-email@domain.com

---

⭐ **Star this repository** if you find it useful!

Built with ❤️ using Python, Docker, and PostgreSQL.
