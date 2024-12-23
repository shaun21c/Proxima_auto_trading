# CommRqData("RQName", "TRCode", 0, "ScreenNo")
# RQName: 사용자 구분명으로 사용자가 직접 정의하는 요청의 이름
# TRCode: 요청하는 TR의 코드
# 0: 조회(0), 연속(2)
# ScreenNo: 화면번호

class KiwoomBasicPrice:
    def __init__(self, kiwoom):
        self.kiwoom = kiwoom
        self.screen_no_counter = 1000
    
    def get_screen_no(self):
        self.screen_no_counter += 1
        return str(self.screen_no_counter)

    def request_opt10001_stock_basic_info(self, code):
        """
            주식기본정보요청하는 메서드
            input: code(str) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", 0, screen_no)

    def request_opt10003_stock_trade_info(self, code):
        """
            주식 체결정보요청하는 메서드
            input: code(str) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "체결정보요청", "opt10003", 0, screen_no)

