import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.Qtcore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.login_event_loop = QEventLoop()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

        self.setWindowTitle("종목코드")
        self.setGeeometry(300, 300, 300, 150)

        btn1 = QPushButton("종목코드 얻기", self)
        btn1.move(190, 10)
        btn1.clicked.connect(self.btn1_clicked)

    def btn1_clicked(self):
        ret = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", ["0"])
        kospi_code_list = ret.split(';')
        for stock_code in kospi_code_list:
            name = self.kiwoom.dynamicCall("GetMasterCodeName(Qstring)", [stock_code])
            print(f"종목코드: {stock_code}, 종목명: {name}")


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