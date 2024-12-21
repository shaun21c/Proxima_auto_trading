import time
from loguru import logger
import json
from param import output
from regex import B
import requests
import copy
from collections import namedtuple
import pandas as pd


class KoreaInvestAPI:
    def __init__(self, cfg, base_headers):
        self.custtype = cfg['custtype']
        self._base_headers = base_headers
        self.websocket_approval_key = cfg['websocket_approval_key']
        self.account_num = cfg['account_num']
        self.is_paper_trading = cfg['is_paper_trading']
        self.htsid = cfg['htsid']
        self.using_url = cfg['using_url']
        # self.personalseckey = cfg['personalseckey'] 법인 고객 식별키

    def set_order_hash_key(self, h, p):
        #주문 API에서 사용할 hash key값을 받아 header에 설정해 주는 함수
        # Input: HTTP Header, Http post paran
        # Output: None
        url = f"{self.using_url}/uapi/hashkey"

        res = requests.post(url, data = json.dump(p), headers = h)
        rescode = res.status_code       #status_code: 응답의 HTTP 상태 코드를 확인합니다. 200: 성공적인 응답.
        if rescode == 200:
            h['hashkey'] = res.json()['HASH']       #성공적으로 해시 키를 받아오면, 헤더(h)에 해시 키를 추가합니다
        else:
            logger.info(f"Error: {rescode}")        #실패 시, 응답 코드(rescode)를 로그에 기록합니다

    def _url_fetch(self, api_url, tr_id, params, is_post_request = False, use_hash=True):       #이 함수 **_url_fetch**는 API 요청을 보내는 함수로, GET 또는 POST 방식으로 API 서버에 요청을 전송하고 응답을 처리하는 역할을 합니다. 
                                                                                                # 이 함수는 요청 방식, 헤더 설정, 해시 키 추가, 에러 처리 등 여러 기능을 처리합니다.
                                                                                                # is_post_request: POST 요청을 할지 여부를 결정합니다. 기본값은 False로 설정되어 있으므로 GET 요청이 기본입니다.
                                                                                                # use_hash: 해시 키를 사용할지 여부를 결정합니다. 기본값은 True로 설정되어 있습니다.
        try:
            url = f'{self.using_url}{api_url}'
            headers = self._base_headers        # headers: 기본 헤더인 self._base_headers를 복사하여 사용합니다. 추가적으로, tr_id와 custtype을 헤더에 추가합니다. 
                                                # base_headers는 KoreaInvestAPI 클래스에 init 내부 정의됨. 

            headers["tr_id"] = tr_id            # 거래 ID
            headers["custtype"] = self.custtype # 고객 종류

            # is_post_request가 True이면, POST 요청을 보냅니다.
            # **use_hash**가 True이면, set_order_hash_key()를 호출하여 해시 키를 헤더에 추가합니다.
            if is_post_request:
                if use_hash:
                    self.set_order_hash_key(headers, params)
                res = requests.post(url, headers = headers, data = json.dumps(params))
            else:
                res = requests.get(url, headers = headers, params = params)     # is_post_request가 False일 때는 GET 요청을 보냅니다. 파라미터는 URL 쿼리 스트링으로 전달됩니다.


            # 응답 코드가 200(성공)이면 APIResponse 객체로 변환하여 반환합니다.
            # 실패 시, 응답 코드와 에러 메시지를 로그에 남기고 None을 반환합니다.
            if res.status_code == 200:  # 정상작동
                ar = APIResponse(res)
                return ar
            else:
                logger.info(f"Error Code : {res.status_code} | {res.text}")
                return None

        except Exception as e:
            logger.info(f'URL exception: {e}')    


    ### 주식 정보 받아오기
    def get_current_price(self, stock_no): #종목코드를 입력을 받는다
        url = '/uapi/domestic-stock/v1/quotations/inquire-price'
        tr_id = "FHKST01010100"

        # 쿼리 파라미터
        # FID_COND_MRKT_DIV_CODE: 시장 구분 코드입니다. 'J'는 KOSPI 시장을 의미합니다. 다른 코드로는 KOSDAQ, 기타 시장 등이 있을 수 있습니다.
        # FID_INPUT_ISCD: 조회하고자 하는 종목 코드입니다. stock_no를 받아 주식 종목 코드를 API에 전달합니다.
        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_no
        }

        # _url_fetch: 이 함수는 앞서 설명한 API 호출 함수로, url, tr_id, params를 사용하여 GET 요청을 보내고 API 서버에서 응답을 받아옵니다.
        # 응답을 받아 **t1**에 저장합니다.
        t1 = self._url_fetch(url, tr_id, params)

        # t1이 None이 아니고, 정상 응답(성공적인 응답)을 받은 경우, t1.get_body().output을 반환합니다.
        # t1.get_body().output: 응답 본문에서 주식의 가격 정보를 추출하여 반환합니다.
        if t1 is not None and t1.is_ok():
            return t1.get_body().output
        elif t1 is None:
            return dict()   # t1이 None인 경우(즉, 응답을 받지 못한 경우), 빈 딕셔너리를 반환합니다.
        else:
            t1.print_error()
            return dict()       # 요청이 실패한 경우, t1.print_error()로 에러 메시지를 출력하고, 빈 딕셔너리를 반환합니다.

    def get_hoga_info(self, stock_no):
        url = '/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn'
        tr_id = 'FHKST01010200'

        # 쿼리 파라미터
        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_no
        }

        t1 = self._url_fetch(url, tr_id, params)

        if t1 is not None and t1.is_ok():
            return t1.get_body().output1
        elif t1 is None:
            return dict()
        else:
            t1.print_error()
            return dict()
        
    def get_fluctuation_ranking(self):                                      # 주식 시장에서 **변동성 순위(상승 또는 하락률 순위)**를 조회하여, 특정 정보를 반환하는 역할을 합니다. 
                                                                            # 변동성 순위는 종목별 가격 변동률을 기반으로 순위를 매긴 데이터를 제공합니다. 
                                                                            # 이 함수는 API 호출을 통해 변동성 순위 데이터를 받아서, 특정 열을 선택해 반환합니다.
        url = '/uapi/domestic-stock/v1/ranking/fluctuation'
        tr_id = 'FHPST01700000'
        
        params = {
            "fid_cond_mrkt_div_code":"J",           # "fid_cond_mrkt_div_code":"J": 시장 구분 코드, 'J'는 KOSPI 시장을 의미합니다.
            "fid_cond_scr_div_code":"20170",        # "fid_cond_scr_div_code":"20170": 화면 구분 코드로, 변동성 순위 조회를 나타냅니다.
            "fid_input_iscd":"0000",                # "fid_input_iscd":"0000": 종목 코드. 여기서는 전체 종목을 대상으로 조회.
            "fid_rank_sort_cls_code":"0",           # 그 외 파라미터는 순위 정렬, 가격 범위, 거래량 조건 등을 설정합니다.
            "fid_input_cnt_1":"0",
            "fid_prc_cls_code":"0",
            "fid_input_price_1":"",
            "fid_input_price_2":"",
            "fid_vol_cnt":"",
            "fid_trgt_cls_code":"0",
            "fid_trgt_exls_cls_code":"0",
            "fid_div_cls_code":"0",
            "fid_rsfl_rate1":"",
            "fid_rsfl_rate2":""
        }

        t1 = self._url_fetch(url, tr_id, params)

        if t1 is not None and t1.is_ok():                       #API 응답 데이터 중에서, 필요한 열만 선택합니다.
                                                                    #target_columns: 필요한 데이터 열을 정의합니다. 여기서는:
                                                                    # stck_shrn_iscd: 종목 코드.
                                                                    # stck_prpr: 현재가 (현재 주식 가격).
                                                                    # prdy_ctrt: 전일 대비 비율.
                                                                    # output_columns: 데이터를 보다 이해하기 쉽게 한글로 열 이름을 변경합니다.
            df = pd.DataFrame(t1.get_body(), output)
            target_columns = ['stck_shrn_iscd', 'stck_prpr', 'prdy_ctrt']
            output_columns = ['종목코드', '현재가', '전일대비율']
            df = df[target_columns]

            # 열 이름 변경: target_columns와 output_columns를 매핑하여, 데이터프레임의 열 이름을 한글로 변경합니다.
            # 결과 반환: 최종적으로 가공된 데이터프레임을 반환합니다.
            column_name_map = dict(zip(target_columns, output_columns))
            return df.rename(columns = column_name_map)
        elif t1 is None:
            return dict()
        else:
            t1.print_error()
            return dict()


    
    ### 국장 잔고 정보 받아오기
    # 이 함수 **get_acct_balance**는 사용자의 계좌 잔고 및 종목별 보유 자산 정보를 조회하는 API 호출 함수입니다. 
    # 이를 통해 계좌에 있는 주식의 보유수량, 매입단가, 수익률, 현재가 등의 정보를 DataFrame으로 반환하고, 계좌 총 평가금액을 반환합니다
    def get_acct_balance(self):
        url = '/uapi/domestic-stock/v1/trading/inquire-balance'
        tr_id = 'TTTC8434R'
        #계좌 잔고 평가 잔고의 상세 내열을 DataFrame으로 반환

        params = {
            "CANO": self.account_num,       # CANO: 계좌 번호. self.account_num으로 사용자의 계좌 번호를 전달합니다.
            "ACNT_PRDT_CD": "01",           # 계좌의 상품 코드. "01"은 기본 주식 계좌를 의미합니다.
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""

        }

        t1 = self._url_fetch(url, tr_id, params)

        # output_columns: 반환할 데이터프레임의 **열 이름(컬럼명)**을 정의합니다. 한글로 표시된 주식 코드, 종목명, 보유 수량, 매입 단가, 수익률 등의 정보를 담고 있습니다.
        output_columns = ['종목코드', '종목명', '보유수량', '매도가능수량', '매입단가', '수익률', '현재가', '전일대비', '전일대비 등략률']

        if t1 is None:
            return 0, pd.DataFrame(columns = output_columns)
        
        try: 
            output1 = t1.get_body().output1
        except Exception as e:
            logger.info(f'Exception: {e}, t1: {t1}')
            return 0, pd.DataFrame(column = output_columns)
        

        # target_columns: API 응답에서 선택할 열의 이름을 정의합니다. 이 열에는 종목 코드, 종목명, 보유 수량, 매입 단가, 수익률 등의 데이터가 포함됩니다.
        if t1 is not None and t1.is_ok() and output1:
            df = pd.DataFrame(output1)
            target_columns = {
                'pdno',
                'prdt_name',
                "trad_dvsn_name",
                "bfdy_buy_qty",
                "bfdy_sll_qty",
                "thdt_buyqty",
                "thdt_sll_qty",
                "hldg_qty",
                "ord_psbl_qty",
                "pchs_avg_pric",
                "pchs_amt",
                "prpr",
                "evlu_amt",
                "evlu_pfls_amt",
                "evlu_pfls_rt",
                "evlu_erng_rt",
                "loan_dt",
                "loan_amt",
                "stln_slng_chgs",
                "expd_dt",
                "fltt_rt",
                "bfdy_cprs_icdc",
                "item_mgna_rt_name",
                "grta_rt_name",
                "sbst_pric",
                "stck_loan_unpr"
            }

            df = df[target_columns]
            df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric)

            # 열 이름 변경: API에서 제공하는 열 이름을 한국어 열 이름으로 바꿔서 사용자가 쉽게 이해할 수 있도록 합니다.
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename(column = column_name_map, inplace = True)

            # 보유 수량이 0인 종목 제거: 보유하지 않은 종목은 제거합니다.
            df = df[df['보유수량'] != 0]

            # r2: API 응답에서 계좌의 총 평가 금액을 가져옵니다.
            # 총 평가 금액과 DataFrame을 반환합니다.
            r2 = t1.get_body().output2
            return int(r2[B]['tot_evlu_amt']), df
        
        else:
            logger.info(f't1.is_ok(): {t1.is_ok()}, output1: {output1}')
            tot_evlu_amt = 3
            
            if t1.is_ok():
                r2 = t1.get_body().output2
                tot_evlu_amt = int(r2[0]['tot_evlu_ant'])
            return tot_evlu_amt

    ### 국장 주문하기
    def do_order(self, stock_code, order_qty, order_price, prd_code = '01', buy_flag = True, order_type = '00'):
        url = '/uapi/domestic-stock/v1/trading/order-cash'

        if buy_flag:
            tr_id = 'TTTC0802U' # buy
            
        else:
            tr_id = 'TTTC0801U' # sell

        params = {
            "CANO": self.account_num,
            "ACNT_PRDT_CD": prd_code,
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(order_qty),
            "ORD_UNPR": str(order_price),
            "CTAC_TLNO": '',
            "SLL_TYPE": '01',
            "ALGO NO": ''
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request = True, use_hash = True)

        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None

    def do_buy(self, stock_code, order_qty, order_price, order_type = '00'):
        t1 = self.do_order(stock_code, order_qty, order_price, buy_flag = True, order_type = order_type)
        return t1
    
    def do_sell(self, stock_code, order_qty, order_price, order_type = '00'):
        t1 = self.do_order(stock_code, order_qty, order_price, buy_flag = False, order_type = order_type)
        return t1


    ### 국장 주문 조회 및 수정하기
    def get_orders(self, prd_code = '01') -> pd. DataFrame:

        url = '/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
        tr_id = 'TTTC8036R'

        params = {
            "ACNT_PRDT_CD": prd_code,
            "CANO": self.account_num,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0"
        }

        t1 = self._url_fetch(url, tr_id, params)
        if t1 is not None and t1.is_ok() and t1.get_body().output:
            tdf = pd.DataFrame(t1.get_body().output)
            tdf.set_index('odno', inplace = True)
            cf1 = ['pdno', 'ord_qty', 'ord_unpr', 'urd_trd', 'urd_gno_brno', 'orgn_odno', 'psbl_qty']
            cf2 = ['종목코드', '주문수량', '주문가격', '시간', '주문점', '원주문번호', '주문가능수량']
            tdf = tdf[cf1]
            ren_dict = dict(zip(cf1, cf2))

            return tdf.rename(columns = ren_dict)
        else:
            return None
        
    def _do_cancel_revise(self, order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn):
        # 특정 주문 취소(01)/정정(02)
        # Input: 주문 번호(get_orders 를 호출하여 얻은 DataFrame 의 index column 값이 취소 가능한 주문번호)
        
        # 주문점(통상 06010), 주문수량, 주문가격, 상품코드(01), 주문유형(00), 정정구분(취소 = 02, 정정 = 01)
        # Output: APIResponse Object

        url = '/uapi/domestic-stock/v1/trading/order-rvsecncl'
        tr_id = 'TTTC0803U'

        params = {
            "CANO": self.account_num,
            "ACNT_PRDT_CD": prd_code,
            "KRX_FWDG_ORD_ORGNO": order_branch,
            "ORGN_ODNO": order_no,
            "ORD_DVSN": order_dv,
            "RVSE_CNCL_DVSN_CD": cncl_dv,   # 취소(02)
            "ORD_QTY": str(order_qty),
            "ORD_UNPR": str(order_price),
            "QTY_ALL_ORD_YN": qty_all_yn
        }

        t1 = self._url_fetch(url, tr_id, params = params, is_post_request = True)

        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None

    def do_cancel(self, order_no, order_qty, order_price = '01', order_branch = '36018', prd_code = '01', order_dv = '00', cncl_dv = '02', qty_all_yn = 'Y'):
        return self._do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)

    def do_revise(self, order_no, order_qty, order_price, order_branch = '36018', prd_code = '01', order_dv = '00', cncl_dv = '01', qty_all_yn = 'Y'):
        return self._do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)

    def do_cancel_all(self, skip_codes = []):
        tdf = self.get_orders()
        if tdf is not None:
            od_list = tdf.index.to_list()
            qty_list = tdf['주문수당'].to_list()
            price_list = tdf['주문가격'].to_list()
            branch_list = tdf['주문점'].to_list()
            codes_list = tdf['종목코드'].to_list()

            cnt = 0

            for x in od_list:
                if codes_list[cnt] in skip_codes:
                    continue
                ar = self.do_cancel(x, qty_list[cnt], price_list[cnt], branch_list[cnt])
                cnt += 1
                logger.info(f"get_error_code: {ar.get_error_code()}, get_error_message: {ar.get_error_message()}")
                time.sleep(0.02)        #혹시라도 너무많은 tr 요청이 들어갈 시를 위한 것




    ### 미장 잔고 정보 받아오기
    def get_overseas_acct_balance(self):
        #계좌 잔고를 평가잔고와 상세 내열을 DataFrame으로 반환
        url = '/uapi/overseas-stock/v1/trading/inquire-balance'
        tr_id = 'TTTS3012R'

        params = {
            "CANO": self.account_num,
            "ACNT_PRDT_CD":"01",
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        t1 = self._url_fetch(url, tr_id, params)
        output_columns = ['종목코드', '해외거래소코드', '종목명', '보유수량', '매도가능수량', '매입단가', '수익률', '현재가', '평가손익']

        if t1 is None:
            return 0, pd.DataFrame(columns = output_columns)
        
        try: 
            output1 = t1.get_body().output1
        except Exception as e:
            logger.info(f'Exception: {e}, t1: {t1}')
            return 0, pd.DataFrame(column = output_columns)
        

        if t1 is not None and t1.is_ok() and output1:
            df = pd.DataFrame(output1)
            target_columns = ["ovrs_pdno", "ovrs_excg_cd", "ovrs_item_name", 'ord_psb1_qty', 'pchs_avg_pric', 'evlu_pfls_rt', 'now_pric2', 'frcr_evlu_pfls_ant']
            df = df[target_columns]
            df[target_columns[3:]] = df[target_columns[3:].apply(pd.to_numeric)]
            column_name_map = dict(zip(target_columns, output_columns))
            df.rename(columns = column_name_map, inplace = True)
            df = df[df['보유수량'] != 0]
            r2 = t1.get_body().output2
            return float(r2['tot_evlu_pfls_ant']), df
        
        else:
            return 0, pd.DataFrame(columns = ['종목코드', '해외거래소코드', '종목명', '보유수량', '매도가능수량', '매입단가', '수익률', '현재가', '평가손익'])

    ### 미장 주문하기
    def overseas_do_order(self, stock_code, exchange_code, order_qty, order_price, prd_code = '01', buy_flag = True, order_type = '00'):
        url = '/uapi/overseas-stock/v1/trading/order'


        if buy_flag:
            tr_id = 'TTTT1002U' # 미국 매수주문

        else:
            tr_id = 'TTTT1006U' # 미국 매도 주문

        params = {
            
            "CANO": self.account_num,
            "ACNT_PRDT_CD": prd_code,
            "OVRS_EXCG_CD": exchange_code,
            "PDNO": stock_code,
            "ORD_QTY": str(order_qty),
            "OVRS_ORD_UNPR": str(order_price),
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": order_type,
        }

        t1 = self._url_fetch(url, tr_id, params, is_post_request = True, use_hash = True)

        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None

    def overseas_do_buy(self, stock_code, exchange_code, order_qty, order_price, prd_code = '01', order_type = '00'):
        t1 = self.overseas_do_order(
            stock_code,
            exchange_code,
            order_qty,
            order_price,
            prd_code = prd_code,
            buy_flag = True,
            order_type = order_type,
        )
        return t1

    def overseas_do_sell(self, stock_code, exchange_code, order_qty, order_price, prd_code = '01', order_type = '00'):
        t1 = self.overseas_do_order(
            stock_code,
            exchange_code,
            order_qty,
            order_price,
            prd_code = prd_code,
            buy_flag = False,
            order_type = order_type,
        )
        return t1


    ### 미장 주문 조회 및 수정하기
    def get_overseas_orders(self, prd_code = '0', exchange_code  = "") -> pd.DataFrame:
        url = '/uapi/overseas-stock/v1/trading/inquire-nccs'
        tr_id = 'TTTS3018R'

        params = {
            "ACNT_PRDT_CD": prd_code,
            "CANO": self.account_num,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "OVRS_EXCG_CD": exchange_code,
            "SORT_SQN": "DS"
        }

        t1 = self._url_fetch(url, tr_id, params)
        if t1 is not None and t1.is_ok() and t1.get_body().output:
            tdf = pd.DataFrame(t1.get_body().output)
            tdf.set_index('odno', inplace = True)
            cf1 = ['pdno', 'ft_ord_qty', 'ft_ord_unpr3', 'ord_tmd', 'ovrs_excg_cd', 'orgn_odno', 'nccs_qty', 'sll_buy_dvsn_cd', 'sll_buy_dvsn_cd_name']
            cf2 = ['종목코드', '주문수량', '주문가격', '시간', '거래소코드', '원주문번호', '주문가능수량', '매도매수구분코드', '매도매수구분코드명']
            tdf = tdf[cf1]
            ren_dict = dict(zip(cf1, cf2))

            return tdf.rename(columns = ren_dict)
        else:
            return None

    def _overseas_do_cancel_revise(self, order_no, stock_code, order_branch, order_qty, order_price, prd_code, cncl_dv):
        # 특정 주문 취소(01)/정정(02)
        # Input: 주문 번호(get_orders 를 호출하여 얻은 DataFrame 의 index comun 같이 취소 가능한 주문번호)
                # 주문점(통상 06010), 주문수량, 주문가격, 상품코드(01), 주문유형(00), 정정구분(취소 = 02, 정정 = 01)
        # Output: APIResponse Object

        url = '/uapi/overseas-stock/v1/trading/order-rvsecncl'
        tr_id = 'TTTT1004U'

        params = {
            "CANO": self.account_num,
            "ACNT_PRDT_CD": prd_code,
            "OVRS_EXCG_CD": order_branch,
            "PDNO": stock_code,
            "ORGN_ODNO": order_no,
            "ORD_SVR_DVSN_CD": "0",
            "RVSE_CNCL_DVSN_CD": cncl_dv,   # 취소(02)
            "ORD_QTY": str(order_qty),
            "OVRS_ORD_UNPR": str(order_price),
        }

        t1 = self._url_fetch(url, tr_id, params = params, is_post_request = True)

        if t1 is not None and t1.is_ok():
            return t1
        elif t1 is None:
            return None
        else:
            t1.print_error()
            return None
    
    def overseas_do_cancel(self, order_no, stock_code, order_qty, order_price = '0', order_branch = '36018', prd_code = '01', cncl_dv = '02'):
        return self._overseas_do_cancel_revise(order_no, stock_code, order_branch, order_qty, order_price, prd_code, cncl_dv)

    def overseas_do_revise(self, order_no, stock_code, order_qty, order_price = '0', order_branch = '36018', prd_code = '01', cncl_dv = '01'):
        return self._overseas_do_cancel_revise(order_no, stock_code, order_branch, order_qty, order_price, prd_code, cncl_dv)

    def overseas_do_cancel_all(self, skip_codes = []):
        tdf = self.get_overseas_orders()
        if tdf is not None:
            od_list = tdf.index.to_list()
            qty_list = tdf['주문수당'].to_list()
            price_list = tdf['주문가격'].to_list()            
            exchange_list = tdf['거래소코드'].to_list()
            codes_list = tdf['종목코드'].to_list()
            cnt = 0

            for x in od_list:
                if codes_list[cnt] in skip_codes:
                    continue
                ar = self.overseas_do_cancel(x, codes_list[cnt], qty_list[cnt], price_list[cnt], exchange_list[cnt])
                cnt += 1
                logger.info(f"get_error_code: {ar.get_error_code()}, get_error_message: {ar.get_error_message()}")
                time.sleep(0.02)        #혹시라도 너무많은 tr 요청이 들어갈 시를 위한 것
        

    # 웹소켓
    def get_send_data(self, cmd = None, stockcode = None):
        # 1.주식호가, 2.주식호가해제, 3.주식체결, 4.주식체결해제, 5.주식체결통보(고객), 6.주식체결통보해제(고객), 7.주식체결통보(모의), 8.주식체결통보해제(모의)
        # 입력란 체크 step
        assert 0 < cmd < 9, f"Wrong Input Data: {cmd}"

        # 입력값에 따라 데이터셋 구분 처리
        if cmd == 1: # 주식호가 등록
            tr_id = 'H0STASP0'
            tr_type = '1'
        elif cmd == 2: # 주식호가 등록해제
            tr_id = 'H0STASP0'
            tr_type = '2'
        elif cmd == 3: # 주식체결 등록
            tr_id = 'H0STCNT0'
            tr_type = '1'
        elif cmd == 4: # 주식체결 등록해제
            tr_id = 'H0STCNT0'
            tr_type = '2'
        elif cmd == 5: # 주식체결통보 등록(고객용)
            tr_id = 'H0STCNI0'
            tr_type = '2'
        elif cmd == 6: # 주식체결통보 등록해제(고객용)
            tr_id = 'H0STCNI0'
            tr_type = '2'
        elif cmd == 7: # 주식체결통보 등록(모의)
            tr_id = 'H0STCNI9' # 테스트용 직원체결통보
            tr_type = '1'
        elif cmd == 8: # 주식레결통보 등록해제(모의)
            tr_id = 'HOSTCNI9' # 테스트용 직원체결통보
            tr_type = '2'

        
        #send json, 체결통보는 tr_key 입력항목이 상이하므로 분리를 한다
        if cmd in (5, 6, 7, 8):
            senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + self.htsid + '"}}}'
            
            # 고객식별키 포함
            # senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","personalseckey":"' + self.personalseckey + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + self.htsid + '"}}}'
        
        else:

            senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + stockcode + '"}}}'

            # 고객식별키 포함
            # senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","personalseckey":"' + self.personalseckey + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + stockcode + '"}}}'
        
        return senddata
    

    def overseas_get_send_data(self, cmd = None, stockcode = None):
        # 1.주식호가, 2.주식호가해제, 3.주식체결, 4.주식체결해제, 5.주식체결통보(고객), 6.주식체결통보해제(고객), 7.주식체결통보(모의), 8.주식체결통보해제(모의)
        # 입력란 체크 step
        assert 0 < cmd < 9, f"Wrong Input Data: {cmd}"

        # 입력값에 따라 데이터셋 구분 처리
        if cmd == 1: # 주식호가 등록
            tr_id = 'HDFSASP0'
            tr_type = '1'
        elif cmd == 2: # 주식호가 등록해제
            tr_id = 'HDFSASP0'
            tr_type = '2'
        elif cmd == 3: # 주식체결 등록
            tr_id = 'HDFSCNT0'
            tr_type = '1'
        elif cmd == 4: # 주식체결 등록해제
            tr_id = 'HDFSCNT0'
            tr_type = '2'
        elif cmd == 5: # 주식체결통보 등록(고객용)
            tr_id = 'H0GSCNI0'
            tr_type = '2'
        elif cmd == 6: # 주식체결통보 등록해제(고객용)
            tr_id = 'H0GSCNI0'
            tr_type = '2'


        
        #send json, 체결통보는 tr_key 입력항목이 상이하므로 분리를 한다
        if cmd in (5, 6, 7, 8):
            senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + self.htsid + '"}}}'
        else:
            senddata = '{"header":{"approval_key":"' + self.websocket_approval_key + '","custtype":"' + self.custtype + '","tr_type":"' + tr_type + '","content_type":"utf-8", "body":"input":{"tr_id":"' + tr_id + '", "tr_key":"' + stockcode + '"}}}'
        return senddata


    def get_approval(self, key, secret):
        # 웹소켓 접속키 발급
        url = 'https://openapi.koreainvestment.com:9443'
        headers = {"content-type": "application/json"}
        body = {"grant_type": "client_credentials",
                "appkey": key,
                "secretkey": secret}
        PATH = "oauth2/Approval"
        URL = f"{url}/{PATH}"
        res = requests.post(URL, headers = headers, data = json.dumps(body))
        approval_key = res.json()["approval_key"]
        return approval_key


        

#Base Headers와 Config를 완성해주는 객체
class KoreaInvestEnv:
    def __init__(self, cfg):

        self.cfg = cfg      # cfg 딕셔너리를 저장.
        self.custtype = cfg['custtype']

        # **self.base_headers**는 API 요청 시 사용할 기본 HTTP 헤더를 설정합니다. 얘는 다른 호출양식에도 기본적으로 들어가는 것들.
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "user-Agent": cfg["my_agent"],
        }

        #cfg에서 받아온 정보를 변수에 저장
        using_url = cfg['url']
        api_key = cfg["api_key"]
        api_secret_key = cfg["api_secret_key"]
        account_num = cfg["stock_account_number"]

        websocket_approval_key = self.get_websocket_approval_key(using_url, api_key, api_secret_key)    #발급받은 웹소켓 접근권한 저장
        account_access_token = self.get_account_access_token(using_url, api_key, api_secret_key)        #발급받은 접근토큰 저장
        
        #base header에 추가
        self.base_headers["authorization"] = account_access_token       # 접근토큰을 발급받아야 한다.
        self.base_headers["appkey"] = api_key
        self.base_headers["appsecret"] = api_secret_key

        #cfg 딕셔너리에 추가
        self.cfg['websocket_approval_key'] = websocket_approval_key
        self.cfg['account_num'] = account_num
        self.cfg['using_url'] = using_url

    # deepcopy는 원래 데이터의 복사본을 반환하여, 복사본을 수정해도 원본 데이터에는 영향을 주지 않도록 해줍니다

    # deepcopy(self.base_headers): 깊은 복사를 사용하여 base_headers의 복사본을 반환합니다. 이 복사본은 원본과 독립적으로, 반환된 값을 수정하더라도 **원본 base_headers**에는 영향을 미치지 않습니다.
    def get_base_headers(self):
        return copy.deepcopy(self.base_headers)

    # deepcopy(self.cfg): 마찬가지로 깊은 복사를 사용하여 cfg의 복사본을 반환합니다. 반환된 복사본은 원본 cfg와 독립적이므로, 복사본을 수정하더라도 **원본 cfg**에는 영향을 미치지 않습니다.
    def get_full_config(self):
        return copy.deepcopy(self.cfg)

    #계좌에 접근 가능한 토큰 발급하는 함수
    def get_account_access_token(self, request_base_url='', api_key = '', api_secret_key = ''):  
        # request_base_url: 한국투자증권 API의 기본 URL입니다. API에 접근할 서버 주소를 입력받습니다.
        # api_key: 한국투자증권에서 발급한 앱 키(API 접근을 위한 인증 정보)입니다.
        # api_secret_key: 한국투자증권에서 발급한 시크릿 키(API 인증을 위한 비밀 키)입니다.


        #한국투자증권 api 접근토큰 발급을 위한 Body 형식
        # grant_type: OAuth2 인증에서 사용되는 방식으로, 클라이언트의 인증 정보를 제공하여 토큰을 발급받는 방식입니다.
        p = {
            "grant_type": "client_credentials",
            "appkey": api_key,
            "appsecret": api_secret_key,
        }

        # url: 한국투자증권 API의 토큰 발급 엔드포인트를 정의합니다. request_base_url은 기본 URL이며, 여기에 /oauth2/tokenP 경로를 덧붙여서 최종적인 API 요청 URL을 생성합니다.
        url = f'{request_base_url}/oauth2/tokenP'

        # requests.post(): Python의 requests 라이브러리를 사용해 POST 요청을 보냅니다.
        # url: 앞서 생성한 URL로 요청을 보냅니다.
        # data = json.dumps(p): 요청 데이터 p를 JSON 형식으로 변환하여 전송합니다.
        # headers: HTTP 요청의 헤더입니다. 이 헤더는 클래스 내의 다른 메서드나 속성에서 정의된 것으로 보이며, 요청 시 Content-Type 등을 지정하는 데 사용됩니다.
        res = requests.post(url, data = json.dumps(p), headers = self.base_headers)

        #res.raise_for_status(): 요청이 성공적으로 완료되지 않으면 **예외(Exception)**를 발생시킵니다.
        #HTTP 상태 코드가 200번대(성공)가 아닐 경우, 예외가 발생하고 프로그램이 멈추므로 에러를 쉽게 디버깅할 수 있습니다.
        res.raise_for_status()

        #res.json(): API 응답 데이터를 JSON 형식으로 변환합니다.
        #res.json()['access_token']: 응답 JSON 데이터에서 access_token 필드를 추출합니다. 이 **access_token**이 API에 접근할 때 필요한 인증 토큰입니다.
        my_token = res.json()['access_token']

        #발급받은 **access_token**을 Bearer라는 접두사와 함께 반환합니다. API 요청 시, Authorization 헤더에 Bearer <토큰> 형식으로 넣어 인증을 수행하게 됩니다.
        return f"Bearer {my_token}"

    #웹소켓 접속키 발급하는 함수
    def get_websocket_approval_key(self, requests_base_url = '', api_key='', api_secret_key=''):
        # request_base_url: 한국투자증권 API의 기본 URL입니다. API에 접근할 서버 주소를 입력받습니다.
        # api_key: 한국투자증권에서 발급한 앱 키(API 접근을 위한 인증 정보)입니다.
        # api_secret_key: 한국투자증권에서 발급한 시크릿 키(API 인증을 위한 비밀 키)입니다.

        # 여기서 "content-type": "application/json"은 요청 본문이 JSON 형식임을 명시하는 헤더입니다. 즉, 서버에 보낼 데이터가 JSON으로 인코딩되어 있다는 것을 알립니다.
        headers = {"content-type": "application/json"}

        # grant_type: OAuth2 인증에서 사용되는 방식으로, 클라이언트의 인증 정보를 제공하여 토큰을 발급받는 방식입니다.
        body = {
            "grant_type": "client_credentials",
            "appkey": api_key,
            "secretkey": api_secret_key,
        }

        # url: 한국투자증권 API의 토큰 발급 엔드포인트를 정의합니다. request_base_url은 기본 URL이며, 여기에 /oauth2/tokenP 경로를 덧붙여서 최종적인 API 요청 URL을 생성합니다.
        URL = f"{requests_base_url}/oauth2/Approval"

        # requests.post(): Python의 requests 라이브러리를 사용해 POST 요청을 보냅니다.
        # url: 앞서 생성한 URL로 요청을 보냅니다.
        # data = json.dumps(p): 요청 데이터 p를 JSON 형식으로 변환하여 전송합니다.
        # headers: HTTP 요청의 헤더입니다. 이 헤더는 클래스 내의 다른 메서드나 속성에서 정의된 것으로 보이며, 요청 시 Content-Type 등을 지정하는 데 사용됩니다.
        res = requests.post(URL, headers = headers, data = json.dumps(body))
        #print(res.json())
        # res.json(): API 서버의 응답을 JSON 형식으로 파싱합니다.
        # 응답 데이터에서 approval_key 필드를 추출합니다. 이 승인 키는 웹소켓 서버에 연결할 때 인증으로 사용됩니다.
        approval_key = res.json()["approval_key"]

        # 추출된 **승인 키(approval_key)**를 반환합니다. 이 키는 이후 웹소켓 서버에 연결할 때 인증 토큰으로 사용됩니다.
        return approval_key
    

