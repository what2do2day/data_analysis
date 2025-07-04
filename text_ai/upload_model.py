from transformers import AutoModelForSequenceClassification, AutoTokenizer

# 로컬 모델 로드
model = AutoModelForSequenceClassification.from_pretrained("my_best_model")
tokenizer = AutoTokenizer.from_pretrained("my_best_model")

# Hugging Face Hub에 업로드 (organization-name과 model-name을 실제 값으로 변경하세요)
repo_id = "organization-name/model-name"
model.push_to_hub(repo_id)
tokenizer.push_to_hub(repo_id) 