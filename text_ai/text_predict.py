import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os 

# =================================================================
# 1. 로컬에 저장된 모델 및 토크나이저 불러오기 (최종 해결 버전)
# =================================================================
print("✅ 로컬 모델을 불러옵니다...")

try:
    # 현재 이 스크립트 파일(__file__)이 있는 폴더의 절대 경로를 가져옵니다.
    script_directory = os.path.dirname(os.path.abspath(__file__))
    
    # 그 폴더 안에 있는 'my_best_model'의 전체 경로를 만듭니다.
    MODEL_PATH = os.path.join(script_directory, "my_best_model")

    # 디버깅을 위해, 파이썬이 실제로 어떤 경로를 찾고 있는지 직접 출력해봅니다.
    print(f"모델을 다음 경로에서 찾습니다: {MODEL_PATH}")

    # 해당 경로에 폴더가 실제로 존재하는지 다시 한번 확인합니다.
    if not os.path.isdir(MODEL_PATH):
        raise FileNotFoundError(f"오류: 계산된 경로에 '{MODEL_PATH}' 폴더가 존재하지 않습니다. 폴더 위치를 다시 확인해주세요.")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    print("✅ 모델 로드 성공!")

except Exception as e:
    # 어떤 오류든 상세하게 출력해줍니다.
    print(f"🚨 모델 로드 중 오류 발생: {e}")
    exit()


# --- 아래 코드는 이전과 동일합니다 ---

# 라벨 정보 (훈련 시 사용했던 라벨과 순서가 같아야 함)
id_to_label = {
    0: '격려',
    1: '위로',
    2: '동조',
    3: '조언'
}

# =================================================================
# 2. 예측 함수 정의
# =================================================================
def predict_empathy(text):
    device = torch.device("cpu")
    model.to(device)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    predicted_class_id = outputs.logits.argmax().item()
    return id_to_label.get(predicted_class_id, "알 수 없는 라벨")

# =================================================================
# 3. 사용자 입력받아 무한 테스트
# =================================================================
print("\n🎉 테스트 준비 완료! 문장을 입력하고 Enter를 누르세요.")
print("   (종료하려면 'exit' 또는 '종료'를 입력하세요)")

while True:
    user_input = input("입력 > ")
    if user_input.lower() in ["exit", "종료"]:
        print("테스트를 종료합니다.")
        break
    prediction = predict_empathy(user_input)
    print(f"예측 결과: '{prediction}'\n")
