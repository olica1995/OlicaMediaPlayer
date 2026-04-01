import sys
import os
import vlc
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QSlider, QListWidget, QLabel, QFrame, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap

class OLICAPlayer(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- BRANDING ---
        self.setWindowTitle("OLICA MUSIC PLAYER")
        
        # Load the custom PNG as the window icon
        # Ensure 'olica_logo.png' exists next to this script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.script_dir, 'olica_logo.png')
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
        
        self.setGeometry(100, 100, 1000, 700) 
        
        # Initialize VLC
        self.instance = vlc.Instance('--quiet') 
        self.player = self.instance.media_player_new()
        
        self.init_ui()
        
        # Timer setup
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_seeker)
        self.timer.start()

    def init_ui(self):
        # 1. Refined Dark Theme Palette
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            #Sidebar {
                background-color: #181818;
                border-right: 1px solid #2A2A2A;
            }
            QPushButton {
                background-color: #1E1E1E;
                border: 1px solid #2A2A2A;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2D2D2D;
            }
            QPushButton#AddBtn {
                background-color: #E67E22; /* OLICA Orange */
                color: black;
                font-weight: bold;
            }
            QPushButton#AddBtn:hover {
                background-color: #D35400;
            }
            QListWidget {
                background-color: #1A1A1A;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #E67E22;
                color: black;
            }
        """)

        # Main Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 2. SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Brand Header (Optional: display the logo in sidebar)
        if os.path.exists(self.icon_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(self.icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sidebar_layout.addWidget(logo_label)

        lib_label = QLabel("OLICA LIBRARY")
        lib_label.setStyleSheet("color: #7A7A7A; font-weight: bold; font-size: 11px; padding: 10px 0 5px 10px;")
        
        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self.play_selected_item)
        
        # Modern Add Button
        btn_add = QPushButton("+ Add Media Files")
        btn_add.setObjectName("AddBtn")
        btn_add.clicked.connect(self.add_file)
        
        sidebar_layout.addWidget(lib_label)
        sidebar_layout.addWidget(self.playlist)
        sidebar_layout.addWidget(btn_add)
        
        # 3. RIGHT PANEL
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        
        # Video Display
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000; border-bottom: 1px solid #2A2A2A;")
        
        # Control Bar
        controls = QHBoxLayout()
        controls.setContentsMargins(20, 10, 20, 10)
        
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.play_pause)
        
        # Simplified Seek Slider
        self.seeker = QSlider(Qt.Orientation.Horizontal)
        self.seeker.setRange(0, 1000)
        self.seeker.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #3A3A3A; height: 6px; background: #1A1A1A; border-radius: 3px; }
            QSlider::handle:horizontal { background: #E67E22; border: 1px solid #D35400; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        """)
        self.seeker.sliderMoved.connect(self.set_position)
        
        controls.addWidget(self.btn_play)
        controls.addWidget(self.seeker, stretch=1)
        
        right_panel.addWidget(self.video_frame, stretch=1)
        right_panel.addLayout(controls)

        main_layout.addWidget(sidebar)
        main_layout.addLayout(right_panel, stretch=1)

        # Connect window to VLC
        self.attach_vlc_events()

    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Media", "", "Media Files (*.mp3 *.mp4 *.mkv *.avi *.wav)")
        if file_path:
            self.playlist.addItem(file_path)

    def play_selected_item(self, item):
        file_path = item.text()
        media = self.instance.media_new(file_path)
        self.player.set_media(media)
        self.player.play()
        self.btn_play.setText("Pause")

    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.setText("Play")
        else:
            self.player.play()
            self.btn_play.setText("Pause")

    def update_seeker(self):
        if self.player.is_playing():
            pos = self.player.get_position()
            self.seeker.setValue(int(pos * 1000))

    def set_position(self, position):
        self.player.set_position(position / 1000.0)

    def attach_vlc_events(self):
        if sys.platform.startswith('linux'):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winId())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = OLICAPlayer()
    player.show()
    sys.exit(app.exec())
