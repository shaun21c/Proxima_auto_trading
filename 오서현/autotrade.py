"""
    실전프로그램 example
    1. 프로그램 시작후 로그인 -> 조건 검색식 리스트 가져오기
    2. ComboBox에 조건 검색식 리스트 추가후 사용할 조건 검색식 선택
    3. 선택한 조건 검색식 실시간 등록
    4. 키움증권 서버 -> 실시간 조건 만족하는 종목 발생 -> 정해진 금액으로 시장가 매수
    5. 미리 정해둔 목표 수익률과 손절 수익률 기반으로 해당 종목 실시간 모니터링
    6. 장 마감 -> 다음 거래일 시작 또는 프로그램 중간에 껐다가 켜도 동일하게 작동
    7. 10초 이상 매도 미체결시 시장가 매도
"""

import os, copy, sys, datetime
import pandas as pd

from collections import deque
from queue import Queue
from loguru import logger
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QComboBox
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import Qt, QSettings, QTimer, QAbstractTableModel
from PyQt5 import QtGui, uic

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" # 해상도 문제 해결

# 커스텀 ui 파일 로드
form_class = uic.loadUiType(r"C:\Users\shaun\OhSeohyeon\Hilbert_technology\Proxima_auto_trading\KiwoomInvestment\RealTimeOrder\99 main.ui")[0]

