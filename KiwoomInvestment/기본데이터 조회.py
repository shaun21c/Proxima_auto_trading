import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.Qtcore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

        self.setWindowTitle("계좌정보")
        self.setGeeometry(300, 300, 300, 150)

        btn1 = QPushButton("계좌 얻기", self)
        btn1.move(190, 20)
        btn1.clicked.connect(self.btn1_clicked)

    def btn1_clicked(self):
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(Qstring)", ["ACCNO"].restrip(';')))
        print(f"계좌번호: {account_nums}")

    def event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그린 실패!")
        self.login_event_loop.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())