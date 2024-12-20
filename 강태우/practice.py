from pykiwoom.kiwoom import Kiwoom

# Kiwoom 인스턴스 생성
kiwoom = Kiwoom()

# 키움증권 Open API 로그인 시도
kiwoom.CommConnect(block=True)

# 로그인 상태 확인
if kiwoom.GetConnectState() == 1:
    print("로그인 성공!")
    # 사용자 정보 출력
    user_id = kiwoom.GetLoginInfo("USER_ID")
    accounts = kiwoom.GetLoginInfo("ACCNO")  # 여러 계좌가 있을 경우 리스트로 반환
    print("사용자 ID:", user_id)
    print("계좌번호:", accounts)
else:
    print("로그인 실패")
