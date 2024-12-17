import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class MyWindow(QMainWindow):
    """로그인 창을 띄우는 클래스"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Login Form')
        self.resize(800, 600)
        btn1 = QPushButton("Login", self)
        btn1.move(30, 20)
        btn1.clicked.connect(self.btn1_clicked)

        btn2 = QPushButton("Check state", self)
        btn2.move(30, 70)
        btn2.resize(150, 30)
        btn2.clicked.connect(self.btn2_clicked)
        
        # 아래의 Kiwoom API 객체를 통해서 앞으로 모든 작업을 처리할 것이므로, MyWindow 클래스의 멤버 변수로 선언
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_event_loop = QEventLoop() 
        self.kiwoom.OnEventConnect.connect(self._event_connect)

    def btn1_clicked(self):
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그인 실패!")
        self.login_event_loop.exit()

    def btn2_clicked(self):
        if self.kiwoom.dynamicCall("GetConnectState()") == 0:
            self.statusBar().showMessage("Not connected")
        else:
            self.statusBar().showMessage("Connected")

# 이 코드를 실행하면, 로그인 창이 뜨고, 로그인 버튼을 누르면 콘솔에 "로그인 성공!"이 출력된다.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())