import os
os. envrion["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
import copy
import sys
from collections import deque
from queue import Queue
import datatime

from loguru import logger
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import Qt, QSettings, QTimer, QAbstractTableModel
from PyQt5 import QtGui, uic


form_class = uic.loadUiType("main.ui")[0]


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data = data

        def rowCount(self, parent=None):
            return self._data.shape[0]
        
        def columnCount(self, parent=None):
            return self._data.shape[1]
        
        def data(self, index, role=Qt.DisplayRole):
            if index.isValid():
                if role == Qt.DisplayRole:
                    return str(self._data.iloc[index.row(), index.column()])
                return None
            
        def headerData(self, section, orientation, role):
            if orientation == Qt.Horizontal and role == Qt. Displayrole:
                return self._data.columns[section]
        if orientation == Qt. Vertical and role == Qt.Displayrole:
            return self._data.index[section]
        return None

    def setData(self, index, value, role):
    #  항상 False를 반환하여 편집을 비활성화
    return False

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable


class KiwoomAPI(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()

        self.conditionInPushButton.clicked.connect(self.condition_in)
        self.conditionOutPushButton.clicked.connect(self.condition_out)
        self.settings = QSettings('MyAPP', 'myApp')
        self.load_settings()
        self.setWindowIcon(QtGui.QIcon('icon.ico'))

        self.max_send_per_sec: int = 4 #초당 TR 호출 최대 4번
        self.max_send_per_minute: int = 55 # 분당 TR 호출 최대 55번
        self.max_send_per_hour: int = 950 # 시간당 TR 호출 최대 950번
        self.last_tr_send_times = deque(maxlen=self.max_send_per_hour)
        self.tr_req_queue = Queue()
        self.orders_queue = Queue()
        self.unfinished_order_num_to_info_dict = dict()
        self.stock_code_to_info_dict = dict()
        self.scrnum = 5000
        self.condition_name_to_condition_idx_dict = dict()
        self.registered_condition_df = pd.DataFrame(columns=["화면번호", "조건식이름"])
        self.registered_conditions_list = []
        self.account_info_df = pd.DataFrame(
            columns=[
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
            self.realtime_watchlist_df = pd.read_pickle("./realtime_watchlist_df.pkl:")
        execpt FileNotFoundError:
            self.realtime_watchlist_df = pd.DataFrame(
                columns=["종목명", "현재가", "평균단가", "목표가", "손절가", "수익률", "매수기반조건식", "보유수량", "매수주문완료여부"]
            )
        self.realtime_registered_codes = set()
        self.stock_code_to_info_dict = dict()

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()  # 키움증권 API와 내부 메소드를 연동
        self._login()

        self.timer1 = QTimer()
        self.timer2 = Qtimer()
        self.timer3 = QTimer()
        self.timer4 = Qtimer()
        self.timer5 = Qtimer()
        self.timer6 = Qtimer()
        self.timer7 = Qtimer()
        self.timer8 = Qtimer()
        self.timer1.timeout.connect(self.update_pandas_models)
        self.timer2.timeout.connect(self.send_tr_request)
        self.timer3.timeout.connect(self.send_orders)
        self.timer4.timeout.connect(self.request_get_account-balance)
        self.timer5.timeout.connect(self.request_current_order_info)
        self.timer6.timeout.connect(self.save_settings)
        self.timer7.timeout.connect(self.check_unfinished_orders)
        self.timer8.timeout.connect(self.check_outliers)

    def check_outliers(self):
        pop_list = []
        for row in self.realtime_watchlist_df.itertuples():
            stock_code = getattr(row, "Index")
            목표가 = getattr(row, "목표가")
            손절가 = getattr(row, "손절가")
            보유수량 = getattr(row, "보유수량")
        if 보유수량 != 0 and(목표가 is None or 손절가 is None):
            pop_list.append(stock_code)
        for stock_code in pop_list:
            logger.info(f"종목코드: {stock_code}, Outlier! Pop!")
            self.realtime_watchlist_df.drop(stock_code, inplace=True)

    def check_unfinished_orders(self):
        pop_list = []
        for order_num, stock_info_dict in self, unfinised_order_num_to_info_dict.items():
            주문번호 = order_num
            종목코드 = stock_info_dict['종목코드']
            주문체결시간 = stock_info_dict['주문체결시간']
            미체결수량 = stock_info_dict['미체결수량']
            order_time = datatime.datetime.now().replace(
                hour=int(주문체결시간[:-4]),
                minute=int(주문체결시간[-4:-2])
                second=int(주문체결시간[-2:]),
            )
            basic_info_dict = self.stock_code_to_info_dict.get(종목코드, None)
            if not basic_info_dict:
                logger.info(f"종목코드: {종목코드}, 기본정보X 정정주문 실패!")
                return
            정정주문가격 = basic_info_dict['하한가']
            if self.now_time - order_time >=datetime.timedelta(seconds=10):
                logger.info(f"종목코드: {종목코드}, 주문번호: {주문번호}, 미체결수량: {미체결수량}, 지정가 매도 정정 주문!")
                self. orders_queue.put(
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

    def load_setttings(self):
        self.resize(self.settings.value("size", self.size()))
        self.move(self.settings.value("pos", self.pos()))
        self.buyAmountLineEdit.sexText(self.settings.value('buyAmountLineEdit', defaultValue="100000", type=str))
        self.goalReturnLineEdit.setText(self.settings.value('goalReturnEdit', defaultValue="2.5", type=str))
        self.stopLossLineEdit. setText(self.settings.value('stopLossLineEdit', defaultValue="-2.5", type=str))

    def request_current_order_info(self):
        self.tr_req.queue.put([self.get_current_order_info])

    def update_pandas_models(self):
        pd_model = PandasModel(self.registered_condition_df)
        self.registeredTableView.setModel(pd_model)
        pd_model2 = PandasModel(self.realtime_watchlist_df)
        self.watchListTableView.setModel(pd_model2)
        pd_model3 = PandasModel(self.account_info_df)
        self.accountTableView.setModel(pd_mode13)

    def condition_in(self):
        condition_name = self.conditionComboBox.currentText()
        condition_idx = self.condition_name_to_condition_idx_dict.get(condition_name, None)
        if not condition_idx:
            logger.info(f"잘못된 조건 검색식 이름! 다시 선택하세요!")
            return 
        else:
            logger.info(f"{condition_name} 실시간 조건 등록 요청!")
            self.send_condition(self._get_screen_num(), condition_name, condition_idx, 1)

    def condition_out(self):
        condition_name = self.conditionComboBox.currentText()
        condition_idx = self.condition_name_to_condition_idx_dict.get(condition_name, None)
        if not condition_idx:
            logger.info(f"잘못된 조건 검색식 이름! 다시 선택하세요!")
            return
        elif condition_idx in self.registered_condition_df.index:
            logger.info(f"{condition_name} 실시간 조건 편출!")
            self.registered_condition_df.drop(condition_idx, inplace=True)
        else:
            logger.info(f"조건식 편출 실패!")
            return                
                
    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveRealData.connect(self._receive_realdata)
        self.kiwoom.OnReceiveConditionVer.connect(self._receive_condition)
        self.kiwoom.OnReceiveRealCondition.connect(self._receive_real_condition)
        self.kiwoom.OnReceiveTrData.connect(self._receive_tr_data)
        self.kiwoom.OnReceiveChejanData.connect(self._receive_chejandata)
        self.kiwoom.OnReceiveMsg.connect(self.receive_msg)

    def receive_msg(self, sScrNo, sRQName, sTrCode, sMsg):
        logger.info(f"Received MSG | 화면번호: {sScrNo}, 사용자 구분명: {sRQName}, TR코드: {sTrCode}, 메시지: {sMsg}")

    def get_current_order_info(self):
        self.set_input_value("계좌번호", self.accountNumComboBox.currentText())
        self.set_input_value("체결구분", "1")
        self.set_input_value("매매구분", "0")
        self.comm_rq_data("opt10075_req", "opt10075", 0, self._get_screen_num())

    def request_get_account_balance(self):
        self.tr_req_queue.put(self.get_account_balance)

    def send_tr_request(self):
        self.now_time = datetime.datetime.now()
        if self.is_check_tr_req_condition() and not self.tr_req_queue.empty():
            request_func, *func_args = self.tr_req_queue.get()
            logger.info(f"Executing TR request function: {request_func}")
            request_func(*func_args) if func_args else request_func()
            self.last_tr_send_times.append(self.now_time)

    def get_account_info(self):
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"]).rstrip(';'))
        logger.info(f"계좌번호 리스트: {account_nums}")
        self.accountNumComboBox.addItems([x for x in account_nums.split(';') if x != ''])

    def get_account_balance(self):
        if self.is_check_tr_req_condition():
            self.set_input_value("계좌번호", self.accountNumComboBox.currentText())
            self.set_input_value("비밀번호", "")
            self.set_input_value("비밀번호입력매체구분", "00")
            self.comm_rq_data("opw00018_req", "opw00018", 0, self._get_screen_num())

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)

    def receive_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage, sSplmMsg):
        # sScrNo: 화면번호, sRQName: 사용자 구분명, sTrCode: TR이름, sRecordName: 레코드 이름, sPrevNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
        # 조회요청 응답을 받거나 조회데이터를 수신했을때 호출됩니다.
        # 조회데이터는 이 이벤트에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.
        logger.info(
            f"Received TR data sScrNo: {sScrNo}, sRQName: {sRQName}, "
            f"sTrCode: {sTrCode}, sRecordName: {sRecordName}, sPrevNext: {sPrevNext}, "
            f"nDataLength: {nDataLength}, sErrorCode: {sErrorCode}, sMessage: {sMessage}, sSplmMsg: {sSplmMsg}"
        )
        try:
            if sRQName == "opw00018_req":
                self._on_opw00018_req(sTrCode, sRQName)
            elif sRQName == "opw10075_req":
                self._on_opw10075_req(sTrCode, sRQName)
            elif sRQName == "opt10001_req":
                self._on_opt10001_req(sTrCode, sRQName)
        except Exception as e:
            logger.exception(e)

    def get_bsic_stock_info(self, stock_code):
        if self.is_check_tr_req_condition():
            self.set_inpu_value("종목코드", stock_code)
            self.comm_rq_data(f"opt10001_req","opt10001", 0, self._get_screen_num())

    def on_opt10001_req(self,sTrCode, sRQName):
        종목코드 = self.get_comm_data(sTrCode, sRQName, 0, "종목코드").replace("A", "").strip()
        상한가 = abs(int(self.get_comm_data(sTRCode,sRQName, 0, "상한가")))
        하한가 = abs(int(self.get_comm_data(sTrCode,sRQName, 0, "하한가")))
        self.stock_code_to_info_dict[종목코드] = dict(상한가=상한가, 하한가=하한가)

    def on_opt100075_req(self,sTrCode,sRQName):
        cnt = self._get_repeat_cnt(sTrCode, sRQName)
        for i in range(cnt)
            주문번호 = self.get_comm_data(sTrCode, sRQName, i, "주문번호").strip()
            미체결수량 = int(self.get_comm_data(sTrCode, sRQName, i, "미체결수량"))
            종목코드 = self.get_comm_data(sTrCode, sRQName, im "시간").strip()
            주문구분 =  self.get_comm_data(sTrCode, sRQName, i, "주문구분").replace("+", "").replace("-","").strip()
            시간 = self.get_comm_data(sTrCode, sRQName, i, "시간").strip()
            order_time = datetime.datetime.now().replace(
                hour-int(시간[:-4]),
                minute=int(시간[-4:-2]),
                second=int(시간[-4:]),
            )
            basic_info_dict = self.stock_code_to_info_dict.get(종목코드, None)
            if not basic_info_dict:
                logger.info(f"종목코드: {종목코두, 기본정보X 정정주문 실패!}")
                return
            정정주문가격 = basic_info_dict['하한가']
            if 주문구분 in ("매도", "매도정정") and self.now_time - order_time >= datetime.timedelta(seconds=10):
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

    def get_chejandata(self, nFid):
        ret = self.kiwoom.dynamicCall("GetChejanData(int)", nFid)
        return ret

    def receive_chejandata(self, sGubun, nItemCnt, sFIdList):
        # sGubun: 체결구분 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4'
        if sGubun == "0":
            종목코드 = self.get_chejandata(9001).replace("A", "").strip()
            종목명 = self.get_chejandata(302).strip()
            주문체결시간 = self.get_chejandata(908).strip()
            주문수량 = 0 if len(self.get_chejandata(900)) == 0 else int(self.get_chejandata(900))
            주문가격= 0 if len(self.get_chejandata(901)) == 0 else int(self.get_chejandata(901))
            체결수량 = 0 if len(self.get_chejandata(911)) == 0 else int(self.get_chejandata(911))
            체결가격 = 0 if len(self.get_chejandata(910)) == 0 else int(self.get_chejandata(910))
            미체결수량 = 0 if len(self.get_chejandata(902)) == 0 else int(self.get_chejandata(902))
            주문구분 = self.get._chejandata(905).replace("+", "").replace("-","").strip()
            매매구분 = self.get_chejandata(906).strip()
            단위체결가 = 0 if len(self.get_chejandata(914)) == 0 else int(self.get_chejandata(914))
            단위체결량 = 0 if len(self.get_chejandata(904).strip()
            원주문번호 = self.get_chejandata(904).strip()
            주문번호 = self.get+chejandata(9203).strip()
            logger.info(f"Received chejandata! 주문체결시간: {주문체결시간}, 종목코드: {종목코드}, "
                        f"종목명: {종목명},  주문수량: {주문수량}, 주문가격: {주문가격}, 체결수량: {체결수량}, 체결가격: {체결가격}, "
                        f"주문구분: {주문구분}, 미체결수량: {미체결수량}, 매매구분: {매매구분}, 단위체결가: {단위체결가}, "
                        f"단위체결량: {단위체결량}, 주문번호: {주문번호}, 원주문번호: {원주문번호}"
            if 주문번호 == "매수" and 체결수량 > 0:
                self.realtime_watchlist_df.loc[종목코드, "보유수량"] = 체결수량

            if 주문구분 in("매도", "매도정정"):
                self.unifnisehd_order_num_tp_info_dict[주문번호] = dict(
                    종목코드=종목코드
                    미체결수량=미체결수량,
                    주문가격=주문가격,
                    주문체결시간=주문체결시간
                )
                if 미체결수량 == 0;
                    self.unfinished_order_num_to_info_dict.pop(주문번호)

        if sGubun == 1;
            logger.info("잔고통보")

    def save_settings(self):
        # Write window size and position to config file
        self.settings.setValue("size", self.size())
        self.settigns.setValue("pos", self.pos())
        self.settings.setValue('buyAmountLineedit', self.buyAmountLineEdit.text())
        self.settings.setValue('goalReturnLineEdit', self.goalReturnLineEdit.text())
        self.settings.setValue('stopLossLineEdit', self.stopLossLineEdit.text())
        self.realtime_watchlist_df.top_picckle("./realtime_watchlist_df.pkl")

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.kiwoom.dynamicCall("GetRepeatCnt(QString, Qstring)", trcode, rqname)
        return set
    
    def on_opw00018_req(self, sTrCode, sRQName):
        현재평가잔고 = int(self.get_comm_data(sTrCode, sRQName, 0, "추정예탁자산"))
        logger.info(f"현재평가잔고: {현재평가잔고: ,}원")
        self.currentBalanceLabel.setText(f"현재 평가 잔고: {현재평가잔고: ,}원")
        cnt = self._get_repeat_cnt(sTRCode, sRQName)
        self.account_info_df = pd.DataFrame(
            columns[
                "종목명",
                "매매가능수량"
                "보유수량",
                "매입가",
                "현재가",
                "수익률",
            ]
        )
        current_account_code_list = []
        current_filled_amount_krw = 0
        for i in range(cnt):
            종목코드 = self.get_comm_data(sTrCodem sRQName, i, "종목번호").replace("A","").strip()
            current_account_code_list.append(종목코드)
            종목명 = self.get_comm_data(sTrCode, sRQName, i, "종목명)
            매매가능수량 = int(self.get_comm_data(sTrCode, sRQName, i, :매매가능수량))
            보유수량 = int(self.get_comm_data(sTrCode, sRQName, i, "보유수량"))
            현재가 = int(self.get_comm_data(sTrCode, sRQName, i, "현재가"))
            매입가 = int(self.get_comm_data(sTrCdoe, sRQName, i, "매입가"))
            수익률 = float(self.get_comm_data(sTRCode, sRQName, i, "수익률(%)"))
            current_filled_amount_krw =+ 보유수량 * 현재가
            if 종목코드 in self.realtime_watchlist_df.index.to_list():
                self.realtime_watchlist_df.loc[종목코드, "종목명"] = 종목명
                self.realtime_watchlist_df.loc[종목코드, "평균단가"] - 매입가
                self.realtime_watchlist_df.loc[종목코드,  "보유수량"] = 보유수량
            self.account_info_df.loc[종목코드] = {
                "종목명": 종목명,
                "매매가능수량": 매매가능수량,
                "현재가": 현재가,
                "보유수량": 보유수량,
                "매입가": 매입가,
                "수익률": 수익률,
            }
        self.current_available_buy_amount_krw = 현재평가잔고 - current_filled_amount_krw
        if not self.is_updated_realtime_watchlist:
            for 종목코드 in current_account_code_list:
                self.register_code_to_realtime_list(종목코드)
            self.is_updated_realtime_watchlist = True
            realtime+tracking_code_list = self.realtime_watchlist_df.index.to_list()
            for stock_code in realtime_tracking_code_list:
                if stock_code not in current_account_code_list:
                    self.realtime_watchlist_df.drop(stock_code, inplace=True)
                    logger.info(f"종목코드: {stock code} self.realtime_watchlist_df에서 drop!")

    def set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(Qstring, Qstring)", id, value)

    def get_comm_data(self,strTrCode, strRecordName, nIndex, strItemName):
        ret = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, Qstring)", strTrCode, strRecordName, nIndex, strItemName)
        return ret.strip()

        def _login(self):
            ret = self.kiwoom.dynamicCall("CommConnect()")
            if ret == 0:
                logger.info("로그인 창 열기 성공!")

        def _event_connect(self, err_code):
            if err_code == 0:
                logger. info("로그인 성공!")
                self._after_login()
            else:
                raise Exception("로그인 실패!")

        def _after_login(self):
            self.get_account_info()
            logger.info("조건 검색 정보 요청")
            self.kiwoom.dynamicCall("GetConditionLoad()")   # 조건 검색 정보 요청
            self.timer1.start(300)      #0.3초마다 한번
            self.timer1.start(10)       #0.01초마다 한번
            self.timer1.start(10)       #0.01초마다 한번
            self.timer1.start(5000)     # 5초마다 한번
            self.timer1.start(60000)    #60초마다 한번
            self.timer1.start(30000)    #30초마다 한번
            self.timer1.start(100)      #0.1초마다 한번
            self.timer1.start(1000)     #1초마다 한번

    def _receive_condition(self):
        condition_info = self.kiwoom.dynamicCall("GetConditionNameList()").split(';')
        for condition_name_idx_str in condition_info:
            if len(condition_name_idx_str) == 0:
                continue
            condition_idx, condition_name = condition_name_idx_str.split('^')
            self.condition_name_to_condition_idx_dict[condition_name] = condition_idx
        self.conditionComboBox.addItems(self.condition_name_to_condition_idx_dict.keys())

    def _get_screen_num(self):
        self.scrnum += 1
        if self.scrnum > 5190:
            self. scrnum = 5000
        return str(self.scrnum)

    def send_condition(self, scr_num, condition_name, condition_idx, n_search):
        # n_search:조회구분, 0: 조건검색, 1:실시간 조건검색
        result = self.kiwoom.dynamicCall(
            "SendCondition(QString, Qstring, int, int)",
            scr_num, condition_name, condition_idx, n_search
        )
        if result == 1:
            logger.info(f"{condition_name} 조건검색 등록!")
            self.registered_condition_df.loc[condition_idx] = {"화면번호":scr_num, "조건식이름": condition_name}
            self.registered_conditions_list.append(condition_name)
        elif result !=1 and condition_name in self.registered_conditions_list:
            logger.info(f"{condition_name} 조건 검색 이미 등록 완료!")
             self.registered_condition_df.loc[condition_idx] = {"화면번호": scr_num, "조건식이름": condition_name}
        else:
            logger.info(f"{condition_name}조건검색 이미 등록 완료!")

    def _receive_real_condition(self, strCode, strType, strConditionName, strConditionIndex):
        # strType: 이벤트 종류, "I":종목편입, "D", 종목이탈
        # strConditionName: 조건식 이름
        #strConditionIndex: 조건명 인덱스
        logger.info(f"Received real condition, {strCode}, {strType}, {strConditionName}, {strConditionIndex}")
        if strConditionIndex.zfill(3) not in self.registered_condition_df.index.to_list():
            logger.info(f"조건명: {strConditionName}, 편입 조건식에 해당 안됨 Pass")
            return
        if strType =- "I" and strCode not in self.realtime_watchlist_df.index.to_list():
            if strCode not in self.realtime_registered_codes:
                self.register_code_to_realtime_list(strCode)    # 실시간 체결 등록
            name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)",[strCode])

            self.realtime_watchlist_df.loc[strCode] = {
                '종목명': name,
                '현재가': None,
                '평균단가'" None,
                '목표가': None,
                '손절가': None,
                '수익률': None,
                '매수기반조건식': strConditionName,
                "보유수량": 0,
                "매수주문완료여부": False,
            }
            self.tr_req_queue.put({self.get_basic_stock_info, strCode})

    def get_comm_realdate(self, strCode, nFid):
        return self.kiwoom.dynamicCall("GetCommRealData(Qstring, int)", strCode, nFid)

    def _receive_realdata(self, sJongmokCode, sRealType, sRealData):
        if sRealType =- "주식체결":
            self.now_time = datetime.datetime.now()
            now_price = int(self.get_comm_realdata(sRealType, 10). replace('-', ''))    # 현재가
            if sJongmokCode in self.realtime_watchlist_df.index.to_list():
                if not self.realtime_watchlist_df.loc[sJongmokCode, "매수주문완료여부"]:
                    goal_price = now_price * (1 + float(self.ReturnLineEdit.text()) / 100)
                    stoploss_price = now_price * (1 + float(self.stopLossLineEdit.text()) / 100)
                    self.realtime_watchlist_df.loc[sJongmokCode, "목표가"] = goal_price
                    self.realtime_watchlist_df.loc[sJongmokCode, "손절가"] = stoploss_price
                    if self.current_available_buy_amount_krw < int(self.buyAmountLineEdit.text()):
                        logger.info(f"주문 가능 금액: {self.current_available_buy_amount_krw: ,}원! 금액 부족으로 매수X")
                        return
                    order_amount = int(self.buyAmountLineEdit.text()) // now_price
                    if order_amount < 1:
                        logger.info(f"종목코드: {sJongmokCode}, 주문수량 부족으로 매수 진행 X")
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
                                "03",
                                "",
                        ],
                    )
                    self.realtime_wathclist.df.loc[sJongmokCode, "매수주문완료여부"] = True

                self.realtime_watchlist_df.loc[sJongmokCode, '현재가'] = now_price
                mean_buy_price = self.realtime_watchlist_df.loc[sJongmokCode, '평균단가']
                if mean_buy_price is not None:
                    self.realtime_watchlist_df.loc[sJongmokcode, '수익률'] = round(
                        (now_price - mean_buy_price) / mean_buy_price * 100 - 0.21,
                        2,
                    )
                보유수량 = int(copy,deepcopy(self.realitme_watchlist_df.loc[sJongmokCode, '보유수량']))
                if 보유수량 > 0 and now_price < self.realtime_watchlist_df.loc[sJongmokCode, '손절가']:
                    logger.info(f"종목코드: {sJongmokcode} 매도 진행! (손절)")
                    basic_info_dict = self.stock_code_to_info_dict.get(sJongmokCode, None)
                    if not basic_info_dict:
                        logger.info(f"종목코드: {sJongmokCode}, 기본정보X 정정주문 실패!")
                        return
                    주문가격 = basic_info_dict['하한가']
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
                    self.realtime_watchlist_df.drop(sJongmokCode, inplace=True)
                elif 보유수량 > 0 and now_price > self.realtime_watchlist_df.loc[sJongmokCode, '목표가']:
                    logger.info(f"종목코드: {sJongmokCode} 매도 진행! (익절)")
                    self.orders_queue.put(
                        [
                            "매도주문",
                            self._get_screen_num()
                            self.accountNumComboBox.currentText(),
                            2,
                            sJongmokCodem
                            보유수량,
                            now_price,
                            "00",
                            "",
                        ],
                    )
                    self.realtime_watchlist_df.drop(sJongmokCode, inplace=True)

    def send_orders(self):
        self.now_time = datetime.datetime.now()
        if self.is_check_tr_req_condition() and not self.orders_queue.empty():
            sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGbm sOrgOrderNo = self.orders_queue.get()
            ret = self.send_order(sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGbm sOrgOrderNo)
            if ret == 0: