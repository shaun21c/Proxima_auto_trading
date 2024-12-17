import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.login_event_loop = QEventLoop()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

        self.setWindowTitle("계좌정보")
        self.setGeometry(300, 300, 300, 150)

        btn1 = QPushButton("계좌 얻기", self)
        btn1.move(190, 20)
        btn1.clicked.connect(self.btn1_clicked)

    def btn1_clicked(self):
        # account_nums에 계좌번호를 키움객체의 GetLoginInfo 메서드를 통해 받아온다. ACCNO는 계좌번호를 의미
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(Qstring)", ["ACCNO"]).rstrip(';'))
        print(self.kiwoom.dynamicCall("GetLoginInfo(Qstring)", ["USER_NAME"]))
        print(f"계좌번호: {account_nums}")

    def event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그인 실패!")
        self.login_event_loop.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())