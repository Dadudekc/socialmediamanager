#!/usr/bin/env python3
"""
Enhanced Social Media GUI with Calendar
======================================

Modern PyQt6 GUI with calendar scheduling, dashboard, and additional features.
"""

import sys
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import queue

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTextEdit, QLineEdit, 
                             QPushButton, QLabel, QCheckBox, QComboBox, 
                             QSpinBox, QGroupBox, QScrollArea, QFrame,
                             QMessageBox, QFileDialog, QProgressBar,
                             QSplitter, QListWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QInputDialog,
                             QCalendarWidget, QTimeEdit, QDateEdit,
                             QGridLayout, QSlider, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDate, QTime
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

from unified_social_manager import UnifiedSocialManager
from social_media_automation import PlatformType
from content_manager import ContentCategory

class EnhancedSocialMediaGUI(QMainWindow):
    """Enhanced GUI with calendar and additional features."""
    
    def __init__(self):
        super().__init__()
        self.manager = UnifiedSocialManager()
        self.message_queue = queue.Queue()
        self.scheduled_posts = []
        
        # Platform mapping
        self.platform_map = {
            "LinkedIn": PlatformType.LINKEDIN,
            "Twitter": PlatformType.TWITTER,
            "Facebook": PlatformType.FACEBOOK,
            "Instagram": PlatformType.INSTAGRAM,
            "Reddit": PlatformType.REDDIT,
            "Discord": PlatformType.DISCORD,
            "Stocktwits": PlatformType.STOCKTWITS
        }
        
        self.setup_ui()
        self.setup_dark_theme()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("🚀 Enhanced Social Media Automation System")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header with stats
        self.create_header(main_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #3c3c3c;
                color: white;
                padding: 12px 24px;
                margin: 2px;
                border-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #00d4ff;
                color: black;
            }
        """)
        
        # Create enhanced tabs
        self.create_dashboard_tab()
        self.create_posting_tab()
        self.create_calendar_tab()
        self.create_campaigns_tab()
        self.create_analytics_tab()
        self.create_automation_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                color: #00d4ff;
                padding: 12px;
                border-top: 2px solid #444;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.status_bar)
        
    def create_header(self, layout):
        """Create header with quick stats."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #1e1e1e 0%, #2b2b2b 100%);
                border-radius: 10px;
                margin: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title = QLabel("🚀 Enhanced Social Media Automation System")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        header_layout.addWidget(title)
        
        # Quick stats
        stats_layout = QHBoxLayout()
        
        # Posts today
        posts_today = QLabel("📝 Posts Today: 0")
        posts_today.setStyleSheet("color: #00ff88; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(posts_today)
        
        # Campaigns active
        campaigns_active = QLabel("📋 Active Campaigns: 0")
        campaigns_active.setStyleSheet("color: #ffaa00; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(campaigns_active)
        
        # Scheduled posts
        scheduled_posts = QLabel("📅 Scheduled Posts: 0")
        scheduled_posts.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(scheduled_posts)
        
        header_layout.addLayout(stats_layout)
        layout.addWidget(header_frame)
        
    def create_dashboard_tab(self):
        """Create dashboard tab with overview."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("📊 Dashboard Overview")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Dashboard grid
        dashboard_layout = QGridLayout()
        
        # Quick actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Quick post button
        quick_post_btn = QPushButton("📝 Quick Post")
        quick_post_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #00d4ff 0%, #00b8e6 100%);
                color: black;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #00b8e6 0%, #0099cc 100%);
            }
        """)
        actions_layout.addWidget(quick_post_btn)
        
        # Schedule post button
        schedule_btn = QPushButton("📅 Schedule Post")
        schedule_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #ff5252 0%, #ff3838 100%);
            }
        """)
        actions_layout.addWidget(schedule_btn)
        
        # Start campaign button
        campaign_btn = QPushButton("📋 Start Campaign")
        campaign_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #44a08d 0%, #3a8b7a 100%);
            }
        """)
        actions_layout.addWidget(campaign_btn)
        
        dashboard_layout.addWidget(actions_group, 0, 0)
        
        # Platform status
        status_group = QGroupBox("🔗 Platform Status")
        status_layout = QVBoxLayout(status_group)
        
        self.platform_status_labels = {}
        for platform_name in self.platform_map.keys():
            label = QLabel(f"❌ {platform_name}")
            label.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 5px;")
            self.platform_status_labels[platform_name] = label
            status_layout.addWidget(label)
        
        dashboard_layout.addWidget(status_group, 0, 1)
        
        # Recent activity
        activity_group = QGroupBox("📈 Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QTextEdit()
        self.activity_list.setReadOnly(True)
        self.activity_list.setMaximumHeight(200)
        self.activity_list.setStyleSheet("""
            QTextEdit {
                background: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                color: #e0e0e0;
                font-family: 'Consolas', monospace;
            }
        """)
        activity_layout.addWidget(self.activity_list)
        
        dashboard_layout.addWidget(activity_group, 1, 0, 1, 2)
        
        layout.addLayout(dashboard_layout)
        
        self.tab_widget.addTab(tab, "📊 Dashboard")
        
    def create_calendar_tab(self):
        """Create calendar tab for scheduling."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("📅 Post Scheduler")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Calendar and scheduling
        calendar_layout = QHBoxLayout()
        
        # Calendar widget
        calendar_group = QGroupBox("📅 Calendar")
        calendar_layout_inner = QVBoxLayout(calendar_group)
        
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.clicked.connect(self.on_date_selected)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background: #2b2b2b;
                color: white;
            }
            QCalendarWidget QToolButton {
                background: #3c3c3c;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background: #00d4ff;
                color: black;
            }
        """)
        calendar_layout_inner.addWidget(self.calendar)
        
        calendar_layout.addWidget(calendar_group)
        
        # Scheduling panel
        schedule_group = QGroupBox("⏰ Schedule Post")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # Date and time
        datetime_layout = QHBoxLayout()
        
        # Date
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("📅 Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        datetime_layout.addLayout(date_layout)
        
        # Time
        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("⏰ Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(self.time_edit)
        datetime_layout.addLayout(time_layout)
        
        schedule_layout.addLayout(datetime_layout)
        
        # Post content
        schedule_layout.addWidget(QLabel("📝 Post Content:"))
        self.schedule_post_content = QTextEdit()
        self.schedule_post_content.setPlaceholderText("Enter your post content here...")
        self.schedule_post_content.setMaximumHeight(100)
        schedule_layout.addWidget(self.schedule_post_content)
        
        # Platforms
        schedule_layout.addWidget(QLabel("🌐 Platforms:"))
        self.schedule_platform_combo = QComboBox()
        self.schedule_platform_combo.addItems(["All Platforms", "LinkedIn", "Twitter", "Facebook", "Instagram", "Reddit", "Discord", "Stocktwits"])
        schedule_layout.addWidget(self.schedule_platform_combo)
        
        # Schedule button
        self.schedule_button = QPushButton("📅 Schedule Post")
        self.schedule_button.clicked.connect(self.schedule_post)
        self.schedule_button.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #ff5252 0%, #ff3838 100%);
            }
        """)
        schedule_layout.addWidget(self.schedule_button)
        
        calendar_layout.addWidget(schedule_group)
        layout.addLayout(calendar_layout)
        
        # Scheduled posts list
        scheduled_group = QGroupBox("📋 Scheduled Posts")
        scheduled_layout = QVBoxLayout(scheduled_group)
        
        self.scheduled_posts_list = QTextEdit()
        self.scheduled_posts_list.setReadOnly(True)
        self.scheduled_posts_list.setMaximumHeight(200)
        scheduled_layout.addWidget(self.scheduled_posts_list)
        
        layout.addWidget(scheduled_group)
        
        self.tab_widget.addTab(tab, "📅 Calendar")
        
    def create_posting_tab(self):
        """Create enhanced posting tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("📝 Multi-Platform Posting")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Content group
        content_group = QGroupBox("📝 Post Content")
        content_layout = QVBoxLayout(content_group)
        
        # Text area with character counter
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Post Text:"))
        
        self.char_counter = QLabel("0 characters")
        self.char_counter.setStyleSheet("color: #00d4ff; font-weight: bold;")
        text_layout.addWidget(self.char_counter)
        
        content_layout.addLayout(text_layout)
        
        self.post_text = QTextEdit()
        self.post_text.setPlaceholderText("Enter your post content here...")
        self.post_text.setMaximumHeight(150)
        self.post_text.textChanged.connect(self.update_char_counter)
        content_layout.addWidget(self.post_text)
        
        # Options
        options_layout = QHBoxLayout()
        
        # Hashtags
        hashtags_layout = QVBoxLayout()
        hashtags_layout.addWidget(QLabel("🏷️ Hashtags:"))
        self.hashtags_input = QLineEdit()
        self.hashtags_input.setPlaceholderText("innovation, tech, automation")
        hashtags_layout.addWidget(self.hashtags_input)
        options_layout.addLayout(hashtags_layout)
        
        # Mentions
        mentions_layout = QVBoxLayout()
        mentions_layout.addWidget(QLabel("👥 Mentions:"))
        self.mentions_input = QLineEdit()
        self.mentions_input.setPlaceholderText("user1, user2")
        mentions_layout.addWidget(self.mentions_input)
        options_layout.addLayout(mentions_layout)
        
        content_layout.addLayout(options_layout)
        layout.addWidget(content_group)
        
        # Platforms group with visual indicators
        platforms_group = QGroupBox("🌐 Platforms")
        platforms_layout = QVBoxLayout(platforms_group)
        
        # Platform checkboxes with icons
        self.platform_checkboxes = {}
        platforms_grid = QHBoxLayout()
        
        platform_icons = {
            "LinkedIn": "💼",
            "Twitter": "🐦", 
            "Facebook": "📘",
            "Instagram": "📷",
            "Reddit": "🤖",
            "Discord": "🎮",
            "Stocktwits": "📈"
        }
        
        for name, icon in platform_icons.items():
            checkbox = QCheckBox(f"{icon} {name}")
            checkbox.setChecked(True)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 5px;
                    background: #3c3c3c;
                }
                QCheckBox:hover {
                    background: #4c4c4c;
                }
            """)
            self.platform_checkboxes[name] = checkbox
            platforms_grid.addWidget(checkbox)
        
        platforms_layout.addLayout(platforms_grid)
        layout.addWidget(platforms_group)
        
        # Buttons with enhanced styling
        buttons_layout = QHBoxLayout()
        
        self.post_button = QPushButton("🚀 Post to Selected")
        self.post_button.clicked.connect(self.post_content)
        self.post_button.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #00d4ff 0%, #00b8e6 100%);
                color: black;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #00b8e6 0%, #0099cc 100%);
            }
        """)
        buttons_layout.addWidget(self.post_button)
        
        self.post_all_button = QPushButton("🌐 Post to All")
        self.post_all_button.clicked.connect(self.post_to_all)
        self.post_all_button.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #44a08d 0%, #3a8b7a 100%);
            }
        """)
        buttons_layout.addWidget(self.post_all_button)
        
        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_posting_form)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #ff5252 0%, #ff3838 100%);
            }
        """)
        buttons_layout.addWidget(self.clear_button)
        
        layout.addLayout(buttons_layout)
        
        # Results with enhanced styling
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout(results_group)
        
        self.posting_results = QTextEdit()
        self.posting_results.setReadOnly(True)
        self.posting_results.setMaximumHeight(200)
        self.posting_results.setStyleSheet("""
            QTextEdit {
                background: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                color: #e0e0e0;
                font-family: 'Consolas', monospace;
            }
        """)
        results_layout.addWidget(self.posting_results)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "📝 Posting")
        
    def create_campaigns_tab(self):
        """Create enhanced campaigns tab."""
        # Similar to before but with enhanced styling
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("📋 Campaign Management")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Add campaign creation form here
        layout.addWidget(QLabel("Campaign features coming soon..."))
        
        self.tab_widget.addTab(tab, "📋 Campaigns")
        
    def create_analytics_tab(self):
        """Create enhanced analytics tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("📊 Analytics Dashboard")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Add analytics features here
        layout.addWidget(QLabel("Analytics features coming soon..."))
        
        self.tab_widget.addTab(tab, "📊 Analytics")
        
    def create_automation_tab(self):
        """Create enhanced automation tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("🤖 Automated Tasks")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00d4ff; padding: 20px;")
        layout.addWidget(title)
        
        # Add automation features here
        layout.addWidget(QLabel("Automation features coming soon..."))
        
        self.tab_widget.addTab(tab, "🤖 Automation")
        
    def setup_dark_theme(self):
        """Setup modern dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: #1e1e1e;
                color: white;
            }
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
            QPushButton:pressed {
                background: #0099cc;
            }
            QPushButton:disabled {
                background: #555;
                color: #888;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {
                background: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
                color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #00d4ff;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #444;
                border-radius: 3px;
                background: #2b2b2b;
            }
            QCheckBox::indicator:checked {
                background: #00d4ff;
                border: 2px solid #00d4ff;
            }
        """)
        
    def setup_timer(self):
        """Setup timer for message processing."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_messages)
        self.timer.start(100)
        
    def update_char_counter(self):
        """Update character counter."""
        count = len(self.post_text.toPlainText())
        self.char_counter.setText(f"{count} characters")
        
        # Change color based on platform limits
        if count > 280:  # Twitter limit
            self.char_counter.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        elif count > 200:
            self.char_counter.setStyleSheet("color: #ffaa00; font-weight: bold;")
        else:
            self.char_counter.setStyleSheet("color: #00d4ff; font-weight: bold;")
            
    def on_date_selected(self, date):
        """Handle date selection."""
        self.date_edit.setDate(date)
        
    def schedule_post(self):
        """Schedule a post."""
        try:
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            datetime_obj = datetime.combine(date, time)
            
            content = self.schedule_post_content.toPlainText().strip()
            platform = self.schedule_platform_combo.currentText()
            
            if not content:
                QMessageBox.warning(self, "Warning", "Please enter post content!")
                return
                
            schedule_data = {
                "datetime": datetime_obj,
                "content": content,
                "platform": platform,
                "status": "scheduled"
            }
            
            # Add to scheduled posts list
            self.scheduled_posts.append(schedule_data)
            self.scheduled_posts_list.append(f"[{datetime_obj.strftime('%Y-%m-%d %H:%M')}] {platform}: {content[:50]}...")
            
            # Clear the form
            self.schedule_post_content.clear()
            
            QMessageBox.information(self, "Success", f"Post scheduled for {datetime_obj.strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error scheduling post: {str(e)}")
            
    def process_messages(self):
        """Process messages from the queue."""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.log_message(message['text'], message['tab'])
        except queue.Empty:
            pass
            
    def log_message(self, message: str, tab="posting"):
        """Log a message to the appropriate tab."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        if tab == "posting":
            self.posting_results.append(formatted_message)
        elif tab == "dashboard":
            self.activity_list.append(formatted_message)
            
    def post_content(self):
        """Post content to selected platforms."""
        def post_thread():
            try:
                self.update_status("Posting content...")
                
                # Get selected platforms
                selected_platforms = []
                for name, checkbox in self.platform_checkboxes.items():
                    if checkbox.isChecked():
                        selected_platforms.append(self.platform_map[name])
                
                if not selected_platforms:
                    self.message_queue.put({'text': 'No platforms selected!', 'tab': 'posting'})
                    return
                
                # Get content
                text = self.post_text.toPlainText().strip()
                if not text:
                    self.message_queue.put({'text': 'No content to post!', 'tab': 'posting'})
                    return
                
                # Get hashtags and mentions
                hashtags = [tag.strip() for tag in self.hashtags_input.text().split(',') if tag.strip()]
                mentions = [mention.strip() for mention in self.mentions_input.text().split(',') if mention.strip()]
                
                # Post content
                result = self.manager.post_to_specific_platforms(
                    text=text,
                    platforms=selected_platforms,
                    hashtags=hashtags,
                    mentions=mentions
                )
                
                # Log results
                self.message_queue.put({'text': f'Posting completed!', 'tab': 'posting'})
                self.message_queue.put({'text': f'Results: {json.dumps(result, indent=2)}', 'tab': 'posting'})
                self.update_status("Post completed successfully")
                
            except Exception as e:
                self.message_queue.put({'text': f'Error posting: {str(e)}', 'tab': 'posting'})
                self.update_status("Post failed")
        
        threading.Thread(target=post_thread, daemon=True).start()
        
    def post_to_all(self):
        """Post content to all platforms."""
        def post_thread():
            try:
                self.update_status("Posting to all platforms...")
                
                text = self.post_text.toPlainText().strip()
                if not text:
                    self.message_queue.put({'text': 'No content to post!', 'tab': 'posting'})
                    return
                
                hashtags = [tag.strip() for tag in self.hashtags_input.text().split(',') if tag.strip()]
                mentions = [mention.strip() for mention in self.mentions_input.text().split(',') if mention.strip()]
                
                result = self.manager.post_to_all_platforms(
                    text=text,
                    hashtags=hashtags,
                    mentions=mentions
                )
                
                self.message_queue.put({'text': f'Posted to all platforms!', 'tab': 'posting'})
                self.message_queue.put({'text': f'Results: {json.dumps(result, indent=2)}', 'tab': 'posting'})
                self.update_status("Post to all platforms completed")
                
            except Exception as e:
                self.message_queue.put({'text': f'Error posting to all platforms: {str(e)}', 'tab': 'posting'})
                self.update_status("Post to all platforms failed")
        
        threading.Thread(target=post_thread, daemon=True).start()
        
    def clear_posting_form(self):
        """Clear the posting form."""
        self.post_text.clear()
        self.hashtags_input.clear()
        self.mentions_input.clear()
        
    def update_status(self, message: str):
        """Update the status bar."""
        self.status_bar.setText(message)
        
    def closeEvent(self, event):
        """Handle application close."""
        self.manager.cleanup()
        event.accept()

def main():
    """Main function."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced Social Media Automation System")
    app.setApplicationVersion("2.0.0")
    
    # Create and show the main window
    window = EnhancedSocialMediaGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 