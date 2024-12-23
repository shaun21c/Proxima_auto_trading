import os
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
import sys
import time
import datetime
from queue import Queue
from threading import Thread, Event

from loguru import logger
from urllib.request import urlopen
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5 import uic

form_class = uic.loadUiType("main.ui")[0]


def request_crawling(req_in_queue: Queue, req_out_queue: Queue, thread_event: Event):
    logger.info(f"Crawling thread started")
    while not thread_event.is_set():
        if req_in_queue.empty():
            time.sleep(0.1) # 쓰레드가 과도하게 돌아가지 않게 방지
            continue
        req_data_dict = req_in_queue.get() # 큐에서 데이터를 가져옴, get()은 큐가 비어있으면 대기하다가 데이터가 들어오면 가져옴 
        if req_data_dict['action_id'] == '크롤링요청': # 큐에서 가져온 데이터의 action_id가 크롤링요청이면
            try: # 크롤링을 시도
                resultXML = urlopen(req_data_dict['url'])
                result = resultXML.read()
                xmlsoup = BeautifulSoup(result, 'xml')
                for t in xmlsoup.findAll("list"):
                    rcept_no = t.rcept_no.string
                    stock_code = t.stock_code.string
                    corp_name = t.corp_name.string
                    report_nm = t.report_nm.string
                    req_out_queue.put(
                        dict(
                            action_id = "크롤링요청",
                            공시번호 = rcept_no,
                            종목코드 = stock_code,
                            종목명 = corp_name,
                            공시제목 = report_nm,
                        )
                    )
            except Exception as e:
                logger.exception(e)
    logger.info(f"Crawling thread exited")


class MainWindow(QMainWindow, form_class):
    def __init__(self, req_in_queue: Queue, req_out_queue: Queue, thread_event: Event):
        super().__init__()
        self.setupUi(self)
        self.reqDartPushButton.clicked.connect(self.request_crawling)
        self.req_in_queue = req_in_queue   
        self.req_out_queue = req_out_queue       
        self.thread_event =  thread_event   

        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.check_result_queue)
        self.timer1.start(100)  # 0.1초마다 실행

    def check_result_queue(self):
        if not self.req_out_queue.empty():
            processed_data_dict = self.req_out_queue.get()
            self.resultTextEdit.append(
                f"공시번호: {processed_data_dict['공시번호']}, 종목코드: {processed_data_dict['종목코드']}, "
                f"종목명: {processed_data_dict['종목명']}, 공시제목: {processed_data_dict['공시제목']}"
                
            )
    
    def request_crawling(self):
        start_date = datetime.datetime.now().strftime("%Y%m%d")
        if len(self.dartAPIKEYLineEdit.text()) < 2:
            return
        for i in range (1, 100):
            url = f"ddd"\
                    f"crtfc_key = {self.dartAPIKEYLineEdit.text()}$bgn_de={start_date}&page_count=8&page_no={i}"
            self.new_data_signal.emit(
                dict(
                    action_id = "크롤링 요청",
                    url = url,
                )
            )

    def closeEvent(self, event):
        self.thread_event.set() # 이벤트 설정하여 스레드가 종료할 수 있도록 함
        QApplication.instance().quit()

if __name__ == '__main__':
    # 크롤링 요청 큐, 크롤링 결과 큐, 스레드 이벤트를 생성
    crawling_req_in_queue = Queue()
    crawling_out_queue = Queue()
    thread_event = Event()
    crawling_thread = Thread(
        target = request_crawling,
        args = (
            crawling_req_in_queue,
            crawling_out_queue,
            thread_event,

        )
    )
    # 스레드란? 프로세스 내에서 실행되는 흐름의 단위
    crawling_thread.start() # 크롤링 스레드 시작
    app = QApplication(sys.argv)
    # 메인 윈도우 생성후 크롤링 큐, 크롤링 결과 큐, 스레드 이벤트를 인자로 넘겨줌
    mainWindow = MainWindow(crawling_req_in_queue, crawling_out_queue, thread_event)
    mainWindow.show()
    sys.exit(app.exec_())