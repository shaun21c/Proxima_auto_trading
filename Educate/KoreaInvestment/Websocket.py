import json
import websockets
import asyncio
from queue import Queue

from loguru import logger
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

# json: JSON 형식의 데이터를 처리하기 위한 표준 라이브러리입니다. 웹소켓 통신에서 데이터 직렬화 및 역직렬화에 사용됩니다.
# websockets: 비동기 웹소켓 클라이언트를 구현하기 위한 라이브러리입니다. 웹소켓 프로토콜을 사용하여 서버와의 통신을 가능하게 합니다.
# asyncio: 비동기 I/O를 위한 표준 라이브러리로, 이벤트 루프, 코루틴, 태스크 등을 관리합니다.
# loguru: 파이썬의 로깅(logging)을 간편하게 사용할 수 있도록 도와주는 라이브러리입니다. 로그를 출력하고 관리하는 데 사용됩니다.
# Crypto.Cipher.AES: AES 암호화를 위한 모듈로, pycryptodome 패키지에서 제공됩니다.
# Crypto.Util.Padding.unpad: 암호화된 데이터를 복호화할 때 패딩을 제거하기 위한 함수입니다.
# base64.b64decode: Base64로 인코딩된 데이터를 디코딩하기 위한 함수입니다.





# run_websocket 함수는 한국투자증권 API 객체와 웹소켓 URL을 받아 웹소켓 연결을 설정하고 데이터를 주고받는 비동기 작업을 실행합니다.
# korea_invest_api: 한국투자증권 API를 사용하기 위한 객체 또는 인스턴스입니다. API 호출을 위해 필요한 인증 정보와 메서드를 포함하고 있을 것입니다.
# websocket_url: 웹소켓 서버에 연결하기 위한 URL입니다. 예를 들어, 실시간 시세 정보를 제공하는 서버의 주소입니다.
def run_websocket(korea_invest_api, websocket_url): # 웹소켓을 실행시키는 함수 
    #이벤트 루프 초기화
    loop = asyncio.get_event_loop()                                     # 현재 실행 중인 이벤트 루프를 가져옵니다. 이벤트 루프는 비동기 작업을 관리하고 실행하는 핵심 구성 요소입니다.
    loop.run_until_complete(connect(korea_invest_api, websocket_url))   # 주어진 코루틴(coroutine)이 완료될 때까지 이벤트 루프를 실행합니다. 여기서는 connect라는 비동기 함수를 실행하고, 이 함수가 완료될 때까지 대기합니다.

"""
def run_websocket(korea_invest_api, websocket_url, req_in_queue: Queue, realtime_data_out_queue: Queue): # 웹소켓을 실행시키는 함수 
    #이벤트 루프 초기화
    loop = asyncio.get_event_loop()                                     # 현재 실행 중인 이벤트 루프를 가져옵니다. 이벤트 루프는 비동기 작업을 관리하고 실행하는 핵심 구성 요소입니다.
    loop.run_until_complete(connect(korea_invest_api, websocket_url, req_in_queue, realtime_data_out_queue))   # 주어진 코루틴(coroutine)이 완료될 때까지 이벤트 루프를 실행합니다. 여기서는 connect라는 비동기 함수를 실행하고, 이 함수가 완료될 때까지 대기합니다.
"""


