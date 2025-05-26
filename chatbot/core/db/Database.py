from sqlalchemy import create_engine, inspect, Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from core.processing.security import hash_password, verify_password
import random
import json
from models.User import User
from models.UserQuery import UserQuery
from models.Base import Base

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize database connection and session."""
        try:
            self.engine = create_engine('sqlite:///tellerai.db')
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self.Base = declarative_base()
            self._create_tables()
            self._create_admin_user()  # Create admin user after tables are created
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            self.Base.metadata.create_all(self.engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def refresh_user(self, user: User) -> Optional[User]:
        """Refresh a user object from the database."""
        try:
            session = self.get_session()
            refreshed_user = session.query(User).filter(User.id == user.id).first()
            if refreshed_user:
                session.refresh(refreshed_user)
                logger.info(f"Successfully refreshed user {user.id}")
                return refreshed_user
            return None
        except Exception as e:
            logger.error(f"Failed to refresh user: {e}")
            return None
        finally:
            session.close()

    def setUser(self, user: User) -> None:
        """Ensure user object is attached to session."""
        try:
            session = self.get_session()
            session.add(user)
            session.refresh(user)
            session.commit()
            logger.info(f"User {user.id} attached to session")
        except Exception as e:
            logger.error(f"Failed to set user in session: {e}")
            session.rollback()
        finally:
            session.close()

    def getUserFromPhoneNo(self, phone: str) -> Optional[User]:
        """Get user by phone number."""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.phone == phone).first()
            if user:
                session.refresh(user)
            return user
        except Exception as e:
            logger.error(f"Failed to get user by phone: {e}")
            return None
        finally:
            session.close()

    def getUserFromEmail(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.email == email).first()
            if user:
                session.refresh(user)
            return user
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
        finally:
            session.close()

    def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate user by email/phone and password."""
        try:
            session = self.get_session()
            user = session.query(User).filter(
                (User.email == identifier) | (User.phone == identifier)
            ).first()
            
            if user and user.verify_password(password):
                session.refresh(user)
                user.last_login = datetime.utcnow()
                user.login_count += 1
                session.commit()
                logger.info(f"User {user.id} authenticated successfully")
                return user
            return None
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def addUser(self, name: str, phone: str, email: str, password: str, 
                lat: Optional[float] = None, long: Optional[float] = None) -> User:
        """Add a new user."""
        try:
            session = self.get_session()
            # Generate a unique account number
            account_number = self._generate_account_number()
            
            user = User(
                name=name,
                phone=phone,
                email=email,
                password=password,
                account_number=account_number,  # Set the generated account number
                latitude=lat,
                longitude=long,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                login_count=1
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"New user created with ID: {user.id} and account number: {account_number}")
            return user
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_user_queries(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's queries with proper session management."""
        try:
            session = self.get_session()
            queries = session.query(UserQuery).filter(UserQuery.user_id == user_id).all()
            return [query.to_dict() for query in queries]
        except Exception as e:
            logger.error(f"Failed to get user queries: {e}")
            return []
        finally:
            session.close()

    def updateLocation(self, lat: float, long: float, location: str = None):
        """Update user's location."""
        if not self.current_user:
            return
        
        try:
            session = self.Session()
            user = session.query(User).filter_by(id=self.current_user.id).first()
            if user:
                user.latitude = lat
                user.longitude = long
                if location:
                    user.last_location = location
                session.commit()
                logger.info(f"Location updated for user: {user.account_number}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating location: {e}")
        finally:
            session.close()

    def addQuery(self, query: str, intent: str, response: str, metadata: Dict = None) -> int:
        """
        Add a new query to the database with enhanced analytics data.
        
        Args:
            query (str): User's query
            intent (str): Detected intent
            response (str): Assistant's response
            metadata (Dict): Additional analytics data
            
        Returns:
            int: The ID of the created query
        """
        try:
            session = self.get_session()
            
            # Extract user_id and location from metadata
            user_id = metadata.get('user_id') if metadata else None
            location = metadata.get('location') if metadata else None
            
            # Create query object
            user_query = UserQuery(
                user_id=user_id,
                query=query,
                intent=intent,
                response=response,
                location=location,
                query_metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            session.add(user_query)
            session.commit()
            session.refresh(user_query)
            
            logger.info(f"Query added successfully: {user_query.id}")
            return user_query.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding query: {e}")
            raise
        finally:
            session.close()

    def updateRating(self, query_id: int, rating: int):
        """Update the rating for a query."""
        try:
            session = self.get_session()
            query = session.query(UserQuery).filter(UserQuery.id == query_id).first()
            if query:
                query.rating = rating
                session.commit()
                logger.info(f"Updated rating for query {query_id} to {rating}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update rating: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def _generate_account_number(self) -> str:
        """Generate a unique account number."""
        while True:
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            session = self.Session()
            if not session.query(User).filter_by(account_number=account_number).first():
                session.close()
                return account_number
            session.close()

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a user.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            Dict[str, Any]: Dictionary containing user statistics
        """
        try:
            session = self.Session()
            queries = session.query(UserQuery).filter_by(user_id=user_id).all()
            
            total_queries = len(queries)
            avg_rating = sum(q.rating or 0 for q in queries) / total_queries if total_queries > 0 else 0
            
            intents = {}
            sentiments = {}
            for q in queries:
                if q.intent:
                    intents[q.intent] = intents.get(q.intent, 0) + 1
                if q.sentiment:
                    sentiments[q.sentiment] = sentiments.get(q.sentiment, 0) + 1
            
            return {
                'total_queries': total_queries,
                'average_rating': avg_rating,
                'intent_distribution': intents,
                'sentiment_distribution': sentiments,
                'last_query': queries[-1].timestamp if queries else None
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                'total_queries': 0,
                'average_rating': 0,
                'intent_distribution': {},
                'sentiment_distribution': {},
                'last_query': None
            }
        finally:
            session.close()

    def get_analytics_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics data for admin dashboard."""
        try:
            session = self.get_session()
            
            # User statistics
            total_users = session.query(User).count()
            active_users = session.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(days=30)
            ).count()
            new_users = session.query(User).filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            # Query statistics
            queries = session.query(UserQuery).all()
            
            # Initialize data structures
            time_series = {}
            ratings_distribution = {i: 0 for i in range(1, 6)}
            location_data = []
            intent_distribution = {}
            sentiment_distribution = {}
            
            # Process queries
            for query in queries:
                # Time series data
                date = query.timestamp.date().isoformat()
                time_series[date] = time_series.get(date, 0) + 1
                
                # Ratings distribution
                if query.rating:
                    ratings_distribution[query.rating] = ratings_distribution.get(query.rating, 0) + 1
                
                # Intent distribution
                if query.intent:
                    intent_distribution[query.intent] = intent_distribution.get(query.intent, 0) + 1
                
                # Sentiment distribution
                if query.sentiment:
                    sentiment_distribution[query.sentiment] = sentiment_distribution.get(query.sentiment, 0) + 1
                
                # Location data
                if query.user and query.user.latitude and query.user.longitude:
                    location_data.append({
                        'latitude': query.user.latitude,
                        'longitude': query.user.longitude,
                        'location': query.location or 'Unknown',
                        'query_count': 1,
                        'avg_rating': query.rating or 0,
                        'intent': query.intent,
                        'sentiment': query.sentiment
                    })
            
            # Aggregate location data
            location_aggregate = {}
            for loc in location_data:
                key = (loc['latitude'], loc['longitude'])
                if key in location_aggregate:
                    location_aggregate[key]['query_count'] += 1
                    location_aggregate[key]['avg_rating'] = (
                        (location_aggregate[key]['avg_rating'] * (location_aggregate[key]['query_count'] - 1) + loc['avg_rating'])
                        / location_aggregate[key]['query_count']
                    )
                    # Update intent and sentiment distributions
                    if loc['intent']:
                        location_aggregate[key]['intents'] = location_aggregate[key].get('intents', {})
                        location_aggregate[key]['intents'][loc['intent']] = location_aggregate[key]['intents'].get(loc['intent'], 0) + 1
                    if loc['sentiment']:
                        location_aggregate[key]['sentiments'] = location_aggregate[key].get('sentiments', {})
                        location_aggregate[key]['sentiments'][loc['sentiment']] = location_aggregate[key]['sentiments'].get(loc['sentiment'], 0) + 1
                else:
                    location_aggregate[key] = {
                        'latitude': loc['latitude'],
                        'longitude': loc['longitude'],
                        'location': loc['location'],
                        'query_count': 1,
                        'avg_rating': loc['avg_rating'],
                        'intents': {loc['intent']: 1} if loc['intent'] else {},
                        'sentiments': {loc['sentiment']: 1} if loc['sentiment'] else {}
                    }
            
            return {
                'user_stats': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'new_users_30d': new_users,
                    'growth_rate': (new_users / total_users * 100) if total_users > 0 else 0
                },
                'query_stats': {
                    'time_series': time_series,
                    'ratings_distribution': ratings_distribution,
                    'intent_distribution': intent_distribution,
                    'sentiment_distribution': sentiment_distribution,
                    'location_data': list(location_aggregate.values())
                }
            }
        except Exception as e:
            logger.error(f"Failed to get analytics data: {e}")
            return {
                'user_stats': {
                    'total_users': 0,
                    'active_users': 0,
                    'new_users_30d': 0,
                    'growth_rate': 0
                },
                'query_stats': {
                    'time_series': {},
                    'ratings_distribution': {i: 0 for i in range(1, 6)},
                    'intent_distribution': {},
                    'sentiment_distribution': {},
                    'location_data': []
                }
            }
        finally:
            session.close()

    def _create_admin_user(self):
        """Create admin user if not exists."""
        try:
            session = self.Session()
            admin = session.query(User).filter_by(email="admin@teller.ai").first()
            if not admin:
                admin = User(
                    name="Admin",
                    phone="0000000000",
                    email="admin@teller.ai",
                    password=hash_password("admin123"),  # Change this in production
                    account_number="0000000000",
                    is_admin=True,
                    created_at=datetime.utcnow()
                )
                session.add(admin)
                session.commit()
                logger.info("Created admin user")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating admin user: {e}")
        finally:
            session.close()

    def get_regional_stats(self, intent: str, location: str) -> Dict[str, Any]:
        """
        Get statistics for queries with the same intent in the same region.
        
        Args:
            intent (str): The query intent
            location (str): The user's location
            
        Returns:
            Dict[str, Any]: Regional statistics
        """
        try:
            session = self.Session()
            queries = session.query(UserQuery).filter(
                UserQuery.intent == intent,
                UserQuery.location == location
            ).all()
            
            return {
                'total_queries': len(queries),
                'avg_rating': sum(q.rating or 0 for q in queries) / len(queries) if queries else 0,
                'sentiment_distribution': {
                    s: len([q for q in queries if q.sentiment == s])
                    for s in set(q.sentiment for q in queries if q.sentiment)
                },
                'resolution_times': [q.resolution_time for q in queries if q.resolution_time]
            }
        except Exception as e:
            logger.error(f"Error getting regional stats: {e}")
            return {}
        finally:
            session.close()

    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics data for a specific user."""
        try:
            session = self.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # Get user's queries
            queries = session.query(UserQuery).filter(UserQuery.user_id == user_id).all()
            
            # Calculate statistics
            total_queries = len(queries)
            ratings = [q.rating for q in queries if q.rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Initialize distributions
            intent_distribution = {}
            sentiment_distribution = {}
            ratings_distribution = {i: 0 for i in range(1, 6)}
            time_series = {}
            
            # Process queries
            for query in queries:
                # Intent distribution
                if query.intent:
                    intent_distribution[query.intent] = intent_distribution.get(query.intent, 0) + 1
                
                # Sentiment distribution
                if query.sentiment:
                    sentiment_distribution[query.sentiment] = sentiment_distribution.get(query.sentiment, 0) + 1
                
                # Ratings distribution
                if query.rating:
                    ratings_distribution[query.rating] = ratings_distribution.get(query.rating, 0) + 1
                
                # Time series
                date = query.timestamp.date().isoformat()
                time_series[date] = time_series.get(date, 0) + 1
            
            # Calculate resolution time statistics
            resolution_times = [q.resolution_time for q in queries if q.resolution_time]
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            return {
                'user_info': {
                    'name': user.name,
                    'email': user.email,
                    'last_login': user.last_login,
                    'login_count': user.login_count,
                    'account_number': user.account_number,
                    'created_at': user.created_at
                },
                'query_stats': {
                    'total_queries': total_queries,
                    'avg_rating': avg_rating,
                    'avg_resolution_time': avg_resolution_time,
                    'intent_distribution': intent_distribution,
                    'sentiment_distribution': sentiment_distribution,
                    'ratings_distribution': ratings_distribution,
                    'time_series': time_series
                }
            }
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}
        finally:
            session.close()