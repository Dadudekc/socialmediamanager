#!/usr/bin/env python3
"""
Calendar Widget for Social Media GUI
===================================

A custom calendar widget for scheduling posts and campaigns.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCalendarWidget, QTimeEdit, QDateEdit,
                             QGroupBox, QTextEdit, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta

class SocialMediaCalendar(QWidget):
    """Custom calendar widget for social media scheduling."""
    
    date_selected = pyqtSignal(QDate)
    schedule_created = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the calendar UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📅 Post Scheduler")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 10px;")
        layout.addWidget(title)
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)
        
        # Schedule group
        schedule_group = QGroupBox("Schedule Post")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # Date and time selection
        datetime_layout = QHBoxLayout()
        
        # Date
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        datetime_layout.addLayout(date_layout)
        
        # Time
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(self.time_edit)
        datetime_layout.addLayout(time_layout)
        
        schedule_layout.addLayout(datetime_layout)
        
        # Post content
        schedule_layout.addWidget(QLabel("Post Content:"))
        self.post_content = QTextEdit()
        self.post_content.setPlaceholderText("Enter your post content here...")
        self.post_content.setMaximumHeight(100)
        schedule_layout.addWidget(self.post_content)
        
        # Platform selection
        schedule_layout.addWidget(QLabel("Platforms:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["All Platforms", "LinkedIn", "Twitter", "Facebook", "Instagram", "Reddit", "Discord", "Stocktwits"])
        schedule_layout.addWidget(self.platform_combo)
        
        # Schedule button
        self.schedule_button = QPushButton("📅 Schedule Post")
        self.schedule_button.clicked.connect(self.schedule_post)
        schedule_layout.addWidget(self.schedule_button)
        
        layout.addWidget(schedule_group)
        
        # Scheduled posts list
        scheduled_group = QGroupBox("Scheduled Posts")
        scheduled_layout = QVBoxLayout(scheduled_group)
        
        self.scheduled_posts = QTextEdit()
        self.scheduled_posts.setReadOnly(True)
        self.scheduled_posts.setMaximumHeight(150)
        scheduled_layout.addWidget(self.scheduled_posts)
        
        layout.addWidget(scheduled_group)
        
    def on_date_selected(self, date):
        """Handle date selection."""
        self.date_edit.setDate(date)
        self.date_selected.emit(date)
        
    def schedule_post(self):
        """Schedule a post."""
        try:
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            datetime_obj = datetime.combine(date, time)
            
            content = self.post_content.toPlainText().strip()
            platform = self.platform_combo.currentText()
            
            if not content:
                return
                
            schedule_data = {
                "datetime": datetime_obj,
                "content": content,
                "platform": platform,
                "status": "scheduled"
            }
            
            # Add to scheduled posts list
            self.scheduled_posts.append(f"[{datetime_obj.strftime('%Y-%m-%d %H:%M')}] {platform}: {content[:50]}...")
            
            # Clear the form
            self.post_content.clear()
            
            # Emit signal
            self.schedule_created.emit(schedule_data)
            
        except Exception as e:
            print(f"Error scheduling post: {e}")

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background: #1e1e1e;
            color: white;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #444;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00d4ff;
        }
        QPushButton {
            background: #00d4ff;
            color: black;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #00b8e6;
        }
        QTextEdit, QLineEdit, QComboBox, QDateEdit, QTimeEdit {
            background: #2b2b2b;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 8px;
            color: white;
        }
        QCalendarWidget {
            background: #2b2b2b;
            color: white;
        }
    """)
    
    window = SocialMediaCalendar()
    window.show()
    sys.exit(app.exec()) 