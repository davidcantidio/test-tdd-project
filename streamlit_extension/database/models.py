"""
🗄️ Database Models for Streamlit Extension

SQLAlchemy models that integrate with the existing framework.db structure:
- Framework epics and tasks
- Timer sessions integration
- User gamification data
- GitHub sync records
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Graceful imports
try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Float
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker
    from sqlalchemy import create_engine
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    Column = Integer = String = DateTime = Text = JSON = Boolean = ForeignKey = Float = None
    relationship = sessionmaker = create_engine = None


if SQLALCHEMY_AVAILABLE:
    class FrameworkEpic(Base):
        """Framework Epic model matching existing database schema."""
        __tablename__ = 'framework_epics'
        
        id = Column(Integer, primary_key=True)
        epic_key = Column(String(50), unique=True, nullable=False)
        name = Column(String(200), nullable=False)
        description = Column(Text)
        status = Column(String(20), default='planning')
        priority = Column(Integer, default=1)
        difficulty_level = Column(Integer, default=1)
        points_earned = Column(Integer, default=0)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        completed_at = Column(DateTime)
        deleted_at = Column(DateTime)
        
        # Relationships
        tasks = relationship("FrameworkTask", back_populates="epic")
    
    class FrameworkTask(Base):
        """Framework Task model matching existing database schema."""
        __tablename__ = 'framework_tasks'
        
        id = Column(Integer, primary_key=True)
        epic_id = Column(Integer, ForeignKey('framework_epics.id'), nullable=False)
        title = Column(String(200), nullable=False)
        description = Column(Text)
        status = Column(String(20), default='todo')
        tdd_phase = Column(String(20))  # 'red', 'green', 'refactor'
        priority = Column(Integer, default=1)
        estimate_minutes = Column(Integer)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        completed_at = Column(DateTime)
        deleted_at = Column(DateTime)
        
        # Relationships
        epic = relationship("FrameworkEpic", back_populates="tasks")
    
    class TimerSession(Base):
        """Timer session model matching task_timer.db schema."""
        __tablename__ = 'timer_sessions'
        
        id = Column(Integer, primary_key=True)
        task_reference = Column(String(100))  # Can reference framework_tasks.id
        user_identifier = Column(String(100), default='user1')
        
        # Time tracking
        started_at = Column(DateTime)
        ended_at = Column(DateTime)
        planned_duration_minutes = Column(Integer)
        actual_duration_minutes = Column(Integer)
        
        # TDAH metrics
        focus_rating = Column(Integer)  # 1-10
        energy_level = Column(Integer)  # 1-10
        mood_rating = Column(Integer)   # 1-10
        interruptions_count = Column(Integer, default=0)
        notes = Column(Text)
        
        # Audit
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class UserAchievement(Base):
        """User achievements for gamification."""
        __tablename__ = 'user_achievements'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, default=1)
        achievement_code = Column(String(50), nullable=False)
        unlocked_at = Column(DateTime, default=datetime.utcnow)
        
        # Metadata
        context_data = Column(JSON)  # Additional data about when/how achieved
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class UserStreak(Base):
        """User productivity streaks."""
        __tablename__ = 'user_streaks'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, default=1)
        streak_type = Column(String(50), nullable=False)  # 'daily_focus', 'weekly_commits', etc
        current_count = Column(Integer, default=0)
        best_count = Column(Integer, default=0)
        last_activity_date = Column(DateTime)
        
        # Audit
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@dataclass
class EpicProgress:
    """Data class for epic progress calculations."""
    epic_id: int
    epic_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    progress_percentage: float
    points_earned: int


@dataclass
class TimerStats:
    """Data class for timer statistics."""
    total_sessions: int
    total_focus_time: int  # minutes
    average_focus_rating: float
    total_interruptions: int
    best_streak: int


def create_database_engine(database_url: str = "sqlite:///./framework.db"):
    """Create SQLAlchemy engine for database operations."""
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy not available. Install with: pip install sqlalchemy")
    
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    
    return engine


def create_session(engine):
    """Create SQLAlchemy session."""
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy not available")
    
    Session = sessionmaker(bind=engine)
    return Session()


def initialize_database(engine):
    """Initialize database tables (create if not exist)."""
    if not SQLALCHEMY_AVAILABLE:
        return False
    
    try:
        # This will create tables that don't exist
        # Existing tables with data will not be affected
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


# Fallback classes for when SQLAlchemy is not available
class DatabaseModelsUnavailable:
    """Fallback when SQLAlchemy is not available."""
    
    def __init__(self):
        self.available = False
    
    def __getattr__(self, name):
        raise ImportError(f"SQLAlchemy not available. Cannot access {name}. Install with: pip install sqlalchemy")


# Export appropriate classes based on availability
if SQLALCHEMY_AVAILABLE:
    __all__ = [
        'FrameworkEpic', 'FrameworkTask', 'TimerSession', 
        'UserAchievement', 'UserStreak', 'EpicProgress', 'TimerStats',
        'create_database_engine', 'create_session', 'initialize_database'
    ]
else:
    # Provide fallback
    FrameworkEpic = FrameworkTask = TimerSession = DatabaseModelsUnavailable()
    UserAchievement = UserStreak = EpicProgress = TimerStats = DatabaseModelsUnavailable()
    create_database_engine = create_session = initialize_database = DatabaseModelsUnavailable()
    
    __all__ = ['DatabaseModelsUnavailable']