
class KiwoomRealTimeStockPrice:

    def __init__(self, kiwoom):
        """
        :param kiwoom: 키움 OpenAPI+ 인스턴스
        :param screen_number: 기본 화면번호
        """
        self.kiwoom = kiwoom
        self.screen_no_counter = 2000
    
    def get_screen_no(self):
        """
        화면번호를 자동으로 증가시키는 함수.
        :return: 새로 할당된 화면번호 (문자열)
        """
        self.screen_no_counter += 1
        return str(self.screen_no_counter)


    def get_real_time_stock_price_info(self, code, register_type=1):
        """
        특정 종목 코드의 주요 시세 정보를 가져옵니다.
        :param code: 종목 코드
        :param register_type: 실시간 등록타입 (0: 대체(등록한 종목들은 실시간 해지되고 등록한 종목만 실시간 시세가 등록) , 1: 추가(먼저 등록한 종목들과 함께 실시간 시세가 등록))
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
        
        fid_list = ";".join([str(fid) for fid in fid_map.values()])  

        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)

    def get_real_time_stock_trade_info(self,code, register_type=1):
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
        
        fid_list = ";".join([str(fid) for fid in fid_map.values()]) 

        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)
    
    def get_real_time_order_book_info(self,code, register_type=1):
        """
        특정 종목 코드의 주식 호가정보를 가져옵니다.
        :param code: 종목 코드
        """
        fid_map = {
            "호가시간" : 21,
            "매도호가1" : 41,
            "매도호가수량1" : 61,
            "매도호가직전대비1" : 81,
            "매수호가1" : 51,
            "매수호가수량1" : 71,
            "매수호가직전대비1" : 91,
            "매도호가2" : 42,
            "매도호가수량2" : 62,
            "매도호가직전대비2" : 82,
            "매수호가2" : 52,
            "매수호가수량2" : 72,
            "매수호가직전대비2" : 92,
            "매도호가3" : 43,
            "매도호가수량3" : 63,
            "매도호가직전대비3" : 83,
            "매수호가3" : 53,
            "매수호가수량3" : 73,
            "매수호가직전대비3" : 93,
            "매도호가4" : 44,
            "매도호가수량4" : 64,
            "매도호가직전대비4" : 84,
            "매수호가4" : 54,
            "매수호가수량4" : 74,
            "매수호가직전대비4" : 94,
            "매도호가5" : 45,
            "매도호가수량5" : 65,
            "매도호가직전대비5" : 85,
            "매수호가5" : 55,
            "매수호가수량5" : 75,
            "매수호가직전대비5" : 95,
            "매도호가6" : 46,
            "매도호가수량6" : 66,
            "매도호가직전대비6" : 86,
            "매수호가6" : 56,
            "매수호가수량6" : 76,
            "매수호가직전대비6" : 96,
            "매도호가7" : 47,
            "매도호가수량7" : 67,
            "매도호가직전대비7" : 87,
            "매수호가7" : 57,
            "매수호가수량7" : 77,
            "매수호가직전대비7" : 97,
            "매도호가8" : 48,
            "매도호가수량8" : 68,
            "매도호가직전대비8" : 88,
            "매수호가8" : 58,
            "매수호가수량8" : 78,
            "매수호가직전대비8" : 98,
            "매도호가9" : 49,
            "매도호가수량9" : 69,
            "매도호가직전대비9" : 89,
            "매수호가9" : 59,
            "매수호가수량9" : 79,
            "매수호가직전대비9" : 99,
            "매도호가10" : 50,
            "매도호가수량10" : 70,
            "매도호가직전대비10" : 90,
            "매수호가10" : 60,
            "매수호가수량10" : 80,
            "매수호가직전대비10" : 100,
            "매도호가총잔량" : 121,
            "매도호가총잔량직전대비" : 122,
            "매수호가총잔량" : 125,
            "매수호가총잔량직전대비" : 126,
            "예상체결가" : 23,
            "예상체결수량" : 24,
            "순매수잔량" : 128,
            "매수비율" : 129,
            "순매도잔량" : 138,
            "매도비율" : 139,
            "예상체결가전일종가대비" : 200,
            "예상체결가전일종가대비등락율" : 201,
            "예상체결가전일종가대비기호" : 238,
            "예상체결가(예상체결 시간동안에만 유효한 값)" : 291,
            "예상체결가량" : 292,
            "예상체결가전일대비기호" : 293,
            "예상체결가전일대비" : 294,
            "예상체결가전일대비등락율" : 295,
            "LP매도호가수량1" : 621,
            "LP매수호가수량1" : 631,
            "LP매도호가수량2" : 622,
            "LP매수호가수량2" : 632,
            "LP매도호가수량3" : 623,
            "LP매수호가수량3" : 633,
            "LP매도호가수량4" : 624,
            "LP매수호가수량4" : 634,
            "LP매도호가수량5" : 625,
            "LP매수호가수량5" : 635,
            "LP매도호가수량6" : 626,
            "LP매수호가수량6" : 636,
            "LP매도호가수량7" : 627,
            "LP매수호가수량7" : 637,
            "LP매도호가수량8" : 628,
            "LP매수호가수량8" : 638,
            "LP매도호가수량9" : 629,
            "LP매수호가수량9" : 639,
            "LP매도호가수량10" : 630,
            "LP매수호가수량10" : 640,
            "누적거래량" : 13,
            "전일거래량대비예상체결률" : 299,
            "장운영구분" : 215,
            "투자자별ticker" : 216
        }
        fid_list = ";".join([str(fid) for fid in fid_map.values()])  

        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)

    def get_after_hours_order_book_info(self, code, register_type=1):
        """
        특정 종목 코드의 주식 시간외 호가정보를 가져옵니다.
 
        """
        fid_map = {
            "호가시간" : 21,
            "시간외매도호가총잔량" : 131,
            "시간외매도호가총잔량직전대비" : 132,
            "시간외매수호가총잔량" : 135,
            "시간외매수호가총잔량직전대비" : 136,
            }

        fid_list = ";".join([str(fid) for fid in fid_map.values()])  

        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)

    def get_real_time_predicted_price(self, code, register_type=1):
        """
        특정 종목 코드의 예상체결가 정보를 가져옵니다.
        """
        fid_map = {
            "체결시간" : 20,
            "현재가" : 10,
            "전일대비" : 11,
            "등락률" : 12,
            "거래량" : 15,
            "누적거래량" : 13,
            "전일대비기호" : 25

        }

        fid_list = ";".join([str(fid) for fid in fid_map.values()])  

        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)
    
    def get_real_time_stock_info(self, code, register_type=1):
        """
        특정 종목 코드의 주식 종목 정보를 가져옵니다.
        :param code: 종목 코드
        """
        fid_map = {
            "임의연장": 297,
            "장전임의연장": 592,
            "장후임의연장": 593,
            "상한가": 305,
            "하한가": 306,
            "기준가": 307,
            "조기종료ELW발생": 689,
            "통화단위": 594,
            "증거금율표시": 382,
            "종목정보": 370,
            "Extra Item": 300
        }

        fid_list = ";".join([str(fid) for fid in fid_map.values()])
        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)

    def get_real_time_market_status(self, register_type=1):
        """
        장 시작 시간과 관련된 코드를 가져옵니다.
        """       
        
        fid_map = {
            "장운영구분": 215,
            "체결시간": 20,
            "장시작예상잔여시간": 214           
        }

        fid_list = ";".join([str(fid) for fid in fid_map.values()])
        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, fid_list, register_type)


    def get_real_time_vi_status(self, code, register_type=1):
        """
        실시간으로 VI 발동/해제 데이터를 요청합니다.
        :param code: 종목 코드 (종목별로 요청 가능)
        """
        fid_map = {
            "종목코드,업종코드": 9001,
            "종목명": 302,
            "누적거래량": 13,
            "누적거래대금": 14,
            "VI발동구분": 9068,
            "KOSPI,KOSDAQ,전체구분": 9008,
            "장전구분": 9075,
            "VI 발동가격": 1221,
            "매매체결처리시각": 1223,
            "VI 해제시각": 1224,
            "VI 적용구분(정적/동적/동적+정적)": 1225,
            "기준가격 정적": 1236,
            "기준가격 동적": 1237,
            "괴리율 정적": 1238,
            "괴리율 동적": 1239,
            "VI발동가 등락률": 1489,
            "VI발동횟수": 1490,
            "발동방향구분": 9069,
            "Extra Item": 1279
        }

        fid_list = ";".join([str(fid) for fid in fid_map.values()])
        screen_no = self.get_screen_no()
        self.kiwoom.SetRealReg(screen_no, code, fid_list, register_type)

    def get_real_time_order_execution(self, register_type=1):
        """
        실시간으로 주문 체결 데이터를 요청합니다.
        :param account_no: 계좌번호
        :param screen_no: 화면번호
        """

        fid_map = {
            "계좌번호": 9201,
            "주문번호": 9203,
            "관리자사번": 9205,
            "종목코드,업종코드": 9001,
            "주문업무분류": 912,
            "주문상태": 913,
            "종목명": 302,
            "주문수량": 900,
            "주문가격": 901,
            "미체결수량": 902,
            "체결누계금액": 903,
            "원주문번호": 904,
            "주문구분": 905,
            "매매구분": 906,
            "매도수구분": 907,
            "주문/체결시간": 908,
            "체결번호": 909,
            "체결가": 910,
            "체결량": 911,
            "현재가": 10,
            "(최우선)매도호가": 27,
            "(최우선)매수호가": 28,
            "단위체결가": 914,
            "단위체결량": 915,
            "당일매매수수료": 938,
            "당일매매세금": 939,
            "거부사유": 919,
            "화면번호": 920,
            "터미널번호": 921,
            "신용구분(실시간 체결용)": 922,
            "대출일(실시간 체결용)": 923
        }
        
        screen_no = self.get_screen_no()

        fid_list = ";".join([str(fid) for fid in fid_map.values()])
        self.kiwoom.SetRealReg(screen_no, fid_list, register_type)

    def get_real_time_account_balance(self, register_type=1):
        """
        실시간으로 잔고 데이터를 요청합니다.
        :param account_no: 계좌번호
        :param screen_no: 화면번호
        """
        fid_map = {
            "계좌번호": 9201,
            "종목코드,업종코드": 9001,
            "신용구분": 917,
            "대출일": 916,
            "종목명": 302,
            "현재가": 10,
            "보유수량": 930,
            "매입단가": 931,
            "총매입가(당일누적)": 932,
            "주문가능수량": 933,
            "당일순매수량": 945,
            "매도/매수구분": 946,
            "당일총매도손익": 950,
            "Extra Item1": 951,
            "(최우선)매도호가": 27,
            "(최우선)매수호가": 28,
            "기준가": 307,
            "손익율(실현손익)": 8019,
            "신용금액": 957,
            "신용이자": 958,
            "만기일": 918,
            "당일실현손익(유가)": 990,
            "당일실현손익률(유가)": 991,
            "당일실현손익(신용)": 992,
            "당일실현손익률(신용)": 993,
            "담보대출수량": 959,
            "Extra Item2": 924
        }

        screen_no = self.get_screen_no()

        fid_list = ";".join([str(fid) for fid in fid_map.values()])
        self.kiwoom.SetRealReg(screen_no, fid_list, register_type)  
