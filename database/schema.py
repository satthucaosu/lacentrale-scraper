# -*- coding: utf-8 -*-
"""
PostgreSQL Database Schemas for LaCentrale Car Listings

Two approaches:
1. Normalized schema (recommended for data integrity)
2. Denormalized schema (optimized for read performance)

@author: dduong
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ==============================================================================
# APPROACH 1: NORMALIZED SCHEMA (Recommended for data integrity)
# ==============================================================================
# Separates data into logical tables with relationships
# Pros: Data consistency, no redundancy, easier maintenance
# Cons: More complex queries with JOINs

class Manufacturers(Base):
    """Table for car manufacturers (e.g. PEUGEOT, CITROEN, RENAULT, etc.)"""
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    models = relationship("CarModels", back_populates="manufacturer")
    vehicles = relationship("Vehicles", back_populates="manufacturer")

class CarModels(Base):
    """Table for car models (GOLF, CLASSE A, etc.)"""
    __tablename__ = 'car_models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    name = Column(String(100), nullable=False)  # GOLF, CLASSE A
    commercial_name = Column(String(100))  # GOLF 7, CLASSE A 4 BERLINE
    category = Column(String(50))  # COMPACTE, SUV_4X4_CROSSOVER
    family = Column(String(50))  # AUTO
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    manufacturer = relationship("Manufacturers", back_populates="models")
    vehicles = relationship("Vehicles", back_populates="car_model")

class Dealers(Base):
    """Table for car dealers/sellers"""
    __tablename__ = 'dealers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_reference = Column(String(50), unique=True, nullable=False)  # C023014
    owner_correlation_id = Column(String(50))  # C023014
    name = Column(String(200))  # AUTO OCCASION PASTEUR
    customer_type = Column(String(20))  # PRO, PARTICULIER
    customer_family_code = Column(String(100))  # CENTRE_MULTIMARQUES, CONCESSIONNAIRE
    country = Column(String(5), default='FR')  # FR
    visit_place = Column(String(10))  # 95, 77
    display_phone = Column(String(200))  # Encoded phone number
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    listings = relationship("CarListings", back_populates="dealer")

class Vehicles(Base):
    """Table for vehicle specifications"""
    __tablename__ = 'vehicles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), unique=True, nullable=True)  # Vehicle Identification Number (not always available)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    car_model_id = Column(Integer, ForeignKey('car_models.id'), nullable=False)
    year = Column(Integer, nullable=False)
    detailed_model = Column(String(200))  # VOLKSWAGEN GOLF VII
    version = Column(String(300))  # VII 1.4 TSI ACT 140 BLUEMOTION TECHNOLOGY CARAT DSG7 5P
    trim_level = Column(String(100))  # CARAT, AMG LINE
    doors = Column(Integer)  # 4, 5
    gearbox = Column(String(20))  # AUTO, MANUAL
    motorization = Column(String(100))  # 1.4 TSI 140
    energy = Column(String(50))  # ESSENCE, HYBRID_ESSENCE_ELECTRIC
    external_color = Column(String(100))  # GRIS F, NOIR
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    manufacturer = relationship("Manufacturers", back_populates="vehicles")
    car_model = relationship("CarModels", back_populates="vehicles")
    listings = relationship("CarListings", back_populates="vehicle")

class CarListings(Base):
    """Main table for car listings"""
    __tablename__ = 'car_listings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reference = Column(String(50), unique=True, nullable=False)  # E116704555
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    dealer_id = Column(Integer, ForeignKey('dealers.id'), nullable=False)
    
    # Pricing information
    price = Column(Integer, nullable=False)  # Main price in euros
    financing_teasing_price = Column(Integer)  # Monthly financing price
    
    # Vehicle condition
    mileage = Column(Integer, nullable=False)  # Kilometers
    is_new = Column(Boolean, default=False)
    
    # Scoring and badges
    score = Column(Float)  # 562.79553
    good_deal_badge = Column(String(50))  # EQUITABLE_DEAL, VERY_GOOD_DEAL, GOOD_DEAL
    
    # Media information
    pictures_count = Column(Integer, default=0)
    pictures_photosphere = Column(Boolean, default=False)
    pictures_360_exterieur = Column(Boolean, default=False)
    photo_url = Column(Text)  # Main photo URL
    photo_url_mobile = Column(JSON)  # Array of mobile photo URLs
    
    # Publication and warranty
    publication_options = Column(JSON)  # Array of publication options
    manufacturer_warranty_duration = Column(Integer)  # Months
    autoviza = Column(Boolean, default=False)
    
    # Delivery information
    delivery_is_active = Column(Boolean, default=False)
    delivery_distance_max = Column(Integer)  # Max delivery distance in km
    delivery_prices = Column(JSON)  # Array of delivery prices
    distance_km = Column(Integer)  # Distance from search location
    deliverable = Column(Boolean, default=False)
    delivery_price = Column(Integer)  # Actual delivery price for this distance
    
    # Timestamps
    first_online_date = Column(String(20))  # "2025-08-02"
    last_update = Column(Integer)  # Unix timestamp
    pictures_count_date = Column(Integer)  # Unix timestamp
    
    # URL
    url = Column(Text, nullable=False)  # Full URL to the listing
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicles", back_populates="listings")
    dealer = relationship("Dealers", back_populates="listings")


# ==============================================================================
# APPROACH 2: DENORMALIZED SCHEMA (Optimized for read performance)
# ==============================================================================
# Stores most data in fewer tables for faster queries
# Pros: Faster queries, simpler JOINs
# Cons: Data redundancy, potential inconsistency

class CarListingsFlat(Base):
    """Denormalized table containing all car listing information"""
    __tablename__ = 'car_listings_flat'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Listing identification
    reference = Column(String(50), unique=True, nullable=False)  # E116704555
    url = Column(Text, nullable=False)
    
    # Vehicle information (denormalized)
    vin = Column(String(17), nullable=True)  # VIN not always available from LaCentrale
    make = Column(String(100), nullable=False)  # VOLKSWAGEN, MERCEDES
    model = Column(String(100), nullable=False)  # GOLF, CLASSE A
    commercial_name = Column(String(100))  # GOLF 7, CLASSE A 4 BERLINE
    year = Column(Integer, nullable=False)
    detailed_model = Column(String(200))  # VOLKSWAGEN GOLF VII
    version = Column(String(300))  # Full version string
    trim_level = Column(String(100))  # CARAT, AMG LINE
    doors = Column(Integer)
    gearbox = Column(String(20))  # AUTO, MANUAL
    motorization = Column(String(100))  # 1.4 TSI 140
    energy = Column(String(50))  # ESSENCE, HYBRID_ESSENCE_ELECTRIC
    external_color = Column(String(100))
    category = Column(String(50))  # COMPACTE, SUV_4X4_CROSSOVER
    family = Column(String(50))  # AUTO
    mileage = Column(Integer, nullable=False)
    
    # Dealer information (denormalized)
    customer_reference = Column(String(50), nullable=False)
    owner_correlation_id = Column(String(50))
    dealer_name = Column(String(200))  # AUTO OCCASION PASTEUR
    customer_type = Column(String(20))  # PRO, PARTICULIER
    customer_family_code = Column(String(100))  # CENTRE_MULTIMARQUES
    dealer_country = Column(String(5), default='FR')
    dealer_visit_place = Column(String(10))  # 95, 77
    dealer_phone = Column(String(200))  # Encoded phone
    
    # Pricing information
    price = Column(Integer, nullable=False)
    financing_teasing_price = Column(Integer)
    
    # Scoring and condition
    score = Column(Float)
    good_deal_badge = Column(String(50))
    is_new = Column(Boolean, default=False)
    
    # Media information
    pictures_count = Column(Integer, default=0)
    pictures_photosphere = Column(Boolean, default=False)
    pictures_360_exterieur = Column(Boolean, default=False)
    photo_url = Column(Text)
    photo_url_mobile = Column(JSON)  # Array of mobile photo URLs
    
    # Publication details
    publication_options = Column(JSON)  # Array of publication options
    manufacturer_warranty_duration = Column(Integer)
    autoviza = Column(Boolean, default=False)
    
    # Delivery information
    delivery_is_active = Column(Boolean, default=False)
    delivery_distance_max = Column(Integer)
    delivery_prices = Column(JSON)
    distance_km = Column(Integer)
    deliverable = Column(Boolean, default=False)
    delivery_price = Column(Integer)
    
    # Timestamps
    first_online_date = Column(String(20))
    last_update = Column(Integer)
    pictures_count_date = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==============================================================================
# INDEXES FOR PERFORMANCE
# ==============================================================================

# For normalized schema
from sqlalchemy import Index

# Indexes for common queries on normalized tables
Index('idx_vehicles_make_model_year', Vehicles.manufacturer_id, Vehicles.car_model_id, Vehicles.year)
Index('idx_listings_price_mileage', CarListings.price, CarListings.mileage)
Index('idx_listings_dealer_date', CarListings.dealer_id, CarListings.first_online_date)
Index('idx_listings_reference', CarListings.reference)

# Indexes for denormalized table
Index('idx_flat_make_model_year', CarListingsFlat.make, CarListingsFlat.model, CarListingsFlat.year)
Index('idx_flat_price_mileage', CarListingsFlat.price, CarListingsFlat.mileage)
Index('idx_flat_location_date', CarListingsFlat.dealer_visit_place, CarListingsFlat.first_online_date)
Index('idx_flat_reference', CarListingsFlat.reference)
Index('idx_flat_energy_gearbox', CarListingsFlat.energy, CarListingsFlat.gearbox)


def create_tables(engine, approach="normalized"):
    """
    Create database tables based on the chosen approach
    
    Args:
        engine: SQLAlchemy engine
        approach: "normalized" or "denormalized"
    """
    if approach == "normalized":
        # Create all normalized tables
        Base.metadata.create_all(engine)
        print("✅ Normalized database schema created successfully")
    elif approach == "denormalized":
        # Create only the flat table (and any shared tables if needed)
        CarListingsFlat.__table__.create(engine, checkfirst=True)
        print("✅ Denormalized database schema created successfully")
    else:
        raise ValueError("Approach must be 'normalized' or 'denormalized'")


def drop_tables(engine, approach="normalized"):
    """
    Drop database tables based on the chosen approach
    
    Args:
        engine: SQLAlchemy engine
        approach: "normalized" or "denormalized"  
    """
    if approach == "normalized":
        Base.metadata.drop_all(engine)
        print("🗑️ Normalized database schema dropped")
    elif approach == "denormalized":
        CarListingsFlat.__table__.drop(engine, checkfirst=True)
        print("🗑️ Denormalized database schema dropped")
    else:
        raise ValueError("Approach must be 'normalized' or 'denormalized'")


if __name__ == "__main__":
    # Example usage
    from sqlalchemy import create_engine
    
    # Example connection string - replace with your actual database credentials
    # engine = create_engine("postgresql://username:password@localhost:5432/lacentrale_db")
    
    print("Database schema definitions loaded successfully!")
    print("\nApproach 1 (Normalized):")
    print("- 5 tables: Manufacturers, CarModels, Dealers, Vehicles, CarListings")
    print("- Best for data integrity and avoiding redundancy")
    print("- Requires JOINs for complex queries")
    
    print("\nApproach 2 (Denormalized):")
    print("- 1 main table: CarListingsFlat")
    print("- Best for read performance and simpler queries")
    print("- Some data redundancy but faster searches")