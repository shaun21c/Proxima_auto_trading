from PyQt5.QtCore import QEventLoop
from time import time

class KiwoomOrder:
    def __init__(self, kiwoom):
        """
        키움 실전 주문 처리를 위한 클래스
        Args:
            kiwoom_instance: 키움 API COM 객체
        """
        self.kiwoom = kiwoom
        self._create_event_loop()
        
        # 주문 결과 저장용 변수들
        self.order_no = ""          # 주문번호
        self.order_status = ""      # 주문상태
        self.order_success = False  # 주문 성공 여부
        self.order_error_msg = ""   # 주문 거부/에러 메시지
        
        # 주문 제한 관리
        self.last_order_time = 0    # 마지막 주문 시간
        self.order_count = 0        # 초당 주문 횟수
        
        # 거래구분 코드
        self.TRADE_TYPES = {
            "LIMIT": "00",           # 지정가
            "MARKET": "03",          # 시장가
            "CONDITIONAL": "05",     # 조건부지정가
            "BEST_LIMIT": "06",      # 최유리지정가
            "BEST_PRIORITY": "07",   # 최우선지정가
            "LIMIT_IOC": "10",       # 지정가IOC
            "MARKET_IOC": "13",      # 시장가IOC
            "BEST_IOC": "16",        # 최유리IOC
            "LIMIT_FOK": "20",       # 지정가FOK
            "MARKET_FOK": "23",      # 시장가FOK
            "BEST_FOK": "26",        # 최유리FOK
            "PRE_MARKET_CLOSE": "61", # 장전시간외종가
            "SINGLE_PRICE": "62",     # 시간외단일가
            "POST_MARKET_CLOSE": "81" # 장후시간외종가
        }
        
        # 주문가격 불필요 거래구분 (0으로 입력)
        self.NO_PRICE_TRADES = [
            "03", "06", "07", "13", "16", "23", "26", "61", "81"
        ]
        
        # 주문증거금 상한가 기준 거래구분
        self.MARGIN_AT_UPPER_LIMIT = [
            "03", "06", "07", "13", "16", "23", "26"
        ]
        
    def _create_event_loop(self):
        """이벤트 루프 생성"""
        self.order_loop = QEventLoop()
        
    def _check_order_limit(self) -> bool:
        """1초당 5회 주문 제한 체크"""
        current_time = time()
        if current_time - self.last_order_time >= 1:
            self.order_count = 0
            self.last_order_time = current_time
            
        self.order_count += 1
        if self.order_count > 5:
            self.order_error_msg = "주문 횟수 초과 (1초에 5회까지 가능)"
            return False
        return True
        
    def _validate_order(self, code: str, hoga_gb: str, price: int) -> bool:
        """주문 유효성 검사"""
        # 종목코드 길이 체크
        if len(code) != 6:
            self.order_error_msg = "올바른 종목코드가 아닙니다"
            return False
            
        # 거래구분 체크
        if hoga_gb not in self.TRADE_TYPES.values():
            self.order_error_msg = "올바른 거래구분이 아닙니다"
            return False
            
        # 주문가격 체크
        if hoga_gb in self.NO_PRICE_TRADES and price != 0:
            self.order_error_msg = f"{hoga_gb} 거래는 주문가격을 0으로 입력해야 합니다"
            return False
            
        return True
        
    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next):
        """
        주문 TR 데이터 수신 이벤트
        주문번호 존재 여부로 주문 성공 판단
        """
        self.order_no = self.kiwoom.GetCommData(trcode, rqname, 0, "주문번호").strip()
        self.order_success = bool(self.order_no)
        self.order_loop.exit()
        
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """주문 관련 메시지 수신"""
        self.order_error_msg = msg
        
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        체결정보 수신 이벤트
        gubun: 0 - 주문체결통보, 1 - 잔고통보
        """
        if gubun == '0':
            # 주문상태 업데이트
            self.order_status = self.kiwoom.GetChejanData(913).strip()
            # 필요한 경우 체결 상세 정보 저장
            self.filled_price = self.kiwoom.GetChejanData(910).strip()  # 체결가
            self.filled_quantity = self.kiwoom.GetChejanData(911).strip()  # 체결량
            self.remaining_quantity = self.kiwoom.GetChejanData(902).strip()  # 미체결수량
            
    def send_order(self, rqname: str, screen_no: str, account_no: str, order_type: int, 
                  code: str, quantity: int, price: int, hoga_gb: str, org_order_no: str = ""):
        """
        주식 주문 함수
        Args:
            rqname: 사용자 구분명
            screen_no: 화면번호
            account_no: 계좌번호 10자리
            order_type: 주문유형 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            code: 종목코드 (6자리)
            quantity: 주문수량
            price: 주문가격
            hoga_gb: 거래구분 (self.TRADE_TYPES 참고)
            org_order_no: 원주문번호 (정정/취소 주문시)
        Returns:
            bool: 주문 성공 여부
        """
        # 초기화
        self.order_no = ""
        self.order_success = False
        self.order_error_msg = ""
        
        # 주문 제한 체크
        if not self._check_order_limit():
            return False
            
        # 주문 유효성 검사
        if not self._validate_order(code, hoga_gb, price):
            return False
            
        # 이벤트 핸들러 연결
        self.kiwoom.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.kiwoom.OnReceiveMsg.connect(self._on_receive_msg)
        self.kiwoom.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        
        try:
            # 주문 전송
            result = self.kiwoom.SendOrder(
                rqname, screen_no, account_no, order_type,
                code, quantity, price, hoga_gb, org_order_no
            )
            
            # 주문 전송 성공 시 응답 대기
            if result == 0:
                self.order_loop.exec_()
            else:
                self.order_error_msg = f"주문전송 실패 (에러코드: {result})"
                
        finally:
            # 이벤트 핸들러 연결 해제
            self.kiwoom.OnReceiveTrData.disconnect(self._on_receive_tr_data)
            self.kiwoom.OnReceiveMsg.disconnect(self._on_receive_msg)
            self.kiwoom.OnReceiveChejanData.disconnect(self._on_receive_chejan_data)
        
        return self.order_success
        
    # 편의성을 위한 래퍼 함수들
    def buy_market_order(self, code: str, quantity: int, account_no: str, screen_no: str = "0101"):
        """시장가 매수"""
        return self.send_order(
            "시장가매수", screen_no, account_no, 1, code, quantity, 0, self.TRADE_TYPES["MARKET"]
        )
        
    def sell_market_order(self, code: str, quantity: int, account_no: str, screen_no: str = "0101"):
        """시장가 매도"""
        return self.send_order(
            "시장가매도", screen_no, account_no, 2, code, quantity, 0, self.TRADE_TYPES["MARKET"]
        )
        
    def buy_limit_order(self, code: str, quantity: int, price: int, account_no: str, screen_no: str = "0101"):
        """지정가 매수"""
        return self.send_order(
            "지정가매수", screen_no, account_no, 1, code, quantity, price, self.TRADE_TYPES["LIMIT"]
        )
        
    def sell_limit_order(self, code: str, quantity: int, price: int, account_no: str, screen_no: str = "0101"):
        """지정가 매도"""
        return self.send_order(
            "지정가매도", screen_no, account_no, 2, code, quantity, price, self.TRADE_TYPES["LIMIT"]
        )
        
    def cancel_order(self, org_order_no: str, code: str, quantity: int, account_no: str, screen_no: str = "0101"):
        """주문 취소"""
        return self.send_order(
            "주문취소", screen_no, account_no, 3, code, quantity, 0, self.TRADE_TYPES["LIMIT"], org_order_no
        )
        
    def modify_order(self, org_order_no: str, code: str, quantity: int, price: int,
                    account_no: str, screen_no: str = "0101", order_type: int = 5):
        """주문 정정 (order_type: 5-매수정정, 6-매도정정)"""
        return self.send_order(
            "주문정정", screen_no, account_no, order_type, code, quantity, price,
            self.TRADE_TYPES["LIMIT"], org_order_no
        )

    def buy_best_limit_order(self, code: str, quantity: int, account_no: str, screen_no: str = "0101"):
        """최유리지정가 매수"""
        return self.send_order(
            "최유리지정가매수", screen_no, account_no, 1, code, quantity, 0, 
            self.TRADE_TYPES["BEST_LIMIT"]
        )

    def sell_best_limit_order(self, code: str, quantity: int, account_no: str, screen_no: str = "0101"):
        """최유리지정가 매도"""
        return self.send_order(
            "최유리지정가매도", screen_no, account_no, 2, code, quantity, 0, 
            self.TRADE_TYPES["BEST_LIMIT"]
        )