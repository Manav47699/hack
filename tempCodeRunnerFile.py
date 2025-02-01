import sys
from PyQt5.QtGui import QGuiApplication, QFontDatabase, QFont, QIcon, QImage, QPixmap, QTransform
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QWidget, QFileDialog, QProgressBar, QMessageBox, QScrollArea, QCheckBox, QMenu
)
from PyQt5.QtCore import Qt, QTimer
import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
import numpy as np
import tensorflow as tf
import pickle

# Disable oneDNN optimization warning
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

class MainWindow(QMainWindow):
    def __init__(self, username=None):
        super().__init__()
        self.username = username  # stores username
        self.initUI()

        # Variables for the model and file paths
        self.model = None
        self.train_data_dir = None
        self.num_images = 0  # Store the number of images used for training
        self.current_image = None  # Store the current image for manipulation
        self.dark_mode = False  # Track dark mode state
        self.class_labels = []  # Store class labels

        # Load pre-trained model and class labels if they exist
        self.loadPreTrainedModel()

    def initUI(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen.x(), screen.y(), screen.width(), screen.height())
        self.setWindowTitle("AI Image Editor")

        # Load custom font
        QFontDatabase.addApplicationFont(r"D:\HACKATHON real\Roboto-Bold.ttf")  # Replace with your font path
        self.custom_font = QFont("Roboto", 12)

        # Set light background for the main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                border: 2px solid #4CAF50;
                margin: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #45a049, stop:1 #4CAF50);
                border: 2px solid #45a049;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #387038, stop:1 #4CAF50);
                border: 2px solid #387038;
            }
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.8);
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
            QCheckBox {
                font-size: 14px;
                margin: 5px;
            }
        """)

        # Create main vertical layout
        main_layout = QVBoxLayout()

        # Create a horizontal layout for the top buttons
        top_buttons_layout = QHBoxLayout()

        if self.username:
            welcome_label = QLabel(f"Welcome, {self.username} (स्वागत छ, {self.username})", self)
            welcome_label.setObjectName("welcome_label")  # Set object name for styling
            welcome_label.setStyleSheet("""
                QLabel#welcome_label {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6F61, stop:1 #6B5B95);
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #4CAF50;
                }
                QLabel#welcome_label:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF8C61, stop:1 #8B5B95);
                }
            """)
            welcome_label.setFont(self.custom_font)
            welcome_label.setAlignment(Qt.AlignCenter)
            
            # Add the welcome label to the top buttons layout
            top_buttons_layout.addWidget(welcome_label)

        # Create buttons for AI functionality
        self.upload_train = QPushButton("Upload Training Images (प्रशिक्षण तस्वीरहरू अपलोड गर्नुहोस्)", self)
        self.upload_predict = QPushButton("Upload Prediction Image (पूर्वानुमान तस्वीर अपलोड गर्नुहोस्)", self)
        self.ask_ai = QPushButton("Ask AI (AI सोध्नुहोस्)", self)
        self.ask_ai.setIcon(QIcon(r"D:\HACKATHON real\ai_icon.png"))  # Replace with your icon path
        self.ask_ai.setFixedHeight(80)  # Increased height for the "Ask AI" button

        # Apply styling for buttons
        self.style_button(self.upload_train)
        self.style_button(self.upload_predict)
        self.style_button(self.ask_ai)

        # Add the top buttons to the horizontal layout
        top_buttons_layout.addWidget(self.upload_train)
        top_buttons_layout.addWidget(self.upload_predict)
        top_buttons_layout.addWidget(self.ask_ai)

        # Add a dropdown menu (triple horizontal line) below the "Ask AI" button
        self.menu_button = QPushButton("☰", self)  # Unicode for triple horizontal lines
        self.menu_button.setFixedSize(80, 40)  # Set a fixed size for the button
        self.menu_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 20px;
                padding: 5px;
                border-radius: 5px;
                border: 2px solid #4CAF50;
                margin: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #45a049, stop:1 #4CAF50);
                border: 2px solid #45a049;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #387038, stop:1 #4CAF50);
                border: 2px solid #387038;
            }
        """)

        # Create a menu for the dropdown
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

        # Add "About Us" action to the menu
        about_us_action = self.menu.addAction("About Us (हाम्रो बारेमा)")
        about_us_action.triggered.connect(self.openAboutUs)

        # Add the menu to the button
        self.menu_button.setMenu(self.menu)

        # Add the menu button to the top buttons layout
        top_buttons_layout.addWidget(self.menu_button)

        # Add the top buttons layout to the main layout
        main_layout.addLayout(top_buttons_layout)

        # Add a "Connect with Us" section below the dropdown menu
        connect_label = QLabel("Connect with Us (हामीलाई जोड्नुहोस्):", self)
        connect_label.setObjectName("connect_label")  # Set object name for styling
        connect_label.setStyleSheet("""
            QLabel#connect_label {
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                color: #333333;
                background-color: gold;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #FFD700;
            }
            QLabel#connect_label:hover {
                background-color: #FFD700;
                border: 2px solid #FFD700;
                color: white;
            }
        """)
        connect_label.setFont(self.custom_font)
        main_layout.addWidget(connect_label)

        # Add social media links
        social_media_links = QLabel("""
            <a href="https://www.facebook.com/profile.php?id=100072706513262" style="color: #4CAF50; text-decoration: none;">Facebook</a> | 
            <a href="https://www.youtube.com" style="color: #4CAF50; text-decoration: none;">YouTube</a> | 
            <a href="https://www.tiktok.com/@tirthangkarkhatiw?_t=ZS-8tXdPseDvXN&_r=1" style="color: #4CAF50; text-decoration: none;">TikTok</a> | 
            <a href="https://x.com/dhakalbijay768?t=zoq4BJqQZcLQJqyz47ppAw&s=07&mx=2" style="color: #4CAF50; text-decoration: none;">Twitter</a> | 
            <a href="https://www.instagram.com/manav.ar/" style="color: #4CAF50; text-decoration: none;">Instagram</a>
        """)
        social_media_links.setOpenExternalLinks(True)  # Open links in the default browser
        social_media_links.setStyleSheet("""
            QLabel {
                font-size: 14px;
                margin-top: 5px;
            }
        """)
        social_media_links.setFont(self.custom_font)
        main_layout.addWidget(social_media_links)

        # Add a toggle button for dark mode and the new button for pre-trained images
        toggle_layout = QHBoxLayout()
        self.dark_mode_toggle = QCheckBox("Toggle Dark Mode (डार्क मोड सक्रिय गर्नुहोस्)", self)
        self.dark_mode_toggle.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                margin: 5px;
            }
        """)
        self.dark_mode_toggle.stateChanged.connect(self.toggleDarkMode)
        toggle_layout.addWidget(self.dark_mode_toggle, alignment=Qt.AlignLeft)

        self.upload_pre_trained = QPushButton("Upload Pre-trained Images (पूर्व-प्रशिक्षित तस्वीरहरू अपलोड गर्नुहोस्)", self)
        self.style_button(self.upload_pre_trained)
        self.upload_pre_trained.clicked.connect(self.uploadPreTrainedImages)
        toggle_layout.addWidget(self.upload_pre_trained, alignment=Qt.AlignLeft)

        self.delete_model_button = QPushButton("Delete Model (मोडेल मेटाउनुहोस्)", self)
        self.style_button(self.delete_model_button)
        self.delete_model_button.clicked.connect(self.deleteModel)
        toggle_layout.addWidget(self.delete_model_button, alignment=Qt.AlignLeft)

        # Add FAQ button
        self.faq_button = QPushButton("Proceed further with our bot (प्रश्नोत्तर)", self)
        self.style_button(self.faq_button)
        self.faq_button.clicked.connect(self.openFAQ)
        toggle_layout.addWidget(self.faq_button, alignment=Qt.AlignLeft)

        toggle_layout.addStretch()  # Push the toggle button to the left
        main_layout.addLayout(toggle_layout)

        # Create and center the image label
        self.image_label = QLabel("Your selected image will appear here. (तपाईंले छान्नुभएको तस्वीर यहाँ देखिनेछ।)", self)
        self.image_label.setObjectName("image_label")  # Set object name for styling
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel#image_label {
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding: 10px;
                background-color: rgba(255, 255, 255, 0.8);
                color: #333333;
            }
        """)
        self.image_label.setFont(self.custom_font)

        # Add the image label to a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        main_layout.addWidget(scroll_area, stretch=1)

        # Create a progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setVisible(False)  # Hide by default
        main_layout.addWidget(self.progress_bar)

        # Add a label for invasive species detection
        self.invasive_species_label = QLabel("Invasive species detected", self)
        self.invasive_species_label.setObjectName("invasive_species_label")  # Set object name for styling
        self.invasive_species_label.setAlignment(Qt.AlignCenter)
        self.invasive_species_label.setStyleSheet("""
            QLabel#invasive_species_label {
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                color: #ff6666;
                background-color: #ffe6e6;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #ff6666;
            }
        """)
        self.invasive_species_label.setFont(self.custom_font)
        self.invasive_species_label.setVisible(False)  # Hide by default
        main_layout.addWidget(self.invasive_species_label)

        # Create a label for model predictions
        self.predictions_label = QLabel("Model's Predictions (मोडेलको पूर्वानुमानहरू)", self)
        self.predictions_label.setObjectName("predictions_label")  # Set object name for styling
        self.predictions_label.setAlignment(Qt.AlignCenter)
        self.predictions_label.setStyleSheet("""
            QLabel#predictions_label {
                font-size: 20px;
                font-weight: bold;
                margin-top: 10px;
                color: #333333;
            }
        """)
        self.predictions_label.setFont(self.custom_font)

        # Add the predictions label to a scroll area
        predictions_scroll_area = QScrollArea(self)
        predictions_scroll_area.setWidgetResizable(True)
        predictions_scroll_area.setWidget(self.predictions_label)
        main_layout.addWidget(predictions_scroll_area, stretch=1)

        # Add a label for image manipulation buttons
        manipulate_label = QLabel("Manipulate Image (तस्वीर सम्पादन गर्नुहोस्)", self)
        manipulate_label.setObjectName("manipulate_label")  # Set object name for styling
        manipulate_label.setAlignment(Qt.AlignCenter)
        manipulate_label.setStyleSheet("""
            QLabel#manipulate_label {
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                color: #333333;
            }
        """)
        manipulate_label.setFont(self.custom_font)
        main_layout.addWidget(manipulate_label)

        # Create basic image manipulation buttons
        self.left = QPushButton("Rotate Left (बायाँ घुमाउनुहोस्)", self)
        self.right = QPushButton("Rotate Right (दायाँ घुमाउनुहोस्)", self)
        self.mirror = QPushButton("Mirror (मिरर गर्नुहोस्)", self)
        self.clear = QPushButton("Clear Image (तस्वीर खाली गर्नुहोस्)", self)
        self.save = QPushButton("Save Image (तस्वीर बचत गर्नुहोस्)", self)

        # Apply styling for buttons
        self.style_button(self.left)
        self.style_button(self.right)
        self.style_button(self.mirror)
        self.style_button(self.clear)
        self.style_button(self.save)

        # Create a horizontal layout for the image manipulation buttons
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addWidget(self.left)
        image_buttons_layout.addWidget(self.right)
        image_buttons_layout.addWidget(self.mirror)
        image_buttons_layout.addWidget(self.clear)
        image_buttons_layout.addWidget(self.save)

        # Add the image buttons layout to the main layout
        main_layout.addLayout(image_buttons_layout)

        # Add "Predict Now" and "Help" buttons
        bottom_buttons_layout = QHBoxLayout()
        self.predict_now_button = QPushButton("Predict Now (अहिले पूर्वानुमान गर्नुहोस्)", self)
        self.style_button(self.predict_now_button)
        self.predict_now_button.clicked.connect(self.predictCurrentImage)
        bottom_buttons_layout.addWidget(self.predict_now_button)

        self.help_button = QPushButton("Help (मद्दत)", self)
        self.style_button(self.help_button)
        self.help_button.clicked.connect(self.showHelp)
        bottom_buttons_layout.addWidget(self.help_button)

        main_layout.addLayout(bottom_buttons_layout)

        # Set the layout to the central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(main_layout)

        # Connect buttons to backend functionality
        self.upload_train.clicked.connect(self.selectTrainFolder)
        self.upload_predict.clicked.connect(self.uploadTestImage)
        self.left.clicked.connect(self.rotateLeft)
        self.right.clicked.connect(self.rotateRight)
        self.mirror.clicked.connect(self.mirrorImage)
        self.clear.clicked.connect(self.clearImage)
        self.save.clicked.connect(self.saveImage)

    def style_button(self, button):
        button.setFont(self.custom_font)

    def toggleDarkMode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                QLabel#welcome_label {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6F61, stop:1 #6B5B95);
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #4CAF50;
                }
                QLabel#welcome_label:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF8C61, stop:1 #8B5B95);
                }
                QMainWindow {
                    background-color: #333333;
                }
                QLabel {
                    color: #ffffff;
                }
                QLabel#image_label {
                    border: 2px solid #777777;
                    border-radius: 10px;
                    padding: 10px;
                    background-color: rgba(51, 51, 51, 0.8);
                    color: #ffffff;
                }
                QLabel#predictions_label {
                    font-size: 20px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #ffffff;
                }
                QLabel#manipulate_label {
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #ffffff;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #555555, stop:1 #666666);
                    color: white;
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid #555555;
                    margin: 5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #666666, stop:1 #555555);
                    border: 2px solid #666666;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #444444, stop:1 #555555);
                    border: 2px solid #444444;
                }
                QProgressBar {
                    border: 2px solid #777777;
                    border-radius: 5px;
                    text-align: center;
                    background-color: rgba(255, 255, 255, 0.2);
                }
                QProgressBar::chunk {
                    background-color: #555555;
                    width: 10px;
                }
                QCheckBox {
                    font-size: 14px;
                    margin: 5px;
                    color: #ffffff;
                }
                QLabel#connect_label {
                    font-size: 16px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #333333;
                    background-color: gold;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #FFD700;
                }
                QLabel#connect_label:hover {
                    background-color: #FFD700;
                    border: 2px solid #FFD700;
                    color: white;
                }
                QLabel#invasive_species_label {
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #ff6666;
                    background-color: #ffe6e6;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #ff6666;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel#welcome_label {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6F61, stop:1 #6B5B95);
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #4CAF50;
                }
                QLabel#welcome_label:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF8C61, stop:1 #8B5B95);
                }
                QMainWindow {
                    background-color: #f0f0f0;
                }
                QLabel {
                    color: #333333;
                }
                QLabel#image_label {
                    border: 2px solid #cccccc;
                    border-radius: 10px;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 0.8);
                    color: #333333;
                }
                QLabel#predictions_label {
                    font-size: 20px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #333333;
                }
                QLabel#manipulate_label {
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #333333;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049);
                    color: white;
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 10px;
                    border: 10px solid #4CAF50;
                    margin: 5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #45a049, stop:1 #4CAF50);
                    border: 2px solid #45a049;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #387038, stop:1 #4CAF50);
                    border: 2px solid #387038;
                }
                QProgressBar {
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: rgba(255, 255, 255, 0.8);
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    width: 10px;
                }
                QCheckBox {
                    font-size: 14px;
                    margin: 5px;
                }
                QLabel#connect_label {
                    font-size: 16px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #333333;
                    background-color: gold;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #FFD700;
                }
                QLabel#connect_label:hover {
                    background-color: #FFD700;
                    border: 2px solid #FFD700;
                    color: white;
                }
                QLabel#invasive_species_label {
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 10px;
                    color: #ff6666;
                    background-color: #ffe6e6;
                    padding: 10px;
                    border-radius: 10px;
                    border: 2px solid #ff6666;
                }
            """)

    def selectTrainFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder for Training (प्रशिक्षणका लागि फोल्डर छान्नुहोस्)')
        if folder_path:
            self.train_data_dir = folder_path
            self.trainModel(folder_path)

    def trainModel(self, folder_path):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Simulate smooth progress update
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.updateProgress(1))  # Increment by 1% every 50ms
        self.timer.start(50)

        datagen = ImageDataGenerator(rescale=1.0/255.0)
        train_generator = datagen.flow_from_directory(
            folder_path,
            target_size=(150, 150),
            batch_size=32,
            class_mode='categorical'
        )

        self.num_images = train_generator.samples
        if self.num_images == 0:
            self.image_label.setText('No images found in the selected folder. (चयन गरिएको फोल्डरमा कुनै तस्वीर भेटिएन।)')
            self.progress_bar.setVisible(False)
            return

        print(f"Total images used for training: {self.num_images}")

        self.model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(train_generator.num_classes, activation='softmax')
        ])

        self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        history = self.model.fit(train_generator, epochs=5)

        self.timer.stop()
        self.progress_bar.setVisible(False)

        for epoch in range(5):
            print(f"Epoch {epoch+1}: Loss = {history.history['loss'][epoch]:.4f}, Accuracy = {history.history['accuracy'][epoch]*100:.2f}%")

        self.model.save('trained_model.h5')
        self.class_labels = list(os.listdir(folder_path))
        with open('class_labels.pkl', 'wb') as f:
            pickle.dump(self.class_labels, f)
        self.image_label.setText(f'Model trained with {self.num_images} images! Now upload an image for prediction. (मोडेल {self.num_images} तस्वीरहरूसँग प्रशिक्षित गरियो! अब पूर्वानुमानका लागि तस्वीर अपलोड गर्नुहोस्।)')

    def updateProgress(self, value):
        if self.progress_bar.value() < 100:
            self.progress_bar.setValue(self.progress_bar.value() + value)
        else:
            self.timer.stop()

    def uploadTestImage(self):
        image_path, _ = QFileDialog.getOpenFileName(self, 'Select Image for Prediction (पूर्वानुमानका लागि तस्वीर छान्नुहोस्)', '', 'Images (*.png *.jpg *.bmp)')
        if image_path:
            print(f"Uploaded image: {image_path}")
            self.current_image = QImage(image_path)
            self.displayImage(self.current_image)
            self.predictImage(image_path)

    def displayImage(self, image):
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def rotateLeft(self):
        if self.current_image:
            transform = QTransform().rotate(-90)
            self.current_image = self.current_image.transformed(transform)
            self.displayImage(self.current_image)

    def rotateRight(self):
        if self.current_image:
            transform = QTransform().rotate(90)
            self.current_image = self.current_image.transformed(transform)
            self.displayImage(self.current_image)

    def mirrorImage(self):
        if self.current_image:
            self.current_image = self.current_image.mirrored(True, False)
            self.displayImage(self.current_image)

    def clearImage(self):
        self.current_image = None
        self.image_label.setText("Your selected image will appear here. (तपाईंले छान्नुभएको तस्वीर यहाँ देखिनेछ।)")
        self.predictions_label.setText("Model's Predictions (मोडेलको पूर्वानुमानहरू)")
        self.invasive_species_label.setVisible(False)

    def saveImage(self):
        if self.current_image:
            file_path, _ = QFileDialog.getSaveFileName(self, 'Save Image (तस्वीर बचत गर्नुहोस्)', '', 'Images (*.png *.jpg *.bmp)')
            if file_path:
                self.current_image.save(file_path)
                QMessageBox.information(self, "Success (सफलता)", "Image saved successfully! (तस्वीर सफलतापूर्वक बचत गरियो!)")

    def predictImage(self, image_path):
        img = load_img(image_path, target_size=(150, 150))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        predictions = self.model.predict(img_array)
        predicted_class = np.argmax(predictions[0])

        predicted_label = self.class_labels[predicted_class]
        confidence = predictions[0][predicted_class] * 100

        result_text = f'<b>Prediction (पूर्वानुमान):</b> {predicted_label} ({confidence:.2f}% confidence)<br>'
        result_text += f'<b>Trained with (प्रशिक्षित गरिएको):</b> {self.num_images} images.<br><br>'
        result_text += '<b>Probabilities (सम्भाव्यताहरू):</b><br>'

        for i, label in enumerate(self.class_labels):
            probability = predictions[0][i] * 100
            result_text += f'{label}: {probability:.2f}%<br>'

        self.predictions_label.setText(result_text)

        # Show invasive species label if detected
        if predicted_label == "Invasive Species":
            self.invasive_species_label.setVisible(True)
        else:
            self.invasive_species_label.setVisible(False)

    def predictCurrentImage(self):
        if self.current_image:
            # Save the current image temporarily
            temp_image_path = "temp_image.jpg"
            self.current_image.save(temp_image_path)

            # Predict the temporary image
            self.predictImage(temp_image_path)

            # Delete the temporary image
            os.remove(temp_image_path)

    def showHelp(self):
        help_text = """
        <h2>Image Editor Help (तस्वीर सम्पादक मद्दत)</h2>
        <p><b>1. Upload Training Images (प्रशिक्षण तस्वीरहरू अपलोड गर्नुहोस्):</b> Select a folder containing images to train the AI model.</p>
        <p><b>2. Upload Prediction Image (पूर्वानुमान तस्वीर अपलोड गर्नुहोस्):</b> Select an image to predict its class using the trained model.</p>
        <p><b>3. Rotate Left/Right (बायाँ/दायाँ घुमाउनुहोस्):</b> Rotate the uploaded image 90 degrees left or right.</p>
        <p><b>4. Mirror (मिरर गर्नुहोस्):</b> Flip the uploaded image horizontally.</p>
        <p><b>5. Clear Image (तस्वीर खाली गर्नुहोस्):</b> Reset the displayed image.</p>
        <p><b>6. Save Image (तस्वीर बचत गर्नुहोस्):</b> Save the manipulated image to your computer.</p>
        <p><b>7. Progress Bar (प्रगति बार):</b> Shows the progress of model training.</p>
        """
        QMessageBox.information(self, "Help (मद्दत)", help_text)

    def uploadPreTrainedImages(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder for Pre-trained Images (पूर्व-प्रशिक्षित तस्वीरहरूका लागि फोल्डर छान्नुहोस्)')
        if folder_path:
            self.train_data_dir = folder_path
            self.trainModel(folder_path)

    
    def deleteModel(self):
        if os.path.exists('trained_model.h5'):
            os.remove('trained_model.h5')
        if os.path.exists('class_labels.pkl'):
            os.remove('class_labels.pkl')
        self.model = None
        self.class_labels = []
        self.image_label.setText("Model deleted. Upload new training images to train a new model. (मोडेल मेटाइयो। नयाँ प्रशिक्षण तस्वीरहरू अपलोड गरेर नयाँ मोडेल प्रशिक्षित गर्नुहोस्।)")
        self.predictions_label.setText("Model's Predictions (मोडेलको पूर्वानुमानहरू)")
        QMessageBox.information(self, "Success (सफलता)", "Model and associated files deleted successfully! (मोडेल र सम्बन्धित फाइलहरू सफलतापूर्वक मेटाइयो!)")

    def loadPreTrainedModel(self):
        if os.path.exists('trained_model.h5') and os.path.exists('class_labels.pkl'):
            self.model = tf.keras.models.load_model('trained_model.h5')
            with open('class_labels.pkl', 'rb') as f:
                self.class_labels = pickle.load(f)
            self.image_label.setText('Pre-trained model loaded. Now upload an image for prediction. (पूर्व-प्रशिक्षित मोडेल लोड गरियो। अब पूर्वानुमानका लागि तस्वीर अपलोड गर्नुहोस्।)')

    def openAboutUs(self):
        # Open the "aboutus.py" file
        try:
            os.system("python aboutus.py")  # Run the "aboutus.py" file
        except Exception as e:
            QMessageBox.critical(self, "Error (त्रुटि)", f"Could not open 'aboutus.py': {str(e)}")

    def openFAQ(self):
        # Open the "FAQ.py" file
        try:
            os.system("python FAQ.py")  # Run the "FAQ.py" file
        except Exception as e:
            QMessageBox.critical(self, "Error (त्रुटि)", f"Could not open 'FAQ.py': {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()