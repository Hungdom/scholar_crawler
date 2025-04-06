from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from .models import Base
from ..config.settings import DB_CONFIG
from ..crawler.utils.logger import setup_logger
import time

logger = setup_logger(__name__)

def get_db_url():
    """Create database URL from configuration"""
    url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    logger.debug(f"Database URL: {url}")
    return url

def wait_for_db(max_retries=5, delay=2):
    """Wait for database to become available"""
    for attempt in range(max_retries):
        try:
            # Try to create an engine and connect
            temp_engine = create_engine(get_db_url())
            with temp_engine.connect() as conn:
                logger.info("Successfully connected to database")
                temp_engine.dispose()
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise
    return False

# Wait for database to be ready
wait_for_db()

# Create a single engine instance with connection pooling
engine = create_engine(
    get_db_url(),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=True  # Enable SQL logging
)
logger.info("Database engine created with connection pooling")

def init_db():
    """Initialize the database and create tables"""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Initialize database tables
init_db()

# Create a session factory with scoped sessions
Session = scoped_session(
    sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=True,
        expire_on_commit=False
    )
)
logger.info("Session factory created")

def get_session():
    """Create and return a database session"""
    try:
        session = Session()
        logger.debug("New database session created")
        return session
    except Exception as e:
        logger.error(f"Error creating database session: {e}")
        raise 