from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

class CustomSplashScreen(QSplashScreen):
    def __init__(self):
        # Criar pixmap vazio do tamanho desejado
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.white)
        super().__init__(pixmap)
        
        # Layout para organizar os elementos
        layout = QVBoxLayout()
        
        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        
        # Widget container para o layout
        widget = QWidget(self)
        layout.addWidget(self.progress)
        widget.setLayout(layout)
        
        # Centralizar widget na splash screen
        widget.setGeometry(10, 150, 380, 30)
        
        # Configurar mensagem inicial
        self.setStyleSheet("background-color: white;")
        self.showMessage("Carregando aplicação...", Qt.AlignCenter | Qt.AlignBottom, Qt.black)
        
    def update_progress(self, value, message=None):
        self.progress.setValue(value)
        if message:
            self.showMessage(message, Qt.AlignCenter | Qt.AlignBottom, Qt.black)
