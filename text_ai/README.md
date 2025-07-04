# Text AI Project

이 프로젝트는 텍스트 분류/예측을 위한 AI 모델을 구현합니다.

## 설치 방법

```bash
pip install -r requirements.txt
```

## 모델 정보

이 프로젝트는 Hugging Face Hub에 호스팅된 모델을 사용합니다.
모델 주소: https://huggingface.co/seunghyunq/text-classification-model

### 모델 사용 방법

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# 모델과 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained("seunghyunq/text-classification-model")
model = AutoModelForSequenceClassification.from_pretrained("seunghyunq/text-classification-model")
```

## 실행 방법

1. 웹 인터페이스 실행:

```bash
python app.py
```

2. 텍스트 예측:

```bash
python text_predict.py
```

## 주의사항

- 첫 실행 시 모델이 자동으로 다운로드됩니다.
- 인터넷 연결이 필요합니다.
