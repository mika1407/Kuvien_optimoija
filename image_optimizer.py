import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel,
                             QSlider, QHBoxLayout, QGroupBox, QLineEdit, QComboBox, QTextEdit,
                             QSpinBox, QCheckBox, QSizePolicy, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PIL import Image

class ImageProcessor(QThread):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    
    def __init__(self, image_paths, settings):
        super().__init__()
        self.image_paths = image_paths
        self.settings = settings
        self.total_saved_bytes = 0

    def run(self):
        total_images = len(self.image_paths)
        output_folder = self.settings['output_folder']
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for i, path in enumerate(self.image_paths):
            original_size = 0
            
            # Ohita kansiot
            if os.path.isdir(path):
                continue
                
            try:
                original_size = os.path.getsize(path)

                with Image.open(path) as img:
                    # Resoluution muutos
                    if self.settings['resize_mode'] == 'percentage':
                        new_width = int(img.width * (self.settings['resolution_value'] / 100))
                        new_height = int(img.height * (self.settings['resolution_value'] / 100))
                        
                    elif self.settings['resize_mode'] == 'pixels':
                        new_width = self.settings['resolution_value']
                        # Säilytetään kuvasuhde
                        new_height = int(img.height * (new_width / img.width))

                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Korjattu ongelma: muuta väritila RGB-muotoon, jos kohdemuoto on JPEG
                    output_format = self.settings['output_format'].lower()
                    if output_format in ['jpeg', 'jpg'] and img.mode in ('RGBA', 'P'):
                        self.log_message.emit(f"Muutetaan kuva '{os.path.basename(path)}' RGB-tilaan (poistetaan läpinäkyvyys).")
                        img = img.convert('RGB')
                    
                    # Määritä uusi tiedostopolku ja formaatti
                    filename_without_ext = os.path.splitext(os.path.basename(path))[0]
                    
                    new_filename_prefix = self.settings['new_filename_prefix']
                    
                    if new_filename_prefix:
                        new_filename = f"{new_filename_prefix}.{output_format}"
                    else:
                        new_filename = f"{filename_without_ext}_opt.{output_format}"

                    output_path = os.path.join(output_folder, new_filename)

                    # Tallenna kuva
                    if output_format in ['jpeg', 'jpg']:
                        img.save(output_path, quality=self.settings['quality'], optimize=True)
                    else:
                        img.save(output_path, optimize=True)
                        
                    optimized_size = os.path.getsize(output_path)
                    size_difference = original_size - optimized_size
                    self.total_saved_bytes += size_difference
                    
                    original_size_kb = original_size / 1024
                    optimized_size_kb = optimized_size / 1024
                    size_saved_kb = size_difference / 1024
                    
                    self.log_message.emit(
                        f"✅ Käsitelty: {os.path.basename(path)}\n"
                        f"  -> Alkuperäinen: {original_size_kb:.2f} KB | Optimoitu: {optimized_size_kb:.2f} KB | Säästö: {size_saved_kb:.2f} KB"
                    )

            except Exception as e:
                self.log_message.emit(f"❌ VIRHE: Tiedoston '{os.path.basename(path)}' käsittelyssä - {e}")
            
            progress = int((i + 1) / total_images * 100)
            self.progress_updated.emit(progress)
        
        total_saved_mb = self.total_saved_bytes / (1024 * 1024)
        self.log_message.emit(f"\n🎉 Optimointi valmis! Kokonaissäästö: {total_saved_mb:.2f} MB")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.initUI()
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-family: Arial;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                background-color: #3f72af;
                color: #fff;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #558fc9;
            }
            QGroupBox {
                border: 1px solid #555;
                margin-top: 10px;
                border-radius: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                background-color: #2b2b2b;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #3c3c3c;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #3f72af;
                border: 1px solid #3f72af;
                width: 18px;
                margin: -5px 0;
                border-radius: 3px;
            }
            QProgressBar {
                text-align: center;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #3f72af;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)

    def initUI(self):
        self.setWindowTitle('Kuvien Optimointi')
        self.setGeometry(100, 100, 700, 600)
        
        main_layout = QVBoxLayout(self)

        # Pudotusalue
        self.drop_label = QLabel('Pudota kuvat tähän')
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed #555; padding: 50px; font-size: 16px; background-color: #3c3c3c;")
        self.drop_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.drop_label)

        # Uudet painikkeet
        button_layout = QHBoxLayout()
        self.add_images_button = QPushButton('Lisää kuvia...')
        self.clear_list_button = QPushButton('Tyhjennä lista')
        
        self.add_images_button.clicked.connect(self.add_images_dialog)
        self.clear_list_button.clicked.connect(self.clear_image_list)
        
        button_layout.addWidget(self.add_images_button)
        button_layout.addWidget(self.clear_list_button)
        main_layout.addLayout(button_layout)

        # Asetusryhmä
        settings_group = QGroupBox('Optimointiasetukset')
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        # Resoluutio
        res_layout = QHBoxLayout()
        res_label = QLabel('Resoluutio:')
        self.res_slider = QSlider(Qt.Horizontal)
        self.res_slider.setRange(10, 100)
        self.res_slider.setValue(75)
        self.res_spinbox = QSpinBox()
        self.res_spinbox.setRange(10, 100)
        self.res_spinbox.setValue(75)
        self.res_slider.valueChanged.connect(self.res_spinbox.setValue)
        self.res_spinbox.valueChanged.connect(self.res_slider.setValue)
        self.res_mode_combo = QComboBox()
        self.res_mode_combo.addItems(['% (prosentti)', 'px (pikselit)'])
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_slider)
        res_layout.addWidget(self.res_spinbox)
        res_layout.addWidget(self.res_mode_combo)
        settings_layout.addLayout(res_layout)

        # Laatu
        quality_layout = QHBoxLayout()
        quality_label = QLabel('Laatu (JPEG):')
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(85)
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(10, 100)
        self.quality_spinbox.setValue(85)
        self.quality_slider.valueChanged.connect(self.quality_spinbox.setValue)
        self.quality_spinbox.valueChanged.connect(self.quality_slider.setValue)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_spinbox)
        settings_layout.addLayout(quality_layout)

        # Tiedostomuoto
        format_layout = QHBoxLayout()
        format_label = QLabel('Tiedostomuoto:')
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPEG', 'PNG'])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)
        
        # Tiedostonimi
        filename_layout = QHBoxLayout()
        filename_label = QLabel('Uusi tiedostonimi:')
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText('Esim. "optimoitu"')
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        settings_layout.addLayout(filename_layout)

        main_layout.addWidget(settings_group)
        
        # Käynnistyspainike
        self.start_button = QPushButton('Aloita optimointi')
        self.start_button.clicked.connect(self.start_processing)
        main_layout.addWidget(self.start_button)
        
        # Etenemispalkki
        self.progress_bar = QProgressBar(self)
        main_layout.addWidget(self.progress_bar)

        # Loki
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText('Tässä näet optimoinnin tilan ja mahdolliset virheet.')
        main_layout.addWidget(self.log_box)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.drop_label.setStyleSheet("border: 2px dashed #3f72af; padding: 50px; font-size: 16px; background-color: #3c3c3c;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("border: 2px dashed #555; padding: 50px; font-size: 16px; background-color: #3c3c3c;")

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        self.image_paths.extend([url.toLocalFile() for url in urls])
        self.update_drop_label()
        self.drop_label.setStyleSheet("border: 2px dashed #555; padding: 50px; font-size: 16px; background-color: #3c3c3c;")

    def add_images_dialog(self):
        # Avaa tiedostonvalintaikkuna, josta voi valita useita kuvia
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "Lisää kuvia",
            os.path.expanduser("~"),
            "Kuvatiedostot (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_paths:
            self.image_paths.extend(file_paths)
            self.update_drop_label()

    def clear_image_list(self):
        self.image_paths = []
        self.update_drop_label()
        self.log_box.append("Kuvalista tyhjennetty.")

    def update_drop_label(self):
        if self.image_paths:
            self.drop_label.setText(f"Lisätty {len(self.image_paths)} kuvaa")
        else:
            self.drop_label.setText('Pudota kuvat tähän')
    
    def start_processing(self):
        if not self.image_paths:
            self.log_box.append("Lisää kuvia pudottamalla ne tai käyttämällä 'Lisää kuvia...'-painiketta.")
            return

        self.log_box.clear()
        
        # Kerää asetukset käyttöliittymästä
        settings = {
            'output_folder': 'optimoidut_kuvat',
            'quality': self.quality_spinbox.value(),
            'output_format': self.format_combo.currentText(),
            'new_filename_prefix': self.filename_input.text(),
            'resize_mode': 'percentage' if self.res_mode_combo.currentIndex() == 0 else 'pixels',
            'resolution_value': self.res_spinbox.value(),
        }

        # Käynnistetään uusi säie
        self.processor_thread = ImageProcessor(self.image_paths, settings)
        self.processor_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processor_thread.log_message.connect(self.log_box.append)
        self.processor_thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())