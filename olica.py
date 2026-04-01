import sys
import os
import vlc
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QSlider, QListWidget, QLabel, QFrame, 
                             QFileDialog, QComboBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from mutagen import File as MutagenFile
from io import BytesIO

class OLICAPlayer(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OLICA MUSIC PLAYER")
        
        # Enable Drag and Drop for the entire window
        self.setAcceptDrops(True)
        
        # Helper to find files inside a PyInstaller .exe
        def get_resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        # Load the icon from the bundled resources
        self.icon_path = get_resource_path('olica_logo.png')
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))
        
        self.setGeometry(100, 100, 1000, 700) 
        
        # Initialize VLC
        self.instance = vlc.Instance('--quiet') 
        self.player = self.instance.media_player_new()
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_seeker)
        self.timer.start()

    def init_ui(self):
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
            QPushButton, QComboBox {
                background-color: #1E1E1E;
                border: 1px solid #2A2A2A;
                padding: 8px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover, QComboBox:hover {
                background-color: #2D2D2D;
            }
            QPushButton#AddBtn {
                background-color: #E67E22;
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

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        
        if os.path.exists(self.icon_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(self.icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            sidebar_layout.addWidget(logo_label)

        lib_label = QLabel("OLICA LIBRARY")
        lib_label.setStyleSheet("color: #7A7A7A; font-weight: bold; font-size: 11px; padding: 10px 0 5px 10px;")
        
        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self.play_selected_item)
        
        btn_add = QPushButton("+ Add Media Files")
        btn_add.setObjectName("AddBtn")
        btn_add.clicked.connect(self.add_file)
        
        sidebar_layout.addWidget(lib_label)
        sidebar_layout.addWidget(self.playlist)
        sidebar_layout.addWidget(btn_add)
        
        # RIGHT PANEL
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        
        # Video/Album Art Frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000; border-bottom: 1px solid #2A2A2A;")
        
        # Center layout for displaying Album Art and Text
        self.center_layout = QVBoxLayout(self.video_frame)
        self.center_layout.setAlignment(Qt.AlignCenter)
        
        self.art_label = QLabel("Drop files here or use the sidebar to play!")
        self.art_label.setAlignment(Qt.AlignCenter)
        self.art_label.setStyleSheet("color: #7A7A7A; font-size: 16px;")
        
        self.track_info_label = QLabel("")
        self.track_info_label.setAlignment(Qt.AlignCenter)
        self.track_info_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        self.center_layout.addWidget(self.art_label)
        self.center_layout.addWidget(self.track_info_label)
        
        # CONTROLS
        controls = QHBoxLayout()
        controls.setContentsMargins(20, 10, 20, 10)
        
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.play_pause)
        
        # Speed Control Dropdown
        self.speed_box = QComboBox()
        self.speed_box.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_box.setCurrentText("1.0x")
        self.speed_box.currentTextChanged.connect(self.change_speed)
        
        self.seeker = QSlider(Qt.Horizontal)
        self.seeker.setRange(0, 1000)
        self.seeker.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #3A3A3A; height: 6px; background: #1A1A1A; border-radius: 3px; }
            QSlider::handle:horizontal { background: #E67E22; border: 1px solid #D35400; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
        """)
        self.seeker.sliderMoved.connect(self.set_position)
        
        controls.addWidget(self.btn_play)
        controls.addWidget(self.speed_box)
        controls.addWidget(self.seeker, 1)
        
        right_panel.addWidget(self.video_frame, 1)
        right_panel.addLayout(controls)

        main_layout.addWidget(sidebar)
        main_layout.addLayout(right_panel, 1)

        self.attach_vlc_events()

    # --- DRAG AND DROP HANDLERS ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = str(url.toLocalFile())
            if file_path.lower().endswith(('.mp3', '.mp4', '.mkv', '.avi', '.wav')):
                self.playlist.addItem(file_path)

    # --- CORE LOGIC ---
    def add_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Media", "", "Media Files (*.mp3 *.mp4 *.mkv *.avi *.wav)")
        if file_paths:
            self.playlist.addItems(file_paths)

    def play_selected_item(self, item):
        file_path = item.text()
        
        # Reset visual frame
        self.art_label.setText("Playing Video...")
        self.track_info_label.setText(os.path.basename(file_path))
        
        # Try to pull album art if it's an MP3
        if file_path.lower().endswith('.mp3'):
            self.load_metadata(file_path)

        media = self.instance.media_new(file_path)
        self.player.set_media(media)
        self.player.play()
        self.btn_play.setText("Pause")
        
        # Enforce current speed setting
        self.change_speed(self.speed_box.currentText())

    def load_metadata(self, file_path):
        try:
            audio = MutagenFile(file_path)
            title = audio.get('TIT2', [os.path.basename(file_path)])[0]
            artist = audio.get('TPE1', ['Unknown Artist'])[0]
            self.track_info_label.setText(f"{title}\n{artist}")

            # Extract Cover Art
            if 'APIC:' in audio:
                art_data = audio['APIC:'].data
                img = QPixmap()
                img.loadFromData(art_data)
                self.art_label.setPixmap(img.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.art_label.setText("No Album Art Found")
                self.art_label.setPixmap(QPixmap()) # Clear old pixmap
        except Exception:
            self.art_label.setText("Playing Audio...")

    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play.setText("Play")
        else:
            self.player.play()
            self.btn_play.setText("Pause")

    def change_speed(self, speed_text):
        speed_val = float(speed_text.replace('x', ''))
        self.player.set_rate(speed_val)

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
