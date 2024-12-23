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

    def request_opt10001_주식기본정보요청(self, code, next=0):
        """
            주식기본정보요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", next, screen_no)

    def request_opt10003_체결정보요청(self, code, next=0):
        """
            주식 체결정보요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "체결정보요청", "opt10003", next, screen_no)

    def request_opt10004_주식호가요청(self, code, next=0):
        """
            주식호가요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식호가요청", "opt10004", next, screen_no)

    def request_opt10005_주식일주월시요청(self, code, next=0):
        """
            주식일주월시분요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일주월시분분요청", "opt10005", next, screen_no)

    def request_opt10006_주식시분요청(self, code, next=0):
        """
            주식시분요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식시시분요청", "opt10006", next, screen_no)

    def request_opt10007_시세표성정보(self, code, next=0):
        """
            시세표성정보요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "시세표성정보요청", "opt10007", next, screen_no)

    # def request_opt10012_주문체결요청(self, account_num, next=0):
    #     """
    #         주문체결요청하는 메서드
    #         input: account_num(str), next(int) -> output: None
    #     """
    #     screen_no = self.get_screen_no()
    #     self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_num)
    #     self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주문체결요청", "opt10012", next, screen_no)

    def request_opt10015_일별거래상세요청(self, code, date, next=0):
        """
            일별거래상세요청하는 메서드
            input: code(str), date(str), next(int) -> output: None
            date: YYYYMMDD
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "시작일자", date)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "일별거래상세요청", "opt10015", next, screen_no)

    def request_opt10079_주식틱차트조회요청(self, code, tick_unit, revise_stock_price, next=0):
        """
            주식틱차트조회요청하는 메서드
            input: code(str), tick_unit(str), revise_stock_price(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "틱범위", tick_unit)
        # 수정주가구분 = 0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식틱차트조회요청", "opt10079", next, screen_no)

    def request_opt10080_주식분봉차트조회요청(self, code, minute_unit, revise_stock_price, next=0):
        """
            주식분봉차트조회요청하는 메서드
            input: code(str), minute_unit(str), revise_stock_price(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "틱범위", minute_unit)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식분봉차트조회요청", "opt10080", next, screen_no)

    def request_opt10081_주식일봉차트조회요청(self, code, date, revise_stock_price, next=0):
        """
            주식일봉차트조회요청하는 메서드
            input: code(str), date(str), revise_stock_price(str), next(int) -> output: None
            date: YYYYMMDD
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회요청", "opt10081", next, screen_no)

    def request_opt10082_주식주봉차트조회요청(self, code, start_date, end_date, revise_stock_price, next=0):
        """
            주식주봉차트조회요청하는 메서드
            input: code(str), start_date(str), end_date(str), revise_stock_price(str), next(int) -> output: None
            start_date, end_date: YYYYMMDD
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", start_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "끝일자", end_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식주봉차트조회요청", "opt10082", next, screen_no)
    
    def request_opt10083_주식월봉차트조회요청(self, code, start_date, end_date, revise_stock_price, next=0):
        """
            주식월봉차트조회요청하는 메서드
            input: code(str), start_date(str), end_date(str), revise_stock_price(str), next(int) -> output: None
            start_date, end_date: YYYYMMDD
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", start_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "끝일자", end_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식월봉차트조회요청", "opt10083", next, screen_no)

    def request_opt10086_일별주가요청(self, code, date, output, next=0):
        """
            일별주가요청하는 메서드
            input: code(str), date(str), output(str), next(int) -> output: None
            date: YYYYMMDD
            output: 0:수량, 1:금액(백만원)
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회일자", date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "표시구분", output)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "일별주가요청", "opt10086", next, screen_no)

    def request_opt10087_시간외단일가요청(self, code, next=0):
        """
            시간외단일가요청하는 메서드
            input: code(str), next(int) -> output: None
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "시간외단일가요청", "opt10087", next, screen_no)

    def request_opt10094_주식년봉차트조회요청(self, code, start_date, end_date, revise_stock_price, next=0):
        """
            주식년봉차트조회요청하는 메서드
            input: code(str), start_date(str), end_date(str), revise_stock_price(str), next(int) -> output: None
            start_date, end_date: YYYYMMDD
        """
        screen_no = self.get_screen_no()
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", start_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "끝일자", end_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", revise_stock_price)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식년봉차트조회요청", "opt10094", next, screen_no)