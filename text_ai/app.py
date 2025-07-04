from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
from typing import List
import json

app = FastAPI(
    title="Text Empathy Classification API",
    description="텍스트 공감 유형을 분류하는 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 경로 설정
script_directory = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(script_directory, "my_best_model")

# 라벨 정보
id_to_label = {
    0: '격려',
    1: '위로',
    2: '동조',
    3: '조언'
}

# 채팅방 관리를 위한 클래스
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# 모델 클래스들
class TextRequest(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    text: str
    prediction: str

# 모델과 토크나이저 로드
try:
    tokenizer = AutoTokenizer.from_pretrained("seunghyunq/text-classification-model")
    model = AutoModelForSequenceClassification.from_pretrained("seunghyunq/text-classification-model")
    model.eval()
    print("✅ 모델 로드 성공!")
except Exception as e:
    print(f"🚨 모델 로드 중 오류 발생: {e}")
    raise Exception("모델 로드 실패")

def get_prediction(text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    predicted_class_id = outputs.logits.argmax().item()
    return id_to_label.get(predicted_class_id, "알 수 없는 라벨")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                text = message_data.get('text', '')
                
                # 메시지 분류 수행
                prediction = get_prediction(text)
                
                # 응답 메시지 구성
                response_message = {
                    "text": text,
                    "prediction": prediction
                }
                
                # 모든 연결된 클라이언트에게 브로드캐스트
                await manager.broadcast(response_message)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Text Empathy Classification API is running"} 