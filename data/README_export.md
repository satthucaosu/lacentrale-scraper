# Database Export to Excel

This script exports 100 rows from each table in the Lacentraledb database to an Excel file, with each table in a separate sheet.

## Files

- `export_to_excel.py` - Main export script
- `README_export.md` - This documentation

## Prerequisites

### Required Python Packages

The following packages need to be installed:

```bash
pip install pandas openpyxl
```

### Database Connection

Make sure you have:
1. A running PostgreSQL database with the `lacentrale_db` database
2. Proper database credentials configured in your `.env` file or environment variables

Required environment variables:
- `DB_HOST` (default: localhost)
- `DB_PORT` (default: 5432)
- `DB_NAME` (default: lacentrale_db)
- `DB_USER` (default: postgres)
- `POSTGRES_PASSWORD` (required)
- `DATABASE_APPROACH` (default: normalized, options: normalized/denormalized)

## Usage

### 1. Install Required Packages

First, install the required Python packages:

```bash
pip install pandas openpyxl
```

### 2. Run the Export

Run the main export script:

```bash
python data/export_to_excel.py
```

This will:
- Connect to the database
- Discover all tables automatically
- Export 100 rows from each table
- Create an Excel file with separate sheets for each table
- Add a summary sheet with export information

### 3. Output

The script will create an Excel file in the `/data/` folder with the naming pattern:
```
lacentraledb_export_{approach}_{timestamp}.xlsx
```

Example: `lacentraledb_export_normalized_20241220_143052.xlsx`

## Excel File Structure

The exported Excel file will contain:

### For Normalized Approach:
- `manufacturers` - Car manufacturers (PEUGEOT, CITROEN, etc.)
- `car_models` - Car models with details
- `dealers` - Dealer information
- `vehicles` - Vehicle specifications
- `car_listings` - Main car listings with foreign keys
- `Export_Summary` - Export metadata and statistics

### For Denormalized Approach:
- `car_listings_flat` - All data in a single denormalized table
- `Export_Summary` - Export metadata and statistics

## Customization

### Change Number of Rows

To export a different number of rows per table, modify the `rows_per_table` parameter in the main function:

```python
success = exporter.export_to_excel(output_path, rows_per_table=200)  # Export 200 rows instead
```

### Filter Specific Tables

To export only specific tables, modify the `get_all_tables()` method or add filtering logic in the export loop.

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```
   ❌ Error: pandas is required for Excel export
   ```
   Solution: Install pandas and openpyxl
   ```bash
   pip install pandas openpyxl
   ```

2. **Database Connection Error**
   ```
   ❌ Database connection failed
   ```
   Solution: Check your database credentials and ensure PostgreSQL is running

3. **No Tables Found**
   ```
   ⚠️ Database connected but no tables found
   ```
   Solution: Ensure you have data in your database and the correct `DATABASE_APPROACH` setting

4. **Permission Error**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   Solution: Make sure the output directory is writable and any existing Excel file is closed

### Getting Help

If you encounter issues:

1. Check the console output for specific error messages
2. Verify your database connection and credentials
3. Ensure all required packages are installed (pandas, openpyxl)
4. Make sure your PostgreSQL database is running and accessible

## Example Output

```
🚀 Starting database export to Excel...
📝 Database approach: normalized
📁 Output file: C:\path\to\data\lacentraledb_export_normalized_20241220_143052.xlsx
📊 Exporting 100 rows from each table...
✅ Exported 100 rows from manufacturers to sheet 'manufacturers'
✅ Exported 100 rows from car_models to sheet 'car_models'
✅ Exported 100 rows from dealers to sheet 'dealers'
✅ Exported 100 rows from vehicles to sheet 'vehicles'
✅ Exported 100 rows from car_listings to sheet 'car_listings'
🎉 Export completed successfully! File saved: lacentraledb_export_normalized_20241220_143052.xlsx
📊 Exported 5 tables with up to 100 rows each
📄 File saved: C:\path\to\data\lacentraledb_export_normalized_20241220_143052.xlsx
📏 File size: 2.45 MB
```
