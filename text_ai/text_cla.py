import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1" # <-- 이 줄을 추가!

import pandas as pd
import torch
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
import pandas as pd
import json
import glob # 여러 파일 경로를 한 번에 가져오기 위한 라이브러리

# --- 1. 파일 경로 설정 ---
# 사용하시는 폴더 경로에 맞게 수정하세요.
train_json_files = glob.glob(r'./02/*.json')
validate_json_files = glob.glob(r'./Validation/02/*.json')

# --- 2. 여러 JSON 파일을 읽어 하나의 DataFrame으로 만드는 함수 ---
def create_dataframe_from_json(file_paths):
    """
    주어진 경로의 모든 JSON 파일을 읽어,
    [대화문, 라벨] 형태의 Pandas DataFrame으로 만들어 반환합니다.
    """
    training_data = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            conversation = json.load(f)
        
        utterances = conversation['utterances']
        # 이전 코드와 동일한 로직으로 화자/청자 대화를 짝지어 줍니다.
        for i in range(len(utterances) - 1):
            if utterances[i]['role'] == 'speaker' and utterances[i+1]['role'] == 'listener':
                speaker_text = utterances[i]['text']
                # listener_empathy가 있으면 해당 라벨을, 없으면 '중립' 라벨을 부여
                if utterances[i+1]['listener_empathy']:
                    label = utterances[i+1]['listener_empathy'][0]
                else:
                    label = '중립' # 새로운 라벨 부여

                training_data.append([speaker_text, label])
                    
    return pd.DataFrame(training_data, columns=['text', 'label'])

# --- 3. 함수를 이용해 train / validate 데이터프레임 생성 ---
train_df = create_dataframe_from_json(train_json_files)
validate_df = create_dataframe_from_json(validate_json_files)

print(f"훈련 데이터 개수: {len(train_df)}")
print(f"검증 데이터 개수: {len(validate_df)}")
print("\n--- 훈련 데이터 샘플 ---")
print(train_df.head())
print("\n--- 검증 데이터 샘플 ---")
print(validate_df.head())
# [3단계] ... train_df, validate_df 생성 후
print("\n--- 훈련 데이터 라벨 분포 확인 ---")
print(validate_df['label'].value_counts())

# --- 4. 라벨을 숫자로 변환 (Label Encoding) ---
# 훈련 데이터에 있는 모든 라벨을 기준으로 사전을 만듭니다.
labels = train_df['label'].unique().tolist()
label_to_id = {label: i for i, label in enumerate(labels)}
id_to_label = {i: label for i, label in enumerate(labels)}

# train_df와 validate_df 모두에 동일한 규칙을 적용합니다.
train_df['label_id'] = train_df['label'].map(label_to_id)
validate_df['label_id'] = validate_df['label'].map(label_to_id)
# =================================================================
# 1단계: 데이터 로드
# =================================================================

num_labels = len(labels)
print(f"총 라벨 개수: {num_labels}")
print(f"라벨 종류: {labels}")
print(f"라벨 -> ID 맵핑: {label_to_id}")


# =================================================================
# 3단계: 모델 및 토크나이저 준비
# =================================================================
print("\n✅ 3단계: 모델 및 토크나이저를 준비합니다.")
#MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
MODEL_NAME = "klue/roberta-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels)


# =================================================================
# 4단계: 데이터셋 클래스 및 토큰화
# =================================================================
print("\n✅ 4단계: 파이토치 데이터셋을 생성합니다.")
# 텍스트를 토큰화
train_encodings = tokenizer(list(train_df['text']), truncation=True, padding=True, max_length=128)
val_encodings = tokenizer(list(validate_df['text']), truncation=True, padding=True, max_length=128)

# 파이토치 데이터셋 클래스 정의
class EmpathyDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

# 데이터셋 객체 생성
train_dataset = EmpathyDataset(train_encodings, list(train_df['label_id']))
val_dataset = EmpathyDataset(val_encodings, list(validate_df['label_id']))