class PandasModel(QAbstractTableModel):
    """
        PandasModel 클래스
        pandas 데이터프레임을 테이블에 visualization 위한 모델 클래스
    """
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent = None):
        """행의 수"""
        return self._data.shape[0]
    
    def columnCount(self, parent = None):
        """열의 수"""
        return self._data.shape[1]
    
    def data(self, index, role = Qt.DisplayRole):
        """테이블 데이터"""
        if index.isValid(): # 인덱스가 유효하다면
            if role == Qt.DisplayRole: # 
                return str(self._data.iloc[index.row(), index.column()])
        return None
    
    def headerData(self, section, orientation, role):
        """헤더 데이터"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._data.index[section])
        return None
    
    def setData(self, index, value, role):
        # 항상 False를 반환해 편집을 비활성화
        return False
    
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
class KiwoomAPI(QMainWindow, form_class):
    """
        KiwoomAPI 클래스
        키움증권 API와 PyQt5 연동 클래스
    """
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()  # UI를 보여줍니다 (빈 화면)
        
        self.conditionInPushButton.clicked.connect(self.condition_in) # 조건식 등록 버튼 클릭시 condition_in 함수 실행
        self.conditionOutPushButton.clicked.connect(self.condition_out)
        self.settings = QSettings('MyApp', 'MyApp') # 설정 파일
        self.load_settings() # 설정 파일 로드
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.max_send_per_sec: int = 4  # 초당 TR 호출 최대 4번
        self.max_send_per_minute: int = 55
        self.max_send_per_hour: int = 950
        self.last_tr_send_times: deque = deque(maxlen = self.max_send_per_hour)
        self.tr_req_queue: Queue = Queue()
        self.orders_queue: Queue = Queue()
        self.unfinished_order_num_to_info_dict: dict = dict()
        self.stock_code_to_info_dict: dict = dict()
        self.scrnum: int = 5000
        self.condition_name_to_condition_idx_dict = dict()
        self.registered_condition_df: pd.DataFrame = pd.DataFrame(columns = ["화면번호", "조건식이름"])
        self.registered_conditioins_list = []
        self.account_info_df: pd.DataFrame = pd.DataFrame(
            columns = [
                "종목명",
                "매매가능수량",
                "보유수량",
                "매입가",
                "현재가",
                "수익률",
            ]
        )
        self.is_updated_realtime_watchlist = False
        self.current_available_buy_amount_krw = 0
        try:
            self.realtime_watchlist_df = pd.read_pickle("realtime_watchlist_df.pkl")
        except FileNotFoundError:
            self.realtime_watchlist_df = pd.DataFrame(
                columns = [
                    "종목명",
                    "현재가",
                    "평균단가",
                    "목표가",
                    "손절가",
                    "수익률",
                    "매수기반조건식",
                    "보유수량",
                    "매수주문완료여부",
                ]
            )

        self.realtime_registered_codes = set()
        self.stock_code_to_info_dict = dict()

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()    # 키움증권 API와 내부 메소드를 연동
        self._login() # 로그인
        
        self.timer1 = QTimer()
        self.timer2 = QTimer()
        self.timer3 = QTimer()
        self.timer4 = QTimer()
        self.timer5 = QTimer()
        self.timer6 = QTimer()
        self.timer7 = QTimer()
        self.timer8 = QTimer()
        self.timer1.timeout.connect(self.update_pandas_models)
        self.timer2.timeout.connect(self.send_tr_request)
        self.timer3.timeout.connect(self.send_orders)
        self.timer4.timeout.connect(self.request_get_account_balance)
        self.timer5.timeout.connect(self.request_current_order_info)
        self.timer6.timeout.connect(self.save_settings)
        self.timer7.timeout.connect(self.check_unfinished_orders)
        self.timer8.timeout.connect(self.check_outliers)

    def check_outliers(self): #118줄
        pop_list = []
        for row in self.realtime_watchlist_df.itertuples():
            stock_code = getattr(row, "Index")
            목표가 = getattr(row, "목표가")
            손절가 = getattr(row, "손절가")
            보유수량 = getattr(row, "보유수량")
            if 보유수량 != 0 and (목표가 is None or 손절가 is None):
                pop_list.append(stock_code)
        for stock_code in pop_list:
            logger.info(f"종목코드: {stock_code}, Outlier! Pop!")
            self.realtime_watchlist_df.drop(stock_code, inplace = True)

    def check_unfinished_orders(self): # 131줄
        pop_list = []
        for order_num, stock_info_dict in self.unfinished_order_num_to_info_dict.items():
            주문번호 = order_num,
            종목코드 = stock_info_dict["종목코드"]
            주문체결시간 = stock_info_dict["주문체결시간"]
            미체결수량 = stock_info_dict["미체결수량"]
            order_time = datetime.datetime.now().replace(
                hour = int(주문체결시간[:-4]),
                minute = int(주문체결시간[-4:-2]),
                second = int(주문체결시간[-2:])
            )
            basic_info_dict = self.stock_code_to_info_dict.get(종목코드, None)
            if not basic_info_dict:
                logger.info(f"종목코드: {종목코드}, 기본정보x 정정주문 실패!")
                return
            정정주문가격 = basic_info_dict["하한가"]
            if self.now_time - order_time > datetime.timedelta(seconds = 10):
                logger.info(f"종목코드: {종목코드}, 주문번호: {주문번호}, 미체결수량: {미체결수량}, 지정가 매도 정정 주문!")
                self.orders_queue.put(
                    [
                        "매도정정주문",
                        self._get_screen_num(),
                        self.accountNumComboBox.currentText(),
                        6,
                        종목코드,
                        미체결수량,
                        정정주문가격,
                        "00",
                        주문번호,
                    ]
                )
                pop_list.append(주문번호)
                for order_num in pop_list:
                    self.unfinished_order_num_to_info_dict.pop(order_num)

    def load_settings(self): #167
        """설정 파일 로드"""
        self.resize(self.settings.value("size", self.size()))
        self.move(self.settings.value("pos", self.pos()))
        self.buyAmountLineEdit.setText(self.settings.value("buyAmountLineEdit", defaultValue="100000", type=str))
        self.goalReturnLineEdit.setText(self.settings.value("goalReturnLineEdit", defaultValue="2.5", type=str))
        self.stopLossLineEdit.setText(self.settings.value("stopLossLineEdit", defaultValue="2.5", type=str))

    def request_current_order_info(self): # 179
        self.tr_req_queue.put([self.get_current_order_info])

    def update_pandas_models(self): # 182
        """PandasModel 클래스를 통해 데이터프레임을 테이블에 표시"""
        pd_model1 = PandasModel(self.registered_condition_df)
        self.registeredTableView.setModel(pd_model1)
        pd_model2 = PandasModel(self.realtime_watchlist_df)
        self.realtimeWatchlistTableView.setModel(pd_model2)
        pd_model3 = PandasModel(self.account_info_df)
        self.accountInfoTableView.setModel(pd_model3)

    def condition_in(self): # 191
        """조건식 등록"""
        condition_name = self.conditionComboBox.currentText()
        condition_idx = self.condition_name_to_condition_idx_dict.get(condition_name, None)
        if not condition_idx:
            logger.info("잘못된 조건 검색식 이름! 다시 확인해주세요.")
            return
        else:
            logger.info(f"{condition_name} 실시간 조건 등록 요청!")
            self.send_condition(self._get_screen_num(), condition_name, condition_idx, 0)

    def condition_out(self): # 202
        """조건식 해제"""
        condition_name = self.conditionComboBox.currentText()
        condition_idx = self.condition_name_to_condition_idx_dict.get(condition_name, None)
        if not condition_idx:
            logger.info("잘못된 조건 검색식 이름! 다시 확인해주세요.")
            return
        else:
            logger.info(f"{condition_name} 실시간 조건 해제 요청!")
            self.kiwoom.dynamicCall("SendConditionStop(QString, QString, int)", self._get_screen_num(), condition_name, condition_idx)
        
    def _set_signal_slots(self): # 208
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveRealData.connect(self._receive_realdata)
        self.kiwoom.OnReceiveConditionVer.connect(self._receive_condition)
        self.kiwoom.OnReceiveRealCondition.connect(self._receive_real_condition)
        self.kiwoom.OnReceiveTrData.connect(self.receive_tr_data)
        self.kiwoom.OnReceiveChejanData.connect(self._receive_chejandata)
        self.kiwoom.OnReceiveMsg.connect(self.receive_msg)

    def receive_msg(self, sScrNo, sRQName, sTrCode, sMsg): # 217
        logger.info(f"Received message! 화면번호 : {sScrNo}, 사용자 구분명 : {sRQName}, TR이름 : {sTrCode}, 메시지 : {sMsg}")

    def get_current_order_info(self): # 220
        self.set_input_value("계좌번호", self.accountNumComboBox.currentText())
        self.set_input_value("체결구분", "1")
        self.set_input_value("매매구분분", "0")
        # opt10075 TR 은 실시간 주문 체결내역 조회 요청
        self.comm_rq_data("opt10075_req", "opt10075", 0, self._get_screen_num())

    def request_get_account_balance(self): # 229
        self.tr_req_queue.put([self.get_account_balance])  # TR 요청 큐에 get_account_balance 함수 추가

    def send_tr_request(self): # 232
        self.now_time = datetime.datetime.now()
        if self._is_check_tr_req_condition() and not self.tr_req_queue.empty():
            request_func, *func_args = self.tr_req_queue.get()
            logger.info(f"Executing TR request function: {request_func}")
            request_func(*func_args) if func_args else request_func()
            self.last_tr_send_times.append(self.now_time)

    def get_account_info(self): # 241
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"])).rstrip(';')
        logger.info(f"계좌번호: {account_nums}")
        self.accountNumComboBox.addItems([x for x in account_nums.split(';') if x != ""])

    def get_account_balance(self): # 246
        if self.is_check_tr_req_condition(): # TR 요청 조건 확인
            self.set_input_value("계좌번호", self.accountNumComboBox.currentText())
            self.input_value("비밀번호", "0000")
            self.input_value("비밀번호입력매체구분", "00")
            self.comm_rq_data("opw00018_req", "opw00018", 0, self._get_screen_num()) # comm_rq_data 함수 호출, 계좌평가현황요청

    def comm_rq_data(self, rqname, trcode, next, screen_no): # 252
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)

    def receive_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage, sSplmMsg): #252
        # sScrNo: 화면번호, sRQName: 사용자 구분명, sTrCode: TR이름, sRecordName: 레코드이름, sPrevNext: 연속조회여부, nDataLength: 데이터길이, sErrorCode: 에러코드, sMessage: 메시지, sSplmMsg: 추가메시지
        # 조회요청 응답을 받거나 조회데이터를 수신했을 때 호출되는 이벤트
        # 조회데이터는 이 이벤트에서 GetCommData() 메서드를 통해 얻을 수 있음
        logger.info(f"Received TR data! 화면번호: {sScrNo}, 사용자 구분명: {sRQName}, TR이름: {sTrCode}, 레코드이름: {sRecordName}, 연속조회여부: {sPrevNext}, 데이터길이: {nDataLength}, 에러코드: {sErrorCode}, 메시지: {sMessage}, 추가메시지: {sSplmMsg}")
        try:
            if sRQName == "opw00018_req":
                self.on_opw00018_req(sTrCode, sRQName)
            elif sRQName == "opt10075_req":
                self.on_opt10075_req(sTrCode, sRQName)
            elif sRQName == "opt10001_req":
                self.on_opt10001_req(sTrCode, sRQName)
        except Exception as e:
            logger.exception(e)

    def get_basic_stock_info(self, stock_code): # 272줄
        if self.is_check_tr_req_condition():
            self.set_input_value("종목코드", stock_code)
            self.comm_rq_data("opt10001_req", "opt10001", 0, self._get_screen_num())

    def on_opt10001_req(self, sTrCode, sRQName): # 278
        종목코드 = self.get_comm_data(sTrCode, sRQName, 0, "종목코드").replace("A", "").strip()
        상한가 = abs(int(self.get_comm_data(sTrCode, sRQName, 0, "상한가")))
        하한가 = abs(int(self.get_comm_data(sTrCode, sRQName, 0, "하한가")))
        self.stock_code_to_info_dict[종목코드] = dict(상한가 = 상한가, 하한가 = 하한가)

    def on_opt10075_req(self, sTrCode, sRQName): # 284
        cnt = self._get_repeat_cnt(sTrCode, sRQName)
        for i in range(cnt):
            주문번호 = self.get_comm_data(sTrCode, sRQName, i, "주문번호").strip()
            미체결수량 = int(self.get_comm_data(sTrCode, sRQName, i, "미체결수량"))
            종목코드 = self.get_comm_data(sTrCode, sRQName, i, "종목코드").strip()
            주문구분 = self.get_comm_data(sTrCode, sRQName, i, "주문구분").replace("+", "").replace("-", "").strip()
            시간 = self.get_comm_data(sTrCode, sRQName, i, "시간").strip()
            order_time = datetime.datetime.now().replace(
                hour = int(시간[:4]),
                minute = int(시간[4:-2]),
                second = int(시간[-2:])
            )
            basic_info_dict = self.stock_code_to_info_dict.get(종목코드, None)
            if not basic_info_dict:
                logger.info(f"종목코드: {종목코드}, 기본정보x 정정주문 실패!")
                return
            정정주문가격 = basic_info_dict["하한가"]
            if 주문구분 in ("매도", "매도정정") and self.now_time - order_time > datetime.timedelta(seconds = 10):
                logger.info(f"종목코드: {종목코드}, 주문번호: {주문번호}, 미체결수량: {미체결수량}, 시장가 매도 정정 주문!")
                self.orders_queue.put(
                    [
                        "매도정정주문",
                        self._get_screen_num(),
                        self.accountNumComboBox.currentText(),
                        6,
                        종목코드,
                        미체결수량,
                        정정주문가격,
                        "00",
                        주문번호,
                    ]
                )

    def get_chejandata(self, nFid): # 317
        ret = self.kiwoom.dynamicCall("GetChejanData(int)", nFid)
        return ret

    def _receive_chejandata(self, sGubun, nItemCnt, sFidList): # 321
        # sGubun: 체결구분 접수와 체결시 '0', 국내주식 잔고전달은 '1', 파생잔고전달은 '4'
        if sGubun == "0":
            종목코드 = self.get_chejandata(9001).strip()
            종목명 = self.get_chejandata(302).strip()
            주문체결시간 = self.get_chejandata(908).strip()
            주문수량 = 0 if len(self.get_chejandata(900)) == 0 else int(self.get_chejandata(900))
            주문가격 = 0 if len(self.get_chejandata(901)) == 0 else int(self.get_chejandata(901))
            체결수량 = 0 if len(self.get_chejandata(911)) == 0 else int(self.get_chejandata(911))
            체결가격 = 0 if len(self.get_chejandata(910)) == 0 else int(self.get_chejandata(910))
            미체결수량 = 0 if len(self.get_chejandata(902)) == 0 else int(self.get_chejandata(902))
            주문구분 = self.get_chejandata(905).replace("+", "").replace("-", "").strip()
            매매구분 = self.get_chejandata(906).strip()
            단위체결가 = 0 if len(self.get_chejandata(914).strip()) == 0 else int(self.get_chejandata(914).strip())
            단위체결량 = 0 if len(self.get_chejandata(915).strip()) == 0 else int(self.get_chejandata(915).strip())
            원주문번호 = self.get_chejandata(904).strip()
            주문번호 = self.get_chejandata(9203).strip()
            logger.info(f"Received chejandata! 주문체결시간 {주문체결시간}, 종목코드: {종목코드}, 종목명: {종목명}, 주문수량: {주문수량}, 주문가격: {주문가격}, 체결수량: {체결수량}, 체결가격: {체결가격}, 미체결수량: {미체결수량}, 주문구분: {주문구분}, 매매구분: {매매구분}, 단위체결가: {단위체결가}, 단위체결량: {단위체결량}, 원주문번호: {원주문번호}, 주문번호: {주문번호}")
            if 주문구분 == "매수" and 체결수량 > 0:
                self.realtime_watchlist_df.loc[종목코드, "보유수량"] = 체결수량

            if 주문구분 in ("매도", "매도정정"):
                self.unfinished_order_num_to_info_dict[주문번호] = dict(
                    종목코드 = 종목코드,
                    미체결수량 = 미체결수량,
                    주문가격 = 주문가격,
                    주문체결시간 = 주문체결시간,
                )
                if 미체결수량 == 0:
                    self.unfinished_order_num_to_info_dict.pop(주문번호)
                    
            if sGubun == "1":
                logger.info("국내주식 잔고전달")

    def save_settings(self): # 358줄
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("buyAmountLineEdit", self.buyAmountLineEdit.text())
        self.settings.setValue("goalReturnLineEdit", self.goalReturnLineEdit.text())
        self.settings.setValue("stopLossLineEdit", self.stopLossLineEdit.text())
        self.realtime_watchlist_df.to_pickle("./realtime_watchlist_df.pkl")

    def _get_repeat_cnt(self, trcode, rqname): # 367줄
        ret = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret
    
    def on_opw00018_req(self, sTrCode, sRQName): # 372줄
        현재평가잔고 = int(self.get_comm_data(sTrCode, sRQName, 0, "추정예탁자산"))
        logger.info(f"현재평가잔고: {현재평가잔고}")
        self.currentBalanceLabel.setText(f"현재평가잔고: {현재평가잔고}")
        cnt = self._get_repeat_cnt(sTrCode, sRQName)
        self.account_info_df = pd.DataFrame(
            columns = [
                "종목명",
                "매매가능수량",
                "보유수량",
                "매입가",
                "현재가",
                "수익률",
            ]
        )
        current_account_code_list = []
        current_filled_amount_krw = 0
        for i in range(cnt):
            종목코드 = self.get_comm_data(sTrCode, sRQName, i, "종목번호").replace("A", "").strip()
            current_account_code_list.append(종목코드)
            종목명 = self.get_comm_data(sTrCode, sRQName, i, "종목명").strip()
            매매가능수량 = int(self.get_comm_data(sTrCode, sRQName, i, "매매가능수량"))
            보유수량 = int(self.get_comm_data(sTrCode, sRQName, i, "보유수량"))
            현재가 = int(self.get_comm_data(sTrCode, sRQName, i, "현재가"))
            매입가 = int(self.get_comm_data(sTrCode, sRQName, i, "매입가"))
            수익률 = float(self.get_comm_data(sTrCode, sRQName, i, "수익률(%)"))
            current_filled_amount_krw += 보유수량 * 현재가
            if 종목코드 in self.realtime_watchlist_df.index.to_list():
                self.realtime_watchlist_df.loc[종목코드, "종목명"] = 종목명
                self.realtime_watchlist_df.loc[종목코드, "평균단가"] = 매입가
                self.realtime_watchlist_df.loc[종목코드, "보유수량"] = 보유수량
            self.account_info_df.loc[i] = {
                "종목명": 종목명,
                "매매가능수량": 매매가능수량,
                "보유수량": 보유수량,
                "매입가": 매입가,
                "현재가": 현재가,
                "수익률": 수익률,
            }
        self.current_available_buy_amount_krw = 현재평가잔고 - current_filled_amount_krw
        if not self.is_updated_realtime_watchlist:
            for 종목코드 in current_account_code_list:
                self.register_code_to_realtime_list(종목코드)
            self.is_updated_realtime_watchlist = True
            realtime_tracking_code_list = self.realtime_watchlist_df.index.to_list()
            for stock_code in realtime_tracking_code_list:
                self.realtime_watchlist_df.drop(stock_code, inplace = True)
                logger.info(f"종목코드: {stock_code}, self.realtime_watchlist_df에서 삭제!")

    def set_input_value(self, id, value): # 421
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def get_comm_data(self, strTrCode, strRQName, nIndex, strItemName): # 424
        ret = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", strTrCode, strRQName, nIndex, strItemName)
        return ret.strip()
    
    def _login(self): # 429
        ret = self.kiwoom.dynamicCall("CommConnect()")
        if ret == 0:
            logger.info("로그인 창 열기 성공!")
            
    def _event_connect(self, err_code): # 434
        if err_code == 0:
            logger.info("로그인 성공!")
            self._after_login()
        else:
            raise Exception("로그인 실패!")

    def _after_login(self): #441
        self.get_account_info()
        logger.info("조건 검색 정보 요청!")
        self.kiwoom.dynamicCall("GetConditionLoad()")
        self.timer1.start(300)  # 0.3초마다 한번 Execute
        self.timer2.start(10)  # 0.01초마다 한번 Execute
        self.timer3.start(10) # 0.01초마다 한번 Execute
        self.timer4.start(5000)  # 5초마다 한번 Execute
        self.timer5.start(60000)  # 60초마다 한번 Execute  
        self.timer6.start(30000)  # 30초마다 한번 Execute
        self.timer7.start(100)  # 0.1초마다 한번 Execute
        self.timer8.start(1000)  # 1초마다 한번 Execute

    def _receive_condition(self): # 454
        condition_info = self.kiwoom.dynamicCall("GetConditionNameList()").split(";")
        for condition_name_idx_str in condition_info:
            if len(condition_name_idx_str) == 0:
                continue
            condition_idx, condition_name = condition_name_idx_str.split("^")
            self.condition_name_to_condition_idx_dict[condition_name] = condition_idx
        self.conditionComboBox.addItems(self.condition_name_to_condition_idx_dict.keys())

    def _get_screen_num(self): # 463
        self.scrnum += 1
        if self.scrnum > 5190:
            self.scrnum = 5000
        return self.scrnum
    
    def send_condition(self, scr_num, condition_name, condition_idx, n_search): # 469
        # n_search: 조회구분 (0: 조회, 1: 실시간조회)
        result = self.kiwoom.dynamicCall("SendCondition(QString, QString, int, int)", scr_num, condition_name, condition_idx, n_search)
        if result == 1:
            logger.info(f"{condition_name} 조건식 등록 성공!")
            self.registered_condition_df.loc[condition_idx] = {"화면번호" : scr_num, "조건식이름" : condition_name}
            self.registered_conditioins_list.append(condition_name)
        elif result != 1 and condition_name in self.registered_conditioins_list:
            logger.info(f"{condition_name} 조건식 이미 등록 완료료!")
            self.registered_condition_df.loc[condition_idx] = {"화면번호" : scr_num, "조건식이름" : condition_name}
        else:
            logger.info(f"{condition_name} 조건식 등록 실패!")

    def _receive_real_condition(self, strCode, strType, strConditionName, strConditionIndex):
        # strType: 이벤트 종류, "I": 종목편입, "D": 종목이탈
        # strConditionName: 조건식 이름
        # strConditionIndex: 조건식 인덱스
        logger.info(f"Received real condition! TR이름: {strCode}, 이벤트 종류: {strType}, 조건식 이름: {strConditionName}, 조건식 인덱스: {strConditionIndex}")
        # zfill이란 문자열을 오른쪽으로 정렬하고, 왼쪽에 0을 채워주는 메소드 즉, zero fill.
        if strConditionIndex.zfill(3) not in self.registered_condition_df.index.to_list(): # 조건식 인덱스가 등록된 조건식 데이터프레임에 없다면
            logger.info(f"조건명: {strConditionName}, 편입 조건식에 해당 안됨 pass!")
            return
        if strType == "I" and strCode not in self.realtime_watchlist_df.index.to_list():
            if strCode not in self.realtime_registered_codes:
                self.register_code_to_realtime_list(strCode) # 실시간 등록
            name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", [strCode])

            self.realtime_watchlist_df.loc[strCode] = {
                "종목명": name,
                "현재가": None,
                "평균단가": None,
                "목표가": None,
                "손절가": None,
                "수익률": None,
                "매수기반조건식": strConditionName,
                "보유수량": 0,
                "매수주문완료여부": False,
            }
            self.tr_req_queue.put([self.get_basic_stock_info, strCode])

    def get_comm_real_data(self, strCode, nFid): # 496
        return self.kiwoom.dynamicCall("GetCommRealData(QString, int)", strCode, nFid)
    
    def _receive_realdata(self, sCode, sRealType, sRealData): # 499
        if sRealType == "주식체결":
            self.now_time = datetime.datetime.now()
            now_price = int(self.get_comm_real_data(sCode, 10).replace("-", ""))
            if sJongmokCode in self.realtime_watchlist_df.index.to_list():
                if not self.realtime_watchlist_df.loc[sJongmokCode, "매수주문완료여부"]:
                    goal_price = now_price * (1 + float(self.goalReturnLineEdit.text()) / 100)
                    stoploss_price = now_price * (1 - float(self.stopLossLineEdit.text()) / 100)
                    self.realtime_watchlist_df.loc[sJongmokCode, "목표가"] = goal_price
                    self.realtime_watchlist_df.loc[sJongmokCode, "손절가"] = stoploss_price
                    if self.current_available_buy_amount_krw < int(self.buyAmountLineEdit.text()):
                        logger.info(f"주문 가능 금액 : {self.current_available_buy_amount_krw}원, 금액 부족으로 매수X ")
                        return
                    order_amount = int(self.buyAmountLineEdit.text()) // now_price # 얼마 살지. 1주 2주 형태이므로 int형.
                    if order_amount < 1:
                        logger.info(f"종목코드 : {sJongmokCode}, 주문 수량 부족으로 매수 진행 X")
                        return
                    self.orders_queue.put(
                        [
                            "시장가매수주문",
                            self._get_screen_num(),
                            self.accountNumComboBox.currentText(),
                            1,
                            sJongmokCode,
                            order_amount,
                            "",
                        ]
                    )
                    # 이걸 true로 안바꿔주면 계속 주문을 넣게 된다.
                    self.realtime_watchlist_df.loc[sJongmokCode, "매수주문완료여부"] = True

                self.realtime_watchlist_df.loc[sJongmokCode, "현재가"] = now_price
                mean_buy_price = self.realtime_watchlist_df.loc[sJongmokCode, "평균단가"]
                if mean_buy_price is not None:
                    self.realtime_watchlist_df.loc[sJongmokCode, "수익률"] = round(
                        (now_price - mean_buy_price) / mean_buy_price * 100 - 0.21,
                        2,
                    )
                보유수량 = int(copy.deepcopy(self.realtime_watchlist_df.loc[sJongmokCode, "보유수량"]))
                if 보유수량 == 0 and now_price < self.realtime_watchlist_df.loc[sJongmokCode, "손절가"]:
                    logger.info(f"종목코드: {sJongmokCode}, 손절가 도달! ")
                    basic_info_dict = self.stock_code_to_info_dict.get(sJongmokCode, None)
                    if not basic_info_dict:
                        logger.info(f"종목코드: {sJongmokCode}, 기본정보x 매도 주문 실패!")
                        return
                    logger.info(f"종목코드: {sJongmokCode}, 기본정보 x 정정주문 실패!")
                    self.orders_queue.put(
                        [
                            "매도주문",
                            self._get_screen_num(),
                            self.accountNumComboBox.currentText(),
                            1,
                            sJongmokCode,
                            order_amount,
                            "",
                            "03",
                            "",
                        ]
                    )
                    self.realtime_watchlist_df.loc[sJongmokCode, "매수주문완료여부"] = True

                self.realtime_watchlist_df.loc[sJongmokCode, "현재가"] = now_price
                mean_buy_price = self.realtime_watchlist_df.loc[sJongmokCode, "평균단가"]
                if mean_buy_price is not None:
                    self.realtime_watchlist_df.loc[sJongmokCode, "수익률"] = round(
                        (now_price - mean_buy_price) / mean_buy_price * 100 - 0.21,
                        2,
                    )
                보유수량 = int(copy.deepcopy(self.realtime_watchlist_df.loc[sJongmokCode, "보유수량"]))
                if 보유수량 > 0 and now_price < self.realtime_watchlist_df.loc[sJongmokCode, "손절가"]:
                    logger.info(f"종목코드: {sJongmokCode}, 손절가 도달! ")
                    basic_info_dict = self.stock_code_to_info_dict.get(sJongmokCode, None)
                    if not basic_info_dict:
                        logger.info(f"종목코드: {sJongmokCode}, 기본정보x 매도 주문 실패!")
                        return
                    주문가격 = basic_info_dict["하한가"]
                    self.orders_queue.put(
                        [
                            "매도주문",
                            self._get_screen_num(),
                            self.accountNumComboBox.currentText(),
                            2,
                            sJongmokCode,
                            보유수량,
                            주문가격,
                            "00",
                            "",
                        ]
                    )
                elif 보유수량 > 0 and now_price > self.realtime_watchlist_df.loc[sJongmokCode, "목표가"]:
                    logger.info(f"종목코드: {sJongmokCode}, 목표가 도달! ")
                    self.orders_queue.put(
                        [
                            "매도주문",
                            self._get_screen_num(),
                            self.accountNumComboBox.currentText(),
                            2,
                            sJongmokCode,
                            보유수량,
                            now_price,
                            "00",
                            "",
                        ]
                    )
                    self.realtime_watchlist_df.drop(sJongmokCode, inplace = True)

    def send_orders(self): # 592
        self.now_time = datetime.datetime.now()
        if self._is_check_tr_req_condition() and not self.orders_queue.empty():
            sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo = self.orders_queue.get()
            ret = self.send_orders(sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo)
            if ret == 0:
                logger.info(f"주문 요청 성공! 주문번호: {self.order_num}")
                self.order_num += 1



    def set_real(self, scrNum, strCodeList, strFidList, strRealType):
        self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString)", scrNum, strCodeList, strFidList, strRealType)
    
    def register_code_to_realtime_list(self, code):
        fid_list = "10;12;20;28" # 현재가, 등락률, 거래량, 시가
        if len(code) != 0:
            self.realtime_registered_codes.add(code)
            self.set_real(self._get_screen_num(), code, fid_list, "1")
            logger.info(f"{code} 실시간 등록 완료!")

    def is_check_tr_req_condition(self):
        now_time = datetime.datetime.now()
        if len(self.last_tr_send_times) >= self.max_send_per_sec and \
            now_time - self.last_tr_send_times[-self.max_send_per_sec] < datetime.timedelta(milliseconds = 1000):
            logger.info(f"초 단위 TR 요청 제한! 대기!")
            return False
        elif len(self.last_tr_send_times) >= self.max_send_per_minute and \
            now_time - self.last_tr_send_times[-self.max_send_per_minute] < datetime.timedelta(minutes = 1):
            logger.info(f"분 단위 TR 요청 제한! 대기!")
            return False
        elif len(self.last_tr_send_times) >= self.max_send_per_hour and \
            now_time - self.last_tr_send_times[-self.max_send_per_hour] < datetime.timedelta(minutes = 60):
            logger.info(f"시간 단위 TR 요청 제한! 대기!")
            return False
        else:
            return True
        
sys.__excepthook__ = sys.excepthook