# 이 코드는 AES-256 방식의 CBC(Cipher Block Chaining) 모드를 사용하여 Base64로 인코딩된 암호화 텍스트를 복호화하는 함수입니다. 
# key: AES-256 비밀키입니다. AES-256은 256비트의 비밀키를 요구하며, 이 비밀키는 암호화와 복호화 과정에서 사용됩니다. 이 비밀키는 32바이트 크기여야 하며, 일반적으로 문자열로 제공됩니다.
# iv: **초기화 벡터(IV: Initialization Vector)**입니다. AES-256 CBC 모드에서는 첫 번째 블록 암호화를 위해 필요한 값으로, 블록 단위 암호화 시 안전성을 높이기 위해 사용됩니다. IV는 암호화된 메시지와 함께 전송되며, 복호화 시에도 동일한 IV를 사용해야 합니다.
# cipher_text: Base64로 인코딩된 암호화 텍스트입니다. AES로 암호화된 이진 데이터를 Base64로 인코딩하여 텍스트 형태로 변환한 데이터입니다. Base64는 바이너리 데이터를 텍스트로 변환하여 안전하게 전달하기 위한 인코딩 방식입니다.
def aes_cbc_base64_dec(key, iv, cipher_text):
    """
    :param key: str type AES256 secret key value
    :param iv: str type AES356 Initialize Vector
    :param cipher_text: Base64 encoded AES256 str
    :return: Base65 AES265 decode str
    """
    # 복호화 과정
    # AES 객체 생성: AES.new()를 사용하여 AES 암호화 객체를 생성합니다.
    # key.encode('utf-8'): 주어진 비밀키(key)를 UTF-8로 인코딩하여 바이트 형태로 변환합니다. AES 알고리즘은 바이트 형태의 데이터를 처리하기 때문에 문자열로 주어진 비밀키를 먼저 인코딩합니다.
    # AES.MODE_CBC: AES의 CBC 모드를 지정합니다. CBC 모드는 블록 암호화 방식으로, 각 블록이 이전 블록의 암호화 결과에 의존합니다.
    # iv.encode('utf-8'): IV도 문자열로 주어지므로, 이를 바이트 형태로 인코딩하여 사용합니다.
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))

    # Base64 디코딩: b64decode(cipher_text)를 사용하여 Base64로 인코딩된 암호화 텍스트를 바이너리 데이터로 변환합니다. Base64는 텍스트 데이터를 바이너리로 변환하는 인코딩 방식입니다.
    # 복호화: cipher.decrypt()를 사용하여 디코딩된 암호화 데이터를 복호화합니다. 이 과정에서 AES-256 CBC 모드를 사용하여 암호화된 데이터를 원래의 바이너리 데이터로 복원합니다.
    # 패딩 제거: unpad() 함수는 복호화된 데이터에서 패딩을 제거합니다. AES 암호화에서는 마지막 블록의 크기를 맞추기 위해 패딩을 추가하는데, 복호화 후에는 이를 제거해야 원본 데이터를 복원할 수 있습니다.
    # 문자열로 변환: 마지막으로, 복호화된 바이트 데이터를 bytes.decode()를 사용하여 UTF-8 문자열로 변환합니다. 이는 최종적으로 복호화된 텍스트 데이터를 반환하는 과정입니다.
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))


# 이 코드는 AES-256을 사용해 암호화된 데이터를 복호화하고, 복호화된 데이터를 기반으로 주식 체결 및 주문 내역을 처리하는 기능을 수행합니다. 데이터를 해석한 후, 체결 정보와 주문 내역을 로그로 출력합니다. 
# 매개변수
# data: 암호화된 주문 정보 또는 체결 데이터를 포함한 문자열입니다.
# key: AES 암호화에서 사용된 비밀키입니다.
# iv: AES 암호화에서 사용된 **초기화 벡터(IV)**입니다.
# account_num: 계좌번호를 확인하기 위해 사용되는 기본값으로, 조건에 따라 갱신됩니다.

# AES-256 복호화를 통해 암호화된 데이터를 해독.
# 계좌번호와 거부 여부를 확인하여 유효한 주문인지 체크.
# 체결 여부와 주문 상세 내역(가격, 수량, 종목 정보)을 추출.
# 매수/매도 및 정정 주문 여부를 구분하여 처리.
# 로그로 주요 주문 및 체결 정보를 기록하여 관리.

