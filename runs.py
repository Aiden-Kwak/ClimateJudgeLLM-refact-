import os
from controller.main_controller import MainController

if __name__ == "__main__":
    # 환경 변수 로드 및 경로 설정
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = os.getenv("DATA_FOLDER", os.path.join(BASE_DIR, "rscFiles"))

    # 컨트롤러 실행
    controller = MainController()
    claim = os.getenv("CLAIM", "지구 온난화는 기후 모델이 예측한 만큼 진행되지 않고 있다. 이는 식물의 광합성이 예상보다 더 많은 CO2를 흡수하고 있기 때문이다. 기후 변화는 거짓말이다.")
    controller.run(claim, DATA_FOLDER)