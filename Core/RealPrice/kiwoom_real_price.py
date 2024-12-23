
class KiwoomRealTimeStockPrice:

    def __init__(self, kiwoom):
        """
        :param kiwoom: 키움 OpenAPI+ 인스턴스
        :param screen_number: 기본 화면번호
        """
        self.kiwoom = kiwoom
        self.screen_number = 2000
    
    def get_screen_no(self):
        """
        화면번호를 자동으로 증가시키는 함수.
        :return: 새로 할당된 화면번호 (문자열)
        """
        self.screen_no_counter += 1
        return str(self.screen_no_counter)


    def get_real_time_stock_price_info(self, code):
        """
        특정 종목 코드의 주요 시세 정보를 가져옵니다.
        :param code: 종목 코드
        """
        fid_map = {
            "현재가": 10,
            "전일대비": 11,
            "등락률": 12,
            "최우선매도호가": 27,
            "최우선매수호가": 28,
            "누적거래량" : 13,
            "누적거래대금": 14,
            "시가": 16,
            "고가": 17,
            "저가": 18,
            "전일대비기호" : 25,
            "전일거래량대비": 26,
            "거래대금증감": 29,
            "전일거래량대비": 30,
            "거래회전율": 31,
            "거래비용": 32,
            "시가총액": 311,
            "시가총액비중": 312,
            "상한가발생시간": 567,
            "하한가발생시간": 568
        }
            
        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_map, "0")

    def get_real_time_stock_trade_info(self,code):
        """
        특정 종목 코드의 주식 체결정보를 가져옵니다.
        :param code: 종목 코드
        """
        fid_map = {
            "체결시간": 20,
            "현재가": 10,
            "전일대비": 11,
            "등락률": 12,
            "최우선매도호가" : 27,
            "최우선매수호가": 28,
            "거래량(+는 매수체결, -는 매도체결)": 15,
            "누적거래량": 13,
            "누적거래대금": 14,
            "시가": 16,
            "고가": 17,
            "저가": 18,
            "전일대비기호": 25,
            "전일거래량대비": 26,
            "거래대금증감" : 29,
            "전일거래량대비(비율)": 30,
            "거래회전율": 31,
            "거래비용": 32,
            "체결강도": 228,
            "시가총액": 311,
            "장구분" : 290,
            "KO접근도": 691,
            "상한가발생시간": 567,
            "하한가발생시간": 568,
            "전일 동시간 거래량 비율" : 851
        }
        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_map, "0")

        