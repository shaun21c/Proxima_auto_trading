import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('My First Application')
        self.resize(800, 600)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())