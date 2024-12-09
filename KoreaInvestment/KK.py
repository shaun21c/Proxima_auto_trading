import yaml

from utils import KoreaInvestEnv, KoreaInvestAPI


def main():
    with open("c:/HilbertTech/Live Trading/config.yaml", encoding = 'UTF-8') as f:
        cfg = yaml.load(f, Loader = yaml.FullLoader)        #config 파일을 dictionary 형태로 불러오고 있다
    env_cls = KoreaInvestEnv(cfg)                           #Header을 만들어준다.
    base_headers = env_cls.get_base_headers()               #형성된 헤더에서 base header 추출
    cfg = env_cls.get_full_config()                         #형성된 헤더에서 cfg 추출

    #환경 생성
    korea_invest_api = KoreaInvestAPI(cfg, base_headers = base_headers)
    print(korea_invest_api)


if __name__ == "__main__":
    main()

    