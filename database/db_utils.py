# -*- coding: utf-8 -*-
"""
Database utility functions for LaCentrale car listings
Supports both normalized and denormalized database approaches

@author: dduong
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from sqlalchemy import create_engine, and_, or_, desc, asc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import contextmanager

from .schema import (
    Base, Manufacturers, CarModels, Dealers, Vehicles, CarListings, CarListingsFlat
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for LaCentrale car listings"""
    
    def __init__(self, connection_string: str, approach: str = "normalized"):
        """
        Initialize database manager
        
        Args:
            connection_string: PostgreSQL connection string
            approach: "normalized" or "denormalized"
        """
        self.connection_string = connection_string
        self.approach = approach
        
        # Create engine with UTF-8 encoding support
        self.engine = create_engine(
            connection_string, 
            echo=False,
            connect_args={
                "client_encoding": "utf8"
            }
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Validate approach
        if approach not in ["normalized", "denormalized"]:
            raise ValueError("Approach must be 'normalized' or 'denormalized'")
        
        logger.info(f"Database manager initialized with {approach} approach")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            # Handle encoding errors more gracefully
            error_msg = str(e)
            if isinstance(e, UnicodeDecodeError):
                error_msg = f"Encoding error: {e.reason} at position {e.start}-{e.end}"
            logger.error(f"Database session error: {error_msg}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create database tables based on chosen approach"""
        from .schema import create_tables
        create_tables(self.engine, self.approach)
    
    def drop_tables(self):
        """Drop database tables based on chosen approach"""
        from .schema import drop_tables
        drop_tables(self.engine, self.approach)


# ==============================================================================
# INSERT FUNCTIONS
# ==============================================================================

def insert_car_listing_normalized(db_manager: DatabaseManager, car_data: Dict) -> Optional[int]:
    """
    Insert a car listing using the normalized approach
    
    Args:
        db_manager: DatabaseManager instance
        car_data: Car data dictionary from JSON
        
    Returns:
        ID of inserted car listing or None if failed
    """
    try:
        with db_manager.get_session() as session:
            # Extract data from the nested structure
            item = car_data.get('item', {})
            vehicle_data = item.get('vehicle', {})
            contact_data = item.get('contacts', {})
            location_data = item.get('location', {})
            delivery_data = item.get('delivery', {})
            financing_data = item.get('financing', {})
            
            # 1. Get or create manufacturer
            manufacturer = session.query(Manufacturers).filter_by(
                name=vehicle_data.get('make')
            ).first()
            
            if not manufacturer:
                manufacturer = Manufacturers(name=vehicle_data.get('make'))
                session.add(manufacturer)
                session.flush()  # Get the ID
            
            # 2. Get or create car model
            car_model = session.query(CarModels).filter_by(
                manufacturer_id=manufacturer.id,
                name=vehicle_data.get('model')
            ).first()
            
            if not car_model:
                car_model = CarModels(
                    manufacturer_id=manufacturer.id,
                    name=vehicle_data.get('model'),
                    commercial_name=vehicle_data.get('commercialName'),
                    category=vehicle_data.get('category'),
                    family=vehicle_data.get('family')
                )
                session.add(car_model)
                session.flush()
            
            # 3. Get or create dealer
            dealer = session.query(Dealers).filter_by(
                customer_reference=item.get('customerReference')
            ).first()
            
            if not dealer:
                dealer = Dealers(
                    customer_reference=item.get('customerReference'),
                    owner_correlation_id=item.get('ownerCorrelationId'),
                    name=contact_data.get('nomPublie'),
                    customer_type=item.get('customerType'),
                    customer_family_code=item.get('customerFamilyCode'),
                    country=location_data.get('country'),
                    visit_place=location_data.get('visitPlace'),
                    display_phone=contact_data.get('displayPhone1')
                )
                session.add(dealer)
                session.flush()
            
            # 4. Get or create vehicle
            # Handle VIN lookup properly (VIN might be None/missing)
            vin = vehicle_data.get('vin')
            if vin:
                # If VIN exists, use it for unique identification
                vehicle = session.query(Vehicles).filter_by(vin=vin).first()
            else:
                # If no VIN, try to find by other identifying characteristics
                vehicle = session.query(Vehicles).filter_by(
                    manufacturer_id=manufacturer.id,
                    car_model_id=car_model.id,
                    year=vehicle_data.get('year'),
                    detailed_model=vehicle_data.get('detailedModel'),
                    version=vehicle_data.get('version'),
                    vin=None  # Explicitly look for vehicles without VIN
                ).first()
            
            if not vehicle:
                vehicle = Vehicles(
                    vin=vin,  # This can be None
                    manufacturer_id=manufacturer.id,
                    car_model_id=car_model.id,
                    year=vehicle_data.get('year'),
                    detailed_model=vehicle_data.get('detailedModel'),
                    version=vehicle_data.get('version'),
                    trim_level=vehicle_data.get('trimLevel'),
                    doors=vehicle_data.get('doors'),
                    gearbox=vehicle_data.get('gearbox'),
                    motorization=vehicle_data.get('motorization'),
                    energy=vehicle_data.get('energy'),
                    external_color=vehicle_data.get('externalColor')
                )
                session.add(vehicle)
                session.flush()
            
            # 5. Check if listing already exists
            existing_listing = session.query(CarListings).filter_by(
                reference=item.get('reference')
            ).first()
            
            if existing_listing:
                logger.warning(f"Listing {item.get('reference')} already exists")
                return existing_listing.id
            
            # 6. Create car listing
            car_listing = CarListings(
                reference=item.get('reference'),
                vehicle_id=vehicle.id,
                dealer_id=dealer.id,
                price=item.get('price'),
                financing_teasing_price=financing_data.get('teasingPriceClassic'),
                mileage=vehicle_data.get('mileage'),
                is_new=item.get('isNew', False),
                score=item.get('score'),
                good_deal_badge=item.get('goodDealBadge'),
                pictures_count=item.get('picturesCount', 0),
                pictures_photosphere=item.get('picturesPhotosphere', False),
                pictures_360_exterieur=item.get('pictures360Exterieur', False),
                photo_url=item.get('photoUrl'),
                photo_url_mobile=item.get('photoUrlMobile'),
                publication_options=item.get('publicationOptions'),
                manufacturer_warranty_duration=item.get('manufacturerWarrantyDuration'),
                autoviza=item.get('autoviza', False),
                delivery_is_active=delivery_data.get('isActive', False),
                delivery_distance_max=delivery_data.get('distanceMax'),
                delivery_prices=delivery_data.get('prices'),
                distance_km=car_data.get('_distanceKm'),
                deliverable=car_data.get('_deliverable', False),
                delivery_price=car_data.get('_deliveryPrice'),
                first_online_date=item.get('firstOnlineDate'),
                last_update=item.get('lastUpdate'),
                pictures_count_date=item.get('picturesCountDate'),
                url=car_data.get('url')
            )
            
            session.add(car_listing)
            session.flush()
            
            logger.info(f"✅ Inserted car listing {item.get('reference')} (normalized)")
            return car_listing.id
            
    except IntegrityError as e:
        logger.error(f"Integrity error inserting car listing: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inserting car listing: {e}")
        return None


def insert_car_listing_denormalized(db_manager: DatabaseManager, car_data: Dict) -> Optional[int]:
    """
    Insert a car listing using the denormalized approach
    
    Args:
        db_manager: DatabaseManager instance
        car_data: Car data dictionary from JSON
        
    Returns:
        ID of inserted car listing or None if failed
    """
    try:
        with db_manager.get_session() as session:
            # Extract data from the nested structure
            item = car_data.get('item', {})
            vehicle_data = item.get('vehicle', {})
            contact_data = item.get('contacts', {})
            location_data = item.get('location', {})
            delivery_data = item.get('delivery', {})
            financing_data = item.get('financing', {})
            
            # Check if listing already exists
            existing_listing = session.query(CarListingsFlat).filter_by(
                reference=item.get('reference')
            ).first()
            
            if existing_listing:
                logger.warning(f"Listing {item.get('reference')} already exists")
                return existing_listing.id
            
            # Create flattened car listing
            car_listing_flat = CarListingsFlat(
                reference=item.get('reference'),
                url=car_data.get('url'),
                vin=vehicle_data.get('vin'),
                make=vehicle_data.get('make'),
                model=vehicle_data.get('model'),
                commercial_name=vehicle_data.get('commercialName'),
                year=vehicle_data.get('year'),
                detailed_model=vehicle_data.get('detailedModel'),
                version=vehicle_data.get('version'),
                trim_level=vehicle_data.get('trimLevel'),
                doors=vehicle_data.get('doors'),
                gearbox=vehicle_data.get('gearbox'),
                motorization=vehicle_data.get('motorization'),
                energy=vehicle_data.get('energy'),
                external_color=vehicle_data.get('externalColor'),
                category=vehicle_data.get('category'),
                family=vehicle_data.get('family'),
                mileage=vehicle_data.get('mileage'),
                customer_reference=item.get('customerReference'),
                owner_correlation_id=item.get('ownerCorrelationId'),
                dealer_name=contact_data.get('nomPublie'),
                customer_type=item.get('customerType'),
                customer_family_code=item.get('customerFamilyCode'),
                dealer_country=location_data.get('country'),
                dealer_visit_place=location_data.get('visitPlace'),
                dealer_phone=contact_data.get('displayPhone1'),
                price=item.get('price'),
                financing_teasing_price=financing_data.get('teasingPriceClassic'),
                score=item.get('score'),
                good_deal_badge=item.get('goodDealBadge'),
                is_new=item.get('isNew', False),
                pictures_count=item.get('picturesCount', 0),
                pictures_photosphere=item.get('picturesPhotosphere', False),
                pictures_360_exterieur=item.get('pictures360Exterieur', False),
                photo_url=item.get('photoUrl'),
                photo_url_mobile=item.get('photoUrlMobile'),
                publication_options=item.get('publicationOptions'),
                manufacturer_warranty_duration=item.get('manufacturerWarrantyDuration'),
                autoviza=item.get('autoviza', False),
                delivery_is_active=delivery_data.get('isActive', False),
                delivery_distance_max=delivery_data.get('distanceMax'),
                delivery_prices=delivery_data.get('prices'),
                distance_km=car_data.get('_distanceKm'),
                deliverable=car_data.get('_deliverable', False),
                delivery_price=car_data.get('_deliveryPrice'),
                first_online_date=item.get('firstOnlineDate'),
                last_update=item.get('lastUpdate'),
                pictures_count_date=item.get('picturesCountDate')
            )
            
            session.add(car_listing_flat)
            session.flush()
            
            logger.info(f"✅ Inserted car listing {item.get('reference')} (denormalized)")
            return car_listing_flat.id
            
    except IntegrityError as e:
        logger.error(f"Integrity error inserting car listing: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inserting car listing: {e}")
        return None


def insert_car_listing(db_manager: DatabaseManager, car_data: Dict) -> Optional[int]:
    """
    Insert a car listing using the appropriate approach
    
    Args:
        db_manager: DatabaseManager instance
        car_data: Car data dictionary from JSON
        
    Returns:
        ID of inserted car listing or None if failed
    """
    if db_manager.approach == "normalized":
        return insert_car_listing_normalized(db_manager, car_data)
    elif db_manager.approach == "denormalized":
        return insert_car_listing_denormalized(db_manager, car_data)
    else:
        raise ValueError("Invalid database approach")


def bulk_insert_car_listings(db_manager: DatabaseManager, car_data_list: List[Dict]) -> int:
    """
    Insert multiple car listings in bulk
    
    Args:
        db_manager: DatabaseManager instance
        car_data_list: List of car data dictionaries
        
    Returns:
        Number of successfully inserted listings
    """
    success_count = 0
    
    for car_data in car_data_list:
        result = insert_car_listing(db_manager, car_data)
        if result is not None:
            success_count += 1
    
    logger.info(f"✅ Bulk insert completed: {success_count}/{len(car_data_list)} listings inserted")
    return success_count


# ==============================================================================
# FETCH FUNCTIONS
# ==============================================================================

def fetch_car_listings_normalized(
    db_manager: DatabaseManager,
    filters: Optional[Dict] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "price"
) -> List[Dict]:
    """
    Fetch car listings using normalized approach with JOINs
    
    Args:
        db_manager: DatabaseManager instance
        filters: Dictionary of filter criteria
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by
        
    Returns:
        List of car listing dictionaries
    """
    try:
        with db_manager.get_session() as session:
            # Base query with explicit JOINs to avoid ambiguity
            query = session.query(CarListings).join(
                Vehicles, CarListings.vehicle_id == Vehicles.id
            ).join(
                Dealers, CarListings.dealer_id == Dealers.id
            ).join(
                Manufacturers, Vehicles.manufacturer_id == Manufacturers.id
            ).join(
                CarModels, Vehicles.car_model_id == CarModels.id
            )
            
            # Apply filters
            if filters:
                if 'make' in filters:
                    query = query.filter(Manufacturers.name.ilike(f"%{filters['make']}%"))
                if 'model' in filters:
                    query = query.filter(CarModels.name.ilike(f"%{filters['model']}%"))
                if 'min_price' in filters:
                    query = query.filter(CarListings.price >= filters['min_price'])
                if 'max_price' in filters:
                    query = query.filter(CarListings.price <= filters['max_price'])
                if 'min_year' in filters:
                    query = query.filter(Vehicles.year >= filters['min_year'])
                if 'max_year' in filters:
                    query = query.filter(Vehicles.year <= filters['max_year'])
                if 'energy' in filters:
                    query = query.filter(Vehicles.energy == filters['energy'])
                if 'gearbox' in filters:
                    query = query.filter(Vehicles.gearbox == filters['gearbox'])
                if 'max_mileage' in filters:
                    query = query.filter(CarListings.mileage <= filters['max_mileage'])
                if 'location' in filters:
                    query = query.filter(Dealers.visit_place == filters['location'])
            
            # Apply ordering
            if order_by == "price":
                query = query.order_by(asc(CarListings.price))
            elif order_by == "price_desc":
                query = query.order_by(desc(CarListings.price))
            elif order_by == "mileage":
                query = query.order_by(asc(CarListings.mileage))
            elif order_by == "year":
                query = query.order_by(desc(Vehicles.year))
            elif order_by == "date":
                query = query.order_by(desc(CarListings.first_online_date))
            
            # Apply pagination
            listings = query.offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            result = []
            for listing in listings:
                result.append({
                    'id': listing.id,
                    'reference': listing.reference,
                    'url': listing.url,
                    'price': listing.price,
                    'mileage': listing.mileage,
                    'make': listing.vehicle.manufacturer.name,
                    'model': listing.vehicle.car_model.name,
                    'year': listing.vehicle.year,
                    'energy': listing.vehicle.energy,
                    'gearbox': listing.vehicle.gearbox,
                    'external_color': listing.vehicle.external_color,
                    'dealer_name': listing.dealer.name,
                    'location': listing.dealer.visit_place,
                    'score': listing.score,
                    'good_deal_badge': listing.good_deal_badge,
                    'first_online_date': listing.first_online_date,
                    'photo_url': listing.photo_url
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching car listings (normalized): {e}")
        return []


def fetch_car_listings_denormalized(
    db_manager: DatabaseManager,
    filters: Optional[Dict] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "price"
) -> List[Dict]:
    """
    Fetch car listings using denormalized approach (single table)
    
    Args:
        db_manager: DatabaseManager instance
        filters: Dictionary of filter criteria
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by
        
    Returns:
        List of car listing dictionaries
    """
    try:
        with db_manager.get_session() as session:
            # Base query on flat table
            query = session.query(CarListingsFlat)
            
            # Apply filters
            if filters:
                if 'make' in filters:
                    query = query.filter(CarListingsFlat.make.ilike(f"%{filters['make']}%"))
                if 'model' in filters:
                    query = query.filter(CarListingsFlat.model.ilike(f"%{filters['model']}%"))
                if 'min_price' in filters:
                    query = query.filter(CarListingsFlat.price >= filters['min_price'])
                if 'max_price' in filters:
                    query = query.filter(CarListingsFlat.price <= filters['max_price'])
                if 'min_year' in filters:
                    query = query.filter(CarListingsFlat.year >= filters['min_year'])
                if 'max_year' in filters:
                    query = query.filter(CarListingsFlat.year <= filters['max_year'])
                if 'energy' in filters:
                    query = query.filter(CarListingsFlat.energy == filters['energy'])
                if 'gearbox' in filters:
                    query = query.filter(CarListingsFlat.gearbox == filters['gearbox'])
                if 'max_mileage' in filters:
                    query = query.filter(CarListingsFlat.mileage <= filters['max_mileage'])
                if 'location' in filters:
                    query = query.filter(CarListingsFlat.dealer_visit_place == filters['location'])
            
            # Apply ordering
            if order_by == "price":
                query = query.order_by(asc(CarListingsFlat.price))
            elif order_by == "price_desc":
                query = query.order_by(desc(CarListingsFlat.price))
            elif order_by == "mileage":
                query = query.order_by(asc(CarListingsFlat.mileage))
            elif order_by == "year":
                query = query.order_by(desc(CarListingsFlat.year))
            elif order_by == "date":
                query = query.order_by(desc(CarListingsFlat.first_online_date))
            
            # Apply pagination
            listings = query.offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            result = []
            for listing in listings:
                result.append({
                    'id': listing.id,
                    'reference': listing.reference,
                    'url': listing.url,
                    'price': listing.price,
                    'mileage': listing.mileage,
                    'make': listing.make,
                    'model': listing.model,
                    'year': listing.year,
                    'energy': listing.energy,
                    'gearbox': listing.gearbox,
                    'external_color': listing.external_color,
                    'dealer_name': listing.dealer_name,
                    'location': listing.dealer_visit_place,
                    'score': listing.score,
                    'good_deal_badge': listing.good_deal_badge,
                    'first_online_date': listing.first_online_date,
                    'photo_url': listing.photo_url
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching car listings (denormalized): {e}")
        return []


def fetch_car_listings(
    db_manager: DatabaseManager,
    filters: Optional[Dict] = None,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "price"
) -> List[Dict]:
    """
    Fetch car listings using the appropriate approach
    
    Args:
        db_manager: DatabaseManager instance
        filters: Dictionary of filter criteria
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by
        
    Returns:
        List of car listing dictionaries
    """
    if db_manager.approach == "normalized":
        return fetch_car_listings_normalized(db_manager, filters, limit, offset, order_by)
    elif db_manager.approach == "denormalized":
        return fetch_car_listings_denormalized(db_manager, filters, limit, offset, order_by)
    else:
        raise ValueError("Invalid database approach")


def fetch_car_listing_by_reference(db_manager: DatabaseManager, reference: str) -> Optional[Dict]:
    """
    Fetch a specific car listing by its reference
    
    Args:
        db_manager: DatabaseManager instance
        reference: Car listing reference (e.g., E116704555)
        
    Returns:
        Car listing dictionary or None if not found
    """
    try:
        with db_manager.get_session() as session:
            if db_manager.approach == "normalized":
                listing = session.query(CarListings).filter_by(reference=reference).first()
                if listing:
                    return {
                        'id': listing.id,
                        'reference': listing.reference,
                        'url': listing.url,
                        'price': listing.price,
                        'mileage': listing.mileage,
                        'make': listing.vehicle.manufacturer.name,
                        'model': listing.vehicle.car_model.name,
                        'year': listing.vehicle.year,
                        'vin': listing.vehicle.vin,
                        'energy': listing.vehicle.energy,
                        'gearbox': listing.vehicle.gearbox,
                        'external_color': listing.vehicle.external_color,
                        'dealer_name': listing.dealer.name,
                        'location': listing.dealer.visit_place,
                        'score': listing.score,
                        'good_deal_badge': listing.good_deal_badge,
                        'first_online_date': listing.first_online_date,
                        'photo_url': listing.photo_url,
                        'pictures_count': listing.pictures_count
                    }
            
            elif db_manager.approach == "denormalized":
                listing = session.query(CarListingsFlat).filter_by(reference=reference).first()
                if listing:
                    return {
                        'id': listing.id,
                        'reference': listing.reference,
                        'url': listing.url,
                        'price': listing.price,
                        'mileage': listing.mileage,
                        'make': listing.make,
                        'model': listing.model,
                        'year': listing.year,
                        'vin': listing.vin,
                        'energy': listing.energy,
                        'gearbox': listing.gearbox,
                        'external_color': listing.external_color,
                        'dealer_name': listing.dealer_name,
                        'location': listing.dealer_visit_place,
                        'score': listing.score,
                        'good_deal_badge': listing.good_deal_badge,
                        'first_online_date': listing.first_online_date,
                        'photo_url': listing.photo_url,
                        'pictures_count': listing.pictures_count
                    }
            
            return None
            
    except Exception as e:
        logger.error(f"Error fetching car listing by reference: {e}")
        return None


def get_statistics(db_manager: DatabaseManager) -> Dict:
    """
    Get database statistics
    
    Args:
        db_manager: DatabaseManager instance
        
    Returns:
        Dictionary with statistics
    """
    try:
        with db_manager.get_session() as session:
            stats = {}
            
            if db_manager.approach == "normalized":
                stats['total_listings'] = session.query(CarListings).count()
                stats['total_manufacturers'] = session.query(Manufacturers).count()
                stats['total_models'] = session.query(CarModels).count()
                stats['total_dealers'] = session.query(Dealers).count()
                stats['total_vehicles'] = session.query(Vehicles).count()
                
                # Price statistics
                price_stats = session.query(
                    func.min(CarListings.price),
                    func.max(CarListings.price),
                    func.avg(CarListings.price)
                ).first()
                stats['min_price'] = price_stats[0]
                stats['max_price'] = price_stats[1]
                stats['avg_price'] = round(price_stats[2], 2) if price_stats[2] else 0
                
                # Popular makes - Fixed JOIN with explicit table relationships
                popular_makes = session.query(
                    Manufacturers.name, func.count(CarListings.id)
                ).select_from(CarListings).join(
                    Vehicles, CarListings.vehicle_id == Vehicles.id
                ).join(
                    Manufacturers, Vehicles.manufacturer_id == Manufacturers.id
                ).group_by(Manufacturers.name).order_by(
                    desc(func.count(CarListings.id))
                ).limit(5).all()
                stats['popular_makes'] = [{'make': make, 'count': count} for make, count in popular_makes]
                
            elif db_manager.approach == "denormalized":
                stats['total_listings'] = session.query(CarListingsFlat).count()
                
                # Price statistics
                price_stats = session.query(
                    func.min(CarListingsFlat.price),
                    func.max(CarListingsFlat.price),
                    func.avg(CarListingsFlat.price)
                ).first()
                stats['min_price'] = price_stats[0]
                stats['max_price'] = price_stats[1]
                stats['avg_price'] = round(price_stats[2], 2) if price_stats[2] else 0
                
                # Popular makes
                popular_makes = session.query(
                    CarListingsFlat.make, func.count(CarListingsFlat.id)
                ).group_by(CarListingsFlat.make).order_by(
                    desc(func.count(CarListingsFlat.id))
                ).limit(5).all()
                stats['popular_makes'] = [{'make': make, 'count': count} for make, count in popular_makes]
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}


# ==============================================================================
# UPDATE FUNCTIONS
# ==============================================================================

def update_car_listing_price(db_manager: DatabaseManager, reference: str, new_price: int) -> bool:
    """
    Update the price of a car listing
    
    Args:
        db_manager: DatabaseManager instance
        reference: Car listing reference
        new_price: New price in euros
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.get_session() as session:
            if db_manager.approach == "normalized":
                listing = session.query(CarListings).filter_by(reference=reference).first()
            else:
                listing = session.query(CarListingsFlat).filter_by(reference=reference).first()
            
            if listing:
                listing.price = new_price
                listing.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"✅ Updated price for listing {reference} to {new_price}")
                return True
            else:
                logger.warning(f"Listing {reference} not found")
                return False
                
    except Exception as e:
        logger.error(f"Error updating car listing price: {e}")
        return False


def delete_car_listing(db_manager: DatabaseManager, reference: str) -> bool:
    """
    Delete a car listing by reference
    
    Args:
        db_manager: DatabaseManager instance
        reference: Car listing reference
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.get_session() as session:
            if db_manager.approach == "normalized":
                listing = session.query(CarListings).filter_by(reference=reference).first()
            else:
                listing = session.query(CarListingsFlat).filter_by(reference=reference).first()
            
            if listing:
                session.delete(listing)
                session.commit()
                logger.info(f"🗑️ Deleted listing {reference}")
                return True
            else:
                logger.warning(f"Listing {reference} not found")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting car listing: {e}")
        return False


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def load_json_data(file_path: str) -> List[Dict]:
    """
    Load car data from JSON file (supports both new array format and legacy format)
    
    Args:
        file_path: Path to JSON file containing car data
        
    Returns:
        List of car data dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Try to load as proper JSON array first (new format)
        try:
            data = json.loads(content)
            if isinstance(data, list):
                logger.info(f"✅ Loaded {len(data)} car listings from {file_path} (array format)")
                return data
            else:
                logger.info(f"✅ Loaded 1 car listing from {file_path} (single object)")
                return [data]
        except json.JSONDecodeError:
            # Fall back to legacy format handling
            logger.info("Attempting to parse legacy JSON format...")
            pass
        
        # Handle legacy format where JSON objects are concatenated
        car_data_list = []
        json_objects = content.split('}{')
        
        for i, json_str in enumerate(json_objects):
            # Fix the JSON format
            if i == 0 and len(json_objects) > 1:
                json_str += '}'
            elif i == len(json_objects) - 1 and len(json_objects) > 1:
                json_str = '{' + json_str
            elif len(json_objects) > 1:
                json_str = '{' + json_str + '}'
            
            try:
                car_data = json.loads(json_str)
                car_data_list.append(car_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON object {i}: {e}")
                continue
        
        logger.info(f"✅ Loaded {len(car_data_list)} car listings from {file_path} (legacy format)")
        return car_data_list
        
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    print("Database utilities loaded successfully!")
    print("\nAvailable functions:")
    print("- insert_car_listing(db_manager, car_data)")
    print("- bulk_insert_car_listings(db_manager, car_data_list)")
    print("- fetch_car_listings(db_manager, filters, limit, offset, order_by)")
    print("- fetch_car_listing_by_reference(db_manager, reference)")
    print("- update_car_listing_price(db_manager, reference, new_price)")
    print("- delete_car_listing(db_manager, reference)")
    print("- get_statistics(db_manager)")
    print("- load_json_data(file_path)")