# =================================================================
# 5단계: 성능 지표 계산 함수 정의
# =================================================================
print("\n✅ 5단계: 성능 지표 계산 함수를 정의합니다.")
def compute_metrics(p):
    pred, labels = p
    pred = np.argmax(pred, axis=1)
    
    accuracy = accuracy_score(y_true=labels, y_pred=pred)
    f1 = f1_score(y_true=labels, y_pred=pred, average='weighted')
    
    return {"accuracy": accuracy, "f1": f1}


# =================================================================
# 6단계: 훈련 인자 설정 및 Trainer 생성
# =================================================================
print("\n✅ 6단계: 훈련 인자를 설정합니다.")
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3, # 훈련 에폭 수 (전체 데이터를 몇 번 학습할지)
    per_device_train_batch_size=32, # 한 번에 처리할 훈련 데이터 양
    per_device_eval_batch_size=32, # 한 번에 처리할 검증 데이터 양
    logging_dir='./logs',
    logging_steps=50,
    evaluation_strategy="epoch", # 매 에폭마다 성능 측정
    save_strategy="epoch",
    learning_rate=1e-5,       # 매 에폭마다 모델 저장
    load_best_model_at_end=True, # 훈련 종료 후 가장 좋은 모델을 불러옴
    metric_for_best_model="f1",  # 최고 모델 선정 기준
    save_total_limit=1,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)] # <-- 조기 종료 콜백 추
)


# =================================================================
# 7단계: 모델 훈련
# =================================================================
print("\n✅ 7단계: 모델 훈련을 시작합니다. (시간이 다소 소요될 수 있습니다)")
trainer.train()


# =================================================================
# 8단계: 모델 최종 평가
# =================================================================
print("\n✅ 8단계: 훈련된 모델의 최종 성능을 평가합니다.")
final_metrics = trainer.evaluate()
print("--- 최종 성능 평가 결과 ---")
for key, value in final_metrics.items():
    print(f"{key}: {value:.4f}")


# =================================================================
# 9단계: 훈련된 모델로 예측하기
# =================================================================
print("\n✅ 9단계: 새로운 문장으로 예측을 테스트합니다.")
# 가장 성능이 좋았던 모델을 불러옵니다.
best_model_path = trainer.state.best_model_checkpoint
best_model = AutoModelForSequenceClassification.from_pretrained(best_model_path)

def predict_empathy(text):
    """
    새로운 문장을 입력받아 필요한 공감 반응을 예측하는 함수
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    
    # GPU 사용이 가능하다면 입력을 GPU로 보냄
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    best_model.to(device) # 모델도 동일한 장치로 이동
    
    with torch.no_grad():
        outputs = best_model(**inputs)
        
    predicted_class_id = outputs.logits.argmax().item()
    return id_to_label[predicted_class_id]

# 테스트 문장
text1 = "오늘 직장 상사한테 너무 심하게 혼나서 기운이 하나도 없어."
text2 = "나 다음 주부터 새로운 운동 시작해볼까 하는데, 뭘 하면 좋을까?"
text3 = "네 덕분에 프로젝트 잘 마쳤어. 정말 고마워!"

print(f"입력 문장: '{text1}'")
print(f"예측 결과: '{predict_empathy(text1)}'\n")

print(f"입력 문장: '{text2}'")
print(f"예측 결과: '{predict_empathy(text2)}'\n")

print(f"입력 문장: '{text3}'")
print(f"예측 결과: '{predict_empathy(text3)}'\n")

print("🎉 모든 과정이 완료되었습니다!")
print("\n✅ 10단계: 최고 성능 모델을 별도 폴더에 저장합니다.")

# "my_best_model" 이라는 이름의 폴더에 최고 성능 모델을 저장합니다.
trainer.save_model("my_best_5_model")
