from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class IssueSeverity(str, enum.Enum):
    LOW = "low"           # Χαμηλή
    MEDIUM = "medium"     # Μέτρια
    HIGH = "high"         # Υψηλή
    CRITICAL = "critical" # Κρίσιμη

class IssueStatus(str, enum.Enum):
    OPEN = "open"           # Ανοιχτό
    IN_PROGRESS = "in_progress"  # Σε εξέλιξη
    RESOLVED = "resolved"   # Επιλύθηκε
    CLOSED = "closed"       # Κλειστό

class IssueCategory(str, enum.Enum):
    DELAY = "delay"                 # Καθυστέρηση
    QUALITY = "quality"             # Ποιότητα
    SAFETY = "safety"               # Ασφάλεια
    MATERIAL = "material"           # Υλικό
    EQUIPMENT = "equipment"         # Εξοπλισμός
    WEATHER = "weather"             # Καιρός
    LABOR = "labor"                 # Εργατικό
    OTHER = "other"                 # Άλλο

class WeatherCondition(str, enum.Enum):
    SUNNY = "sunny"           # Ηλιόφανο
    CLOUDY = "cloudy"         # Συννεφιά
    RAINY = "rainy"           # Βροχή
    STORMY = "stormy"         # Καταιγίδα
    WINDY = "windy"           # Άνεμος
    SNOW = "snow"             # Χιόνι
    FOG = "fog"               # Ομίχλη

class DailyReport(Base):
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(Date, nullable=False, index=True)
    
    # Καιρικές συνθήκες
    weather_condition = Column(Enum(WeatherCondition), nullable=True)
    temperature = Column(Float, nullable=True)  # Celsius
    weather_notes = Column(Text)  # π.χ. "Βροχή το απόγευμα"
    
    # Εργατικό δυναμικό
    workers_count = Column(Integer, default=0)
    workers_present = Column(Text)  # Comma-separated names or IDs
    workers_absent = Column(Text)   # Ονόματα απόντων
    
    # Εργασίες που έγιναν
    work_description = Column(Text, nullable=False)  # Κύρια εργασία
    work_completed = Column(Text)    # Τι ολοκληρώθηκε
    work_in_progress = Column(Text)  # Τι είναι σε εξέλιξη
    
    # Πρόοδος
    progress_percentage = Column(Float, default=0.0)  # 0-100
    progress_notes = Column(Text)
    
    # Υλικά που χρησιμοποιήθηκαν (summary)
    materials_used_summary = Column(Text)  # "Σίδερο Φ12: 450kg, Τσιμέντο: 120 σακιά"
    
    # Εξοπλισμός που χρησιμοποιήθηκε
    equipment_used = Column(Text)  # "Γερανός, Μπετονιέρα, Ικριώματα"
    
    # Προβλήματα summary
    issues_summary = Column(Text)  # Quick summary
    
    # Παρατηρήσεις / Σημειώσεις
    observations = Column(Text)
    safety_notes = Column(Text)  # Σημειώσεις ασφαλείας
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="daily_reports")
    creator = relationship("User")
    issues = relationship("Issue", back_populates="daily_report")
    photos = relationship("ReportPhoto", back_populates="daily_report")

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=True)
    
    # Βασικά στοιχεία
    title = Column(String(200), nullable=False)  # Σύντομος τίτλος
    description = Column(Text, nullable=False)    # Λεπτομερής περιγραφή
    
    # Κατηγοριοποίηση
    category = Column(Enum(IssueCategory), nullable=False)
    severity = Column(Enum(IssueSeverity), nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN)
    
    # Χρονοδιάγραμμα
    reported_date = Column(DateTime, default=datetime.utcnow, index=True)
    due_date = Column(Date, nullable=True)
    resolved_date = Column(DateTime, nullable=True)
    
    # Επίλυση
    resolution_notes = Column(Text)
    resolution_cost = Column(Float)  # Κόστος επίλυσης
    
    # Impact
    delay_days = Column(Integer, default=0)  # Καθυστέρηση σε ημέρες
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="issues")
    daily_report = relationship("DailyReport", back_populates="issues")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    reporter = relationship("User", foreign_keys=[reported_by])
    photos = relationship("IssuePhoto", back_populates="issue")

class WorkItem(Base):
    __tablename__ = "work_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Εργασία
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # π.χ. "Σκυρόδεμα", "Σιδηρά", "Ηλεκτρολογικά"
    
    # Χρονοδιάγραμμα
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    
    # Πρόοδος
    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    completion_percentage = Column(Float, default=0.0)
    
    # Assignment
    assigned_to = Column(Text)  # Ομάδα/άτομα που αναλαμβάνουν
    
    # Dependencies
    depends_on = Column(Text)  # IDs άλλων work items (comma-separated)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="work_items")

class LaborLog(Base):
    __tablename__ = "labor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=True)
    
    # Εργάτης
    worker_name = Column(String(100), nullable=False)
    worker_role = Column(String(100))  # π.χ. "Σιδηράς", "Ελαιοχρωματιστής"
    
    # Χρόνος
    work_date = Column(Date, nullable=False, index=True)
    hours_worked = Column(Float, default=8.0)
    overtime_hours = Column(Float, default=0.0)
    
    # Κόστος
    hourly_rate = Column(Float)
    total_cost = Column(Float)
    
    # Σημειώσεις
    tasks_performed = Column(Text)  # Τι έκανε
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="labor_logs")
    daily_report = relationship("DailyReport")

class EquipmentLog(Base):
    __tablename__ = "equipment_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=True)
    
    # Εξοπλισμός
    equipment_name = Column(String(100), nullable=False)
    equipment_type = Column(String(100))  # "Γερανός", "Μπετονιέρα", etc.
    
    # Χρήση
    usage_date = Column(Date, nullable=False, index=True)
    hours_used = Column(Float, default=0.0)
    
    # Κόστος
    rental_cost = Column(Float)
    fuel_cost = Column(Float)
    maintenance_cost = Column(Float)
    
    # Σημειώσεις
    operator_name = Column(String(100))
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="equipment_logs")
    daily_report = relationship("DailyReport")

class ReportPhoto(Base):
    __tablename__ = "report_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=False)
    
    title = Column(String(200))
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    
    # Metadata
    taken_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    daily_report = relationship("DailyReport", back_populates="photos")
    uploader = relationship("User")

class IssuePhoto(Base):
    __tablename__ = "issue_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    
    title = Column(String(200))
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    
    # Metadata
    taken_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    issue = relationship("Issue", back_populates="photos")
    uploader = relationship("User")
