
class KiwoomBasicPrice:


    def request_opt10001_basic_info(self, code):
        # Set input values and request opt10001 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10001_req", "opt10001", 0, "0101")

    def request_opt10002_detail_info(self, code):
        # Set input values and request opt10002 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10002_req", "opt10002", 0, "0102")

    def request_opt10003_price_history(self, code):
        # Set input values and request opt10003 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10003_req", "opt10003", 0, "0103")

    def request_opt10004_volume_info(self, code):
        # Set input values and request opt10004 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10004_req", "opt10004", 0, "0104")

    def request_opt10005_account_status(self):
        # Request opt10005 data
        self.comm_rq_data("opt10005_req", "opt10005", 0, "0105")

    def request_opt10006_buy_sell_info(self, code):
        # Set input values and request opt10006 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10006_req", "opt10006", 0, "0106")

    def request_opt10007_other_data(self, code):
        # Set input values and request opt10007 data
        self.set_input_value("종목코드", code)
        self.comm_rq_data("opt10007_req", "opt10007", 0, "0107")

# ...existing code...