def receive_signing_notice(data, key, iv, account_num=''):      # 이 함수는 data라는 암호화된 데이터를 복호화한 후 주식 주문 내역과 체결 상태를 파악하고, 관련 정보를 출력합니다.
    """
    상세 메뉴는 아래 링크 참조

    """
    # AES256 처리 단계
    aes_dec_str = aes_cbc_base64_dec(key, iv, data) # aes_cbc_base64_dec: AES-256 암호화로 암호화된 data를 주어진 key와 iv를 사용해 복호화하는 함수입니다.
    values = aes_dec_str.split('^')                 # 복호화된 데이터는 ^ 구분자로 나뉜 문자열이고, 이를 values 리스트로 변환합니다.

    # 복호화된 데이터의 두 번째 값인 values[1]에 계좌번호가 들어있습니다. 계좌번호 앞 8자리가 일치하지 않으면 이 함수는 종료됩니다. 이는 보안을 위해 유효한 계좌번호인지 확인하는 과정입니다.
    account_num = values[1] 
    if account_num[:8] != account_num:
        return
    
    # 주문 거부 여부 확인: values[12]에 저장된 값이 0이 아니면 주문이 거부된 상태로 인식되고, 함수는 종료됩니다.
    refusal = values[12]    # 거부 여부
    if refusal != "0":
        logger.info(f"Got 거부 TR!")
        return
    
    # 체결 여부 및 주문 정보 추출
    # settlement: 체결 여부를 나타냅니다.
    # stock_no: 주식의 종목 코드입니다.
    # stock_name: 주식의 이름입니다.
    # time: 주문이 이루어진 시간을 나타냅니다.
    # order_amount: 주문 수량으로, 수량 정보가 없으면 0으로 처리됩니다.
    settlement = values[13] #체결여부
    stock_no = values[8] # 종목코드
    stock_name = values[18] # 종목명
    time = values[11] # 시간
    order_amount = 0 if len(values[16]) == 0 else int(values[16]) # 주문수량

    # 주문 가격과 체결 가격 계산
    # order_price: 주문한 가격을 계산합니다. 체결 여부에 따라 주문 가격 필드가 달라지기 때문에 분기 처리로 선택합니다.
    # settlement_amount: 실제 체결된 수량을 나타냅니다.
    # settlement_price: 체결되지 않은 경우 가격을 0으로 설정합니다.
    if values[13] == '1':
        order_price = 0 if len(values[10]) == 0 else int(values[10]) # 주문가격: 
    else:
        order_price = 0 if len(values[22]) == 0 else int(values[22]) # 주문가격
    settlement_amount = 0 if len(values[9]) == 0 or settlement == "1" else int(values[9])
    if values[13] == '1':
        settlement_price = 0
    else: 
        settlement_price = 0 if len(values[10]) == 0 else int(values[10])

    # 매수/매도 및 정정 구분
    # buysell_category: 매수(02) 또는 매도(01) 여부를 나타냅니다.
    # cancel_category: 정정 주문인지 확인하는 필드입니다.
    # 이 두 필드에 따라 주문이 매수인지 매도인지, 혹은 매수/매도 정정 주문인지를 결정합니다.    
    buysell_category = values[4]  # 매도매수구분
    cancel_category = values[5] # 정정구분
    if buysell_category == "02" and cancel_category != "0":
        order_category = "매수정정"
    elif buysell_category == "01" and cancel_category != "0":
        order_category = "매도정정"
    elif buysell_category == "02":
        order_category = "매수"
    elif buysell_category == "01":
        order_category = "매도"
    else:
        raise ValueError(f"주문구분 실패! 매도매수구분: {buysell_category}, 정정구분: {cancel_category}")
    

    # 주문번호 및 체결 정보 로그 기록
    # 마지막으로 주문 번호, 원주문 번호 및 다른 중요한 정보들을 로그로 기록합니다. 이 정보는 체결된 주문의 상세 내역을 담고 있습니다.
    order_no = values[2]    #주문번호
    original_order_no = values[3]   #원주문번호
    logger.info(f"Received chejandata! 시간: {time}, "
                f"종목코드: {stock_no}, 종목명: {stock_name}, 주문수량: {order_amount}, "
                f"주문가격: {order_price}, 체결수량: {settlement_amount}, 체결가격: {settlement_price}, "
                f"주문구분: {order_category}, 주문번호: {order_no}, "
                f"원주문번호: {original_order_no}, 체결여부: {settlement}")




# 이 함수는 실시간 호가 정보를 받아서 이를 처리합니다. 호가 정보는 ^ 문자로 구분된 데이터를 포함하고 있으며, 이 데이터를 처리하여 매수, 매도 호가와 각각의 호가 수량을 추출한 후, 이를 딕셔너리로 정리하여 반환합니다.
def receive_realtime_hoga_domestic(data):
    """
    상세 메뉴는 아래의 링크 참조

    """

    # data.split('^'): 이 코드는 수신된 데이터를 ^ 문자를 기준으로 분할하여 리스트로 변환합니다. 각각의 값들은 values 리스트에 저장됩니다.
    # 예를 들어, "AAPL^1000^100^..."와 같은 형식의 데이터를 ^ 기준으로 나누면 ['AAPL', '1000', '100', ...] 이런 식으로 분리됩니다.
    values = data.split('^') # 수신데이터를 split       
    data_dict = dict()                      # 호가 데이터를 담을 빈 딕셔너리를 생성합니다.
    data_dict["종목코드"] = values[0]       # values[0]에는 종목 코드가 들어있으며, 이를 딕셔너리의 "종목코드" 키로 저장합니다.

    for i in range(1,11):           # for i in range(1, 11): 이 반복문은 1호가부터 10호가까지의 매수, 매도 호가 정보를 처리합니다.
        """
        매수 호가:
        values[i + 12]: values 리스트에서 매수 호가 데이터를 가져옵니다. i는 1부터 10까지 반복되며, i + 12는 매수 호가가 저장된 위치를 가리킵니다.
        values[i + 32]: 해당 매수 호가의 수량을 가져옵니다. i + 32는 매수 호가 수량의 위치를 가리킵니다.
        매도 호가:
        values[2 + i]: values 리스트에서 매도 호가 데이터를 가져옵니다. 2 + i는 매도 호가가 저장된 위치를 가리킵니다.
        values[22 + i]: 해당 매도 호가의 수량을 가져옵니다. 22 + i는 매도 호가 수량의 위치를 가리킵니다.
        """

        data_dict[f"매수{i}호가"] = values[i + 12]
        data_dict[f"매수{i}호가수량"] = values[i + 32]
        data_dict[f"매도{i}호가"] = values[2 + i]
        data_dict[f"매도{i}호가수량"] = values[22 + i]

    return data_dict        # 마지막으로, 매수와 매도 호가 정보가 저장된 data_dict 딕셔너리를 반환합니다. 이 딕셔너리에는 종목 코드, 매수 및 매도 호가, 각 호가의 수량 정보가 모두 포함됩니다.


