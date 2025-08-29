# -*- coding: utf-8 -*-
"""
Export Database Tables to Excel
Export 100 rows from each table in the Lacentraledb database to an Excel file.
Each table will be in a separate sheet.

@author: dduong
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Check for required dependencies
try:
    import pandas as pd
except ImportError:
    print("❌ Error: pandas is required for Excel export")
    print("Please install it with: pip install pandas")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("❌ Error: openpyxl is required for Excel export")
    print("Please install it with: pip install openpyxl")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: python-dotenv not found. Environment variables will be read from system only.")
    DOTENV_AVAILABLE = False

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_utils import DatabaseManager
from database.schema import (
    Manufacturers, CarModels, Dealers, Vehicles, CarListings, CarListingsFlat
)
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseExporter:
    """Export database tables to Excel"""
    
    def __init__(self, connection_string: str, approach: str = "normalized"):
        """
        Initialize the database exporter
        
        Args:
            connection_string: PostgreSQL connection string
            approach: "normalized" or "denormalized"
        """
        self.db_manager = DatabaseManager(connection_string, approach)
        self.approach = approach
        
    def get_table_data(self, table_name: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Get data from a specific table
        
        Args:
            table_name: Name of the table
            limit: Number of rows to fetch
            
        Returns:
            pandas DataFrame with table data
        """
        try:
            with self.db_manager.get_session() as session:
                # Use raw SQL to fetch data to avoid complex ORM queries
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = session.execute(query)
                
                # Get column names
                columns = result.keys()
                
                # Fetch all rows
                rows = result.fetchall()
                
                if not rows:
                    logger.warning(f"No data found in table {table_name}")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(rows, columns=columns)
                
                # Convert datetime columns to string for Excel compatibility
                for col in df.columns:
                    if df[col].dtype == 'datetime64[ns]' or 'datetime' in str(df[col].dtype):
                        df[col] = df[col].astype(str)
                
                logger.info(f"✅ Fetched {len(df)} rows from {table_name}")
                return df
                
        except Exception as e:
            logger.error(f"Error fetching data from {table_name}: {e}")
            return None
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database
        
        Returns:
            List of table names
        """
        try:
            with self.db_manager.get_session() as session:
                # Query to get all table names in the public schema
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                result = session.execute(query)
                tables = [row[0] for row in result.fetchall()]
                
                logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
                return tables
                
        except Exception as e:
            logger.error(f"Error fetching table list: {e}")
            return []
    
    def export_to_excel(self, output_path: str, rows_per_table: int = 100) -> bool:
        """
        Export all tables to Excel file with separate sheets
        
        Args:
            output_path: Path to output Excel file
            rows_per_table: Number of rows to export per table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all tables in the database
            tables = self.get_all_tables()
            
            if not tables:
                logger.error("No tables found in database")
                return False
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                exported_tables = 0
                
                for table_name in tables:
                    logger.info(f"Exporting table: {table_name}")
                    
                    # Get data from table
                    df = self.get_table_data(table_name, rows_per_table)
                    
                    if df is not None and not df.empty:
                        # Clean sheet name (Excel sheet names have restrictions)
                        sheet_name = table_name[:31]  # Excel sheet name limit
                        sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
                        
                        # Write to Excel sheet
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        exported_tables += 1
                        
                        logger.info(f"✅ Exported {len(df)} rows from {table_name} to sheet '{sheet_name}'")
                    else:
                        logger.warning(f"Skipping empty table: {table_name}")
                
                # Add summary sheet
                summary_data = {
                    'Export Information': [
                        'Export Date',
                        'Database Approach',
                        'Total Tables Found',
                        'Tables Exported',
                        'Rows Per Table',
                        'Output File'
                    ],
                    'Value': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        self.approach,
                        len(tables),
                        exported_tables,
                        rows_per_table,
                        os.path.basename(output_path)
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Export_Summary', index=False)
                
            logger.info(f"🎉 Export completed successfully! File saved: {output_path}")
            logger.info(f"📊 Exported {exported_tables} tables with up to {rows_per_table} rows each")
            return True
            
        except Exception as e:
            logger.error(f"Error during export: {e}")
            return False


def get_database_connection_string() -> str:
    """
    Get database connection string from environment variables or use defaults
    
    Returns:
        PostgreSQL connection string
    """
    # Try to load from .env file if it exists
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_file) and DOTENV_AVAILABLE:
        load_dotenv(env_file)
    
    # Get database configuration
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'lacentrale_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', '')
    
    if not db_password:
        logger.warning("No database password found. Please check your .env file or environment variables.")
        db_password = input("Enter database password: ")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return connection_string


def main():
    """Main function to export database tables to Excel"""
    print("🚀 Starting database export to Excel...")
    
    try:
        # Get database configuration
        connection_string = get_database_connection_string()
        approach = os.getenv('DATABASE_APPROACH', 'normalized')
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"lacentraledb_export_{approach}_{timestamp}.xlsx"
        
        # Ensure output directory exists
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, output_filename)
        
        # Create exporter and export data
        exporter = DatabaseExporter(connection_string, approach)
        
        print(f"📝 Database approach: {approach}")
        print(f"📁 Output file: {output_path}")
        print("📊 Exporting 100 rows from each table...")
        
        success = exporter.export_to_excel(output_path, rows_per_table=100)
        
        if success:
            print(f"✅ Export completed successfully!")
            print(f"📄 File saved: {output_path}")
            
            # Try to get file size
            try:
                file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                print(f"📏 File size: {file_size:.2f} MB")
            except:
                pass
                
        else:
            print("❌ Export failed. Check the logs for details.")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