#Api Response가 200이면 보통 성공이지만 가끔 이상한 데이터를 보내기 때문에 그 것까지 확인하기 위한 객체
class APIResponse:  
    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        self._header = self._set_header()
        self._body = self._set_body()
        self._err_code = self._body.rt_cd
        self._err_message = self._body.msg1

    def get_result_code(self):
        return self._rescode
    
    def _set_header(self):
        fld = dict()
        for x in self._resp.headers.keys():
            if x.islower():
                fld[x] = self._resp.headers.get(x)
        
        _th_ = namedtuple('header', fld.keys())
        return _th_(**fld)
    
    def _set_body(self):
        _tb_ = namedtuple('body', self._resp.json().keys())
        return _tb_(**self._resp.json())
    
    def get_header(self):
        return self._header
    
    def get_body(self):
        return self._body
    
    def get_response(self):
        return self._resp
    
    def is_ok(self):
        try:
            if (self.get_body().rt_cd == '0'):
                return True
            else:
                return False
        
        except:
            return False
        
    def get_error_code(self):
        return self._err_code
    
    def get_error_message(self):
        return self._err_message
    
    def print_all(self):
        logger.info("<Header>")
        for x in self.get_header()._fields:
            logger.info(f"\t*{x}: {getattr(self.get_header(), x)}")
        logger.info("<Body>")
        for x in self.get_body()._fields:
            logger.info(f"\t*{x}: {getattr(self.get_body(), x)}")

    def print_error(self):
        logger.info(f'------------------------')
        logger.info(f'Error in response: {self.get_result_code()}')
        logger.info(f'{self.get_body().rt_cd}, {self.get_error_code()}, {self.get_error_message()}')
        logger.info(f'------------------------')