# 이 코드는 실시간 국내 주식 체결 정보를 처리하는 함수로, 체결된 주식의 기본 정보를 받아들이고, 이를 딕셔너리 형태로 반환하는 역할을 합니다. 
# 데이터를 | 기호로 구분하여 접근하며, 각 항목을 처리하는 방식으로 동작합니다. 주식의 체결 시간, 현재가, 종목 코드를 처리하고 이를 반환하는 구조로 설계되었습니다.
def receive_realtime_tick_domestic(data):
    """
    메뉴 순서는 다음과 같음 '|'으로 분리해서 아래와 같이 하나씩 접근하면 됩니다.
    유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|
    매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|
    매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|
    신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량최전율|전일동시간누적거래량|전일동시간누적거래량비율|
    시간구분코드|임의종료구분코드|정적VI발동기준가
    """

    # 다른 것들도 얼마든지 구현가능하다
    values = data.split('^')
    stock_no = values[0]    #종목코드
    settlement_time = values[1] #체결시간
    current_price = int(values[2]) # 현재가

    return dict(
        종목코드 = stock_no,
        체결시간 = settlement_time,
        현재가 = current_price,
    )


def receive_realtime_tick_overseas(data):
    """
    실시간종목코드|종목코드|소수점자리수|현지영업일자|현지일자|현지시간|한국일자|한국시간|시가|고가|저가|
    현재가|대비구분|전일대비|등락률|매수호가|매도호가|매수잔량|매도잔량|체결량|거래량|거래대금|매도체결량|매수체결량|체결강도|시장구분
    """
    values = data.split('^')
    stock_no = values[0]    #종목코드
    local_time = values[5]  #현지시간
    korea_time = values[7]  #한국시간
    current_price = float(values[11]) # 현재가

    return dict(
        종목코드 = stock_no,
        현지시간 = local_time,
        한국시간 = korea_time,
        현재가 = current_price,
    )

# 1
async def connect(korea_invest_api, url):
    logger.info("한국투자증권 API 웹소켓 연결 시도!")

    # 주어진 url로 웹소켓을 통해 연결을 설정합니다. 이 구문은 비동기 방식으로 처리되며, 연결이 끊어질 때까지 웹소켓 통신을 유지합니다.
    # 연결 유지를 위한 Ping 메시지 주기를 설정하는데, 여기서는 None으로 설정되어 있으므로 기본적인 핑 메시지는 비활성화됩니다.
    async with websockets.connect(url, ping_interval=None) as websocket:           
        stock_code = "005930"   # 삼성전자 종목코드

        # 실시간 체결 및 호가 등록
        # get_send_data: 한국투자증권 API를 통해 체결 및 호가 데이터를 서버로 전송하기 위한 데이터를 구성합니다.
        # cmd=3: 체결 등록을 위한 명령어.
        # cmd=1: 호가 등록을 위한 명령어.
        # await websocket.send(): 준비된 데이터를 웹소켓을 통해 서버에 전송합니다.
        # korea_invest_api.get_send_data 라는 데이터 형식이 korea_invest_api 객체 내부에 있다
        send_data = korea_invest_api.get_send_data(cmd=3, stockcode = stock_code) # 체결 등록
        logger.info(f"[실시간 체결 등록] 종목코드: {stock_code}")
        await websocket.send(send_data)
        send_data = korea_invest_api.get_send_data(cmd=1, stockcode = stock_code) # 호가 등록
        logger.info(f"[실시간 호가 등록] 종목코드: {stock_code}")
        await websocket.send(send_data)


        # 실시간 등록 후 데이터를 수신하는 과정
        while True:
            # 데이터 수신 처리. 비동기 함수는 결과를 기다려야 하는 부분이 있으면 무조건 await을 사용해야한다. 안그러면 pass함.
            data = await websocket.recv()   # await websocket.recv(): 웹소켓을 통해 서버에서 보내오는 데이터를 비동기적으로 수신합니다. 수신된 데이터는 문자열 형태로 전달됩니다.

            # 체결 및 호가 데이터 처리
            if data[0] == '0':  # 실시간 호가 및 체결 데이터
                recvstr = data.split('|') # 수신데이터가 실데이터 이전은 '|'으로 나눠져있어 split
                trid0 = recvstr[1]  # 분리한 것의 첫번째

                if trid0 == "HOSTCNTO": # 주식체결 데이터 처리
                    data_cnt = int(recvstr[2])   # 체결데이터 개수: 여러 개의 체결데이터가 고속으로 들어오는 경우를 위함. 허나 그런 경우는 매우 드물고 보통 1이라 생각하면 된다고 한다.
                    for cnt in range(data_cnt):
                        
                        # receive_realtime_hoga_domestic 함수가 실시간 데이터 처리 함수이다. 
                        data_dict = receive_realtime_hoga_domestic(recvstr[3])      # recvstr[3]이 실제 체결데이터가 들어간 str값이다
                        logger.info(f"주식 체결 데이터: {data_dict}")

                        # 한번만 받고 해제하기. 지속적으로 실시간 데이터를 받고 싶으면 이 부분을 해제하면 됨. 
                        send_data = korea_invest_api.get_send_data(cmd=4, stockcode = stock_code) #체결 해제: 실시간 체결 해제에 대한 send data를 받는다.
                        logger.info(f"[실시간 체결 해제] 종목코드: {stock_code}")
                        await websocket.send(send_data) # 그 것을 다시 웹소켓 서버에 보내줘야한다. 그래야 완료됨.

                elif trid0 ==  "HOSTASPO":  # 주식호가 데이터 처리
                    data_dict = receive_realtime_hoga_domestic(recvstr[3])
                    logger.info(f"주식 호가 데이텨: {data_dict}")

                    # 한번만 받고 해제하기. 지속적으로 실시간 데이터를 받고 싶으면 이 부분을 해제하면 됨
                    send_data = korea_invest_api.get_send_data(cmd=2, stockcode = stock_code) # 호가 해제
                    logger.info(f"[실시간 호가 해제] 종목코드: {stock_code}")
                    await websocket.send(send_data)

            # 에러 처리 및 AES-256 처리
            else:
                jsonObject = json.loads(data)       # 수신된 JSON 형식의 데이터를 파싱합니다
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":              # 수신된 데이터가 PINGPONG 메시지가 아닌 경우에만 처리합니다.
                    rt_cd = jsonObject["body"]["rt_cd"]

                    # 에러 처리: rt_cd가 1이면 에러, 0이면 정상적인 응답으로 처리합니다.
                    if rt_cd == '1': # 에러일 경우 처리
                        logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                    elif rt_cd == '0': # 정상일 경우 처리
                        logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid in ("HOSTCNIO", "HOSTCNI9"):
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            logger.info(f'### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]')

                # PINGPONG 메시지: 서버에서 연결 유지 여부를 확인하기 위한 PINGPONG 메시지를 수신하면, 동일한 메시지를 다시 서버로 보내어 연결을 유지합니다.        
                elif trid == "PINGPONG":
                    logger.info(f'### RECV [PINGPONG] [{data}]')
                    await websocket.send(data)
                    logger.info(f"### SEND [PINGPONG] [{data}]")

# 2
async def connect(korea_invest_api, url):

    # 한 증권계좌 아이디에 여러 개의 계좌가 있으면 웹소켓은 한 아이디에 대해서 모두 수신을 하기 때문에 여러 계좌의 실시간 정보를 동시다발적으로 가져올 수 있다. 그렇기에 계좌번호로 필터링해주는 역할이 반드시 필요하다
    running_account_num = korea_invest_api.account_num
    logger.info("한국투자증권 API 웹소켓 연결 시도!")
    async with websockets.connect(url, ping_interval=None) as websocket:
        send_data = korea_invest_api.get_send_data(cmd=5, stockcode=None)   # 주문 접수 / 체결 통보 등록
        logger.info("체결 통보 등록")
        await websocket.send(send_data)
        while True:
            data = await websocket.recv()
            if data[0] == '0':      # 실시간 호가 및 체결 데이터 
                pass                # 생략
            elif data[0] == '1':
                recvstr = data.split('|')   # 수신데이터 이전은 |으로 나뉘어져 있어 split 필요
                trid0 = recvstr[1]
                if trid0 in ("H0STCNI0", "H0STCNI9"):    # 주식 체결 통보 처리
                    receive_signing_notice(recvstr[3], aes_key, aes_iv, running_account_num)
            
            # 실시간 주식 데이터도, 실시간 체결 데이터도 아닌 것
            # 에러 처리 및 AES-256 처리
            else:
                jsonObject = json.loads(data)       # 수신된 JSON 형식의 데이터를 파싱합니다
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":              # 수신된 데이터가 PINGPONG 메시지가 아닌 경우에만 처리합니다.
                    rt_cd = jsonObject["body"]["rt_cd"]

                    # 에러 처리: rt_cd가 1이면 에러, 0이면 정상적인 응답으로 처리합니다.
                    if rt_cd == '1': # 에러일 경우 처리
                        logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                    elif rt_cd == '0': # 정상일 경우 처리
                        logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid in ("HOSTCNIO", "HOSTCNI9"):

                            # 아래의 두 변수를 저장해두었다가 receive_signing_notice에 넘겨줘야 해당 정보들을 해독이 가능한 상태로 수신가능. 계좌정보라 더욱 민감한 듯.
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            logger.info(f'### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]')

                # PINGPONG 메시지: 서버에서 연결 유지 여부를 확인하기 위한 PINGPONG 메시지를 수신하면, 동일한 메시지를 다시 서버로 보내어 연결을 유지합니다.        
                elif trid == "PINGPONG":
                    logger.info(f'### RECV [PINGPONG] [{data}]')
                    await websocket.send(data)
                    logger.info(f"### SEND [PINGPONG] [{data}]")

# 3
async def connect(korea_invest_api, url):

## 해외 쪽은 실시간 호가 데이터를 받기 어려운 경우가 있어서 추천하지 않는다...

    logger.info("한국투자증권 API 웹소켓 연결 시도!")
    async with websockets.connect(url, ping_interval=None) as websocket:
        stock_code = "DNASAAPL" # D + NAS(나스닥) + AAPL(애플)
        send_data = korea_invest_api.overseas_get_send_data(cmd=3, stockcode=stock_code)   # 주문 접수 / 체결 통보 등록
        logger.info(f"[실시간 체결 등록] 종목코드: {stock_code}")
        await websocket.send(send_data)
        while True:
            data = await websocket.recv()
            if data[0] == '0':      # 실시간 호가 및 체결 데이터 
                recvstr = data.split('|')   
                trid0 = recvstr[1]
                if trid0 == "HDFSCNT0":  # 주식체결 데이터 처리
                    data_cnt = int(recvstr[2])  # 체결 데이터 개수 
                    for cnt in range(data_cnt):
                        data_dict = receive_realtime_tick_overseas(recvstr[3])
                        logger.info(f"주식 체결 데이터: {data_dict}")
                        send_data = korea_invest_api.overseas_get_send_data(cmd = 4, stockcode = stock_code)
                        logger.info(f"[실시간 체결 해제] 종목코드: {stock_code}")
                        await websocket.send(send_data)

            elif data[0] == '1':
                pass
            
            # 실시간 주식 데이터도, 실시간 체결 데이터도 아닌 것
            # 에러 처리 및 AES-256 처리
            else:
                jsonObject = json.loads(data)       # 수신된 JSON 형식의 데이터를 파싱합니다
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":              # 수신된 데이터가 PINGPONG 메시지가 아닌 경우에만 처리합니다.
                    rt_cd = jsonObject["body"]["rt_cd"]

                    # 에러 처리: rt_cd가 1이면 에러, 0이면 정상적인 응답으로 처리합니다.
                    if rt_cd == '1': # 에러일 경우 처리
                        logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                    elif rt_cd == '0': # 정상일 경우 처리
                        logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid in ("HOSTCNIO", "HOSTCNI9"):

                            # 아래의 두 변수를 저장해두었다가 receive_signing_notice에 넘겨줘야 해당 정보들을 해독이 가능한 상태로 수신가능. 계좌정보라 더욱 민감한 듯.
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            logger.info(f'### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]')

                # PINGPONG 메시지: 서버에서 연결 유지 여부를 확인하기 위한 PINGPONG 메시지를 수신하면, 동일한 메시지를 다시 서버로 보내어 연결을 유지합니다.        
                elif trid == "PINGPONG":
                    logger.info(f'### RECV [PINGPONG] [{data}]')
                    await websocket.send(data)
                    logger.info(f"### SEND [PINGPONG] [{data}]")

# 4
async def connect(korea_invest_api, url):
    logger.info("한국투자증권 API 웹소켓 연결 시도!")
    async with websockets.connect(url, ping_interval=None) as websocket:
        send_data = korea_invest_api.get_send_data(cmd=5, stockcode=None)   # 주문 접수 / 체결 통보 등록
        logger.info("체결 통보 등록")
        await websocket.send(send_data)
        while True:
            data = await websocket.recv()
            if data[0] == '0':      # 실시간 호가 및 체결 데이터 
                pass                # 생략
            elif data[0] == '1':
                recvstr = data.split('|')   # 수신데이터 이전은 |으로 나뉘어져 있어 split 필요
                trid0 = recvstr[1]
                if trid0 == "H0GSCNI0":    # 주식 체결 통보 처리
                    receive_signing_notice(recvstr[3], aes_key, aes_iv)
            
            # 실시간 주식 데이터도, 실시간 체결 데이터도 아닌 것
            # 에러 처리 및 AES-256 처리
            else:
                jsonObject = json.loads(data)       # 수신된 JSON 형식의 데이터를 파싱합니다
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":              # 수신된 데이터가 PINGPONG 메시지가 아닌 경우에만 처리합니다.
                    rt_cd = jsonObject["body"]["rt_cd"]

                    # 에러 처리: rt_cd가 1이면 에러, 0이면 정상적인 응답으로 처리합니다.
                    if rt_cd == '1': # 에러일 경우 처리
                        logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                    elif rt_cd == '0': # 정상일 경우 처리
                        logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid in ("HOSTCNIO", "HOSTCNI9"):

                            # 아래의 두 변수를 저장해두었다가 receive_signing_notice에 넘겨줘야 해당 정보들을 해독이 가능한 상태로 수신가능. 계좌정보라 더욱 민감한 듯.
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            logger.info(f'### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]')

                # PINGPONG 메시지: 서버에서 연결 유지 여부를 확인하기 위한 PINGPONG 메시지를 수신하면, 동일한 메시지를 다시 서버로 보내어 연결을 유지합니다.        
                elif trid == "PINGPONG":
                    logger.info(f'### RECV [PINGPONG] [{data}]')
                    await websocket.send(data)
                    logger.info(f"### SEND [PINGPONG] [{data}]")

# 5
async def connect(korea_invest_api, url, req_in_queue, realtime_data_out_queue):

    # 한 증권계좌 아이디에 여러 개의 계좌가 있으면 웹소켓은 한 아이디에 대해서 모두 수신을 하기 때문에 여러 계좌의 실시간 정보를 동시다발적으로 가져올 수 있다. 그렇기에 계좌번호로 필터링해주는 역할이 반드시 필요하다
    running_account_num = korea_invest_api.account_num
    logger.info("한국투자증권 API 웹소켓 연결 시도!")
    async with websockets.connect(url, ping_interval=None) as websocket:
        send_data = korea_invest_api.get_send_data(cmd=5, stockcode=None)   # 주문 접수 / 체결 통보 등록
        logger.info("체결 통보 등록")
        await websocket.send(send_data)
        while True:
            if not req_in_queue.empty():
                req_data_dict = req_in_queue.get()
                action_id = req_data_dict['action_id']
                if action_id == "실시간체결등록":
                    stock_code = req_data_dict['종목코드']
                    send_data = korea_invest_api.get_send_data(cmd=3, stockcode = stock_code)   # 체결등록
                    logger.info(f"[실시간 체결 등록] 종목코드: {stock_code}")
                    await websocket.send(send_data)
                elif action_id == "실시간호가등록":
                    stock_code = req_data_dict['종목코드']
                    send_data = korea_invest_api.get_send_data(cmd = 1, stockcode = stock_code) # 호가등록
                    logger.info(f"[실시간 호가 등록] 종목코드: {stock_code}")
                    await websocket.send(send_data)
                elif action_id == "실시간체결해제":
                    stock_code = req_data_dict['종목코드']
                    send_data = korea_invest_api.get_send_data(cmd = 4, stockcode = stock_code) # 체결해제
                    logger.info(f"[실시간 호가 등록] 종목코드: {stock_code}")
                    await websocket.send(send_data)
                elif action_id == "실시간호가해제":
                    stock_code = req_data_dict['종목코드']
                    send_data = korea_invest_api.get_send_data(cmd = 2, stockcode = stock_code) # 호가해제
                    logger.info(f"[실시간 호가 해제] 종목코드: {stock_code}")
                    await websocket.send(send_data)
                elif action_id == "종료":
                    logger.info("종료 이벤트 발생으로 WebSocket 종료!")
                    break

            data = await websocket.recv()
            if data[0] == '0':
                recvstr = data.split('|')   # 수신데이터가 실데이터 이전은 '|'로 나눠져 있어 split
                trid0 = recvstr[1]
                if trid0 == "H0STCNT0":  # 주식체결 데이터 처리
                    data_cnt = int(recvstr[2])  # 체결 데이터 개수
                    for cnt in range(data_cnt):
                        data_dict = receive_realtime_tick_domestic(recvstr[3])
                        # logger.info(f"주식 체결 데이터: {data_dict}")
                        realtime_data_out_queue.put(
                            dict(
                                action_id = "실시간체결",
                                종목코드 = data_dict["종목코드"],
                                data = data_dict,
                            )
                        )
                elif trid0 == "H0STASP0": # 주식호가 데이터 처리
                    data_dict = receive_realtime_hoga_domestic(recvstr[3])
                    # logger.info(f"주식 호가 데이터: {data_dict}")
                    realtime_data_out_queue.put(
                        dict(
                            action_id = "실시간 호가",
                            종목코드 = data_dict["종목코드"],
                            data = data_dict,
                        )
                    )
            
            elif data[0] == '1':
                recvstr = data.split('|')   # 수신데이터 이전은 |으로 나뉘어져 있어 split 필요
                trid0 = recvstr[1]
                if trid0 in ("H0STCNI0", "H0STCNI9"):    # 주식 체결 통보 처리
                    receive_signing_notice(recvstr[3], aes_key, aes_iv, running_account_num, realtime_data_out_queue)
            
            # 실시간 주식 데이터도, 실시간 체결 데이터도 아닌 것
            # 에러 처리 및 AES-256 처리
            else:
                jsonObject = json.loads(data)       # 수신된 JSON 형식의 데이터를 파싱합니다
                trid = jsonObject["header"]["tr_id"]

                if trid != "PINGPONG":              # 수신된 데이터가 PINGPONG 메시지가 아닌 경우에만 처리합니다.
                    rt_cd = jsonObject["body"]["rt_cd"]

                    # 에러 처리: rt_cd가 1이면 에러, 0이면 정상적인 응답으로 처리합니다.
                    if rt_cd == '1': # 에러일 경우 처리
                        logger.info(f"### ERROR RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                    elif rt_cd == '0': # 정상일 경우 처리
                        logger.info(f"### RETURN CODE [{rt_cd}] MSG [{jsonObject['body']['msg1']}]")
                        # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                        if trid in ("HOSTCNIO", "HOSTCNI9"):

                            # 아래의 두 변수를 저장해두었다가 receive_signing_notice에 넘겨줘야 해당 정보들을 해독이 가능한 상태로 수신가능. 계좌정보라 더욱 민감한 듯.
                            aes_key = jsonObject["body"]["output"]["key"]
                            aes_iv = jsonObject["body"]["output"]["iv"]
                            logger.info(f'### TRID [{trid}] KEY[{aes_key}] IV[{aes_iv}]')

                # PINGPONG 메시지: 서버에서 연결 유지 여부를 확인하기 위한 PINGPONG 메시지를 수신하면, 동일한 메시지를 다시 서버로 보내어 연결을 유지합니다.        
                elif trid == "PINGPONG":
                    logger.info(f'### RECV [PINGPONG] [{data}]')
                    await websocket.send(data)
                    logger.info(f"### SEND [PINGPONG] [{data}]")


def stockhoga_domestic(data):
    """
    print("stockhoga[%s]"%(data))
    """
    recvvalue = data.split('^') # 수신데이터를 split '^'

    print("유가증권 단축 종목코드 [" + recvvalue[0] + "]")
    print("영업시간 [" + recvvalue[1] +"]" + "시간구분코드 [" + recvvalue[2] + "]")
    print("=============================")
    print("매도호가10 [%s]  잔량10 [%s]" % (recvvalue[12], recvvalue[32]))
    print("매도호가09 [%s]  잔량09 [%s]" % (recvvalue[11], recvvalue[31]))
    print("매도호가08 [%s]  잔량08 [%s]" % (recvvalue[10], recvvalue[30]))
    print("매도호가07 [%s]  잔량07 [%s]" % (recvvalue[9], recvvalue[29]))
    print("매도호가06 [%s]  잔량06 [%s]" % (recvvalue[8], recvvalue[28]))
    print("매도호가05 [%s]  잔량05 [%s]" % (recvvalue[7], recvvalue[27]))
    print("매도호가04 [%s]  잔량04 [%s]" % (recvvalue[6], recvvalue[26]))
    print("매도호가03 [%s]  잔량03 [%s]" % (recvvalue[5], recvvalue[25]))
    print("매도호가02 [%s]  잔량02 [%s]" % (recvvalue[4], recvvalue[24]))
    print("매도호가01 [%s]  잔량01 [%s]" % (recvvalue[3], recvvalue[23]))
    print("=============================")
    print("매수호가01 [%s]  잔량01 [%s]" % (recvvalue[13], recvvalue[33]))
    print("매수호가02 [%s]  잔량02 [%s]" % (recvvalue[14], recvvalue[33]))
    print("매수호가03 [%s]  잔량03 [%s]" % (recvvalue[15], recvvalue[33]))
    print("매수호가04 [%s]  잔량04 [%s]" % (recvvalue[16], recvvalue[33]))
    print("매수호가05 [%s]  잔량05 [%s]" % (recvvalue[17], recvvalue[33]))
    print("매수호가06 [%s]  잔량06 [%s]" % (recvvalue[18], recvvalue[33]))
    print("매수호가07 [%s]  잔량07 [%s]" % (recvvalue[19], recvvalue[33]))
    print("매수호가08 [%s]  잔량08 [%s]" % (recvvalue[10], recvvalue[33]))
    print("매수호가09 [%s]  잔량09 [%s]" % (recvvalue[1], recvvalue[33]))
    print("매수호가10 [%s]  잔량10 [%s]" % (recvvalue[13], recvvalue[33]))



if __name__ == "__main__":

    # 여기는 korea invest 객체를 생성하는 것
    import yaml
    from utils import KoreaInvestEnv, KoreaInvestAPI

    # 절대경로: c:\HilbertTech\Live Trading\config.yaml
    # 상대경로: ./config.yaml
    with open("c:/HilbertTech/Live Trading/config.yaml", encoding = 'UTF-8') as f:
        cfg = yaml.load(f, Loader = yaml.FullLoader)
    
    env_cls = KoreaInvestEnv(cfg)
    base_headers = env_cls.get_base_headers()
    cfg = env_cls.get_full_config()
    korea_invest_api = KoreaInvestAPI(cfg, base_headers = base_headers)


    websocket_url = cfg['websocket_url']    # websocket url을 cfg에서 가져온다
    run_websocket(korea_invest_api, websocket_url)  # 웹소켓을 실시한다