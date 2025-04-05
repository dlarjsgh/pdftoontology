import joblib
import pandas as pd

model = joblib.load("ml/investment_model.pkl")

# Dummy GPT-based explanation generator
def predict_success(financials: dict, news: str):
    df = pd.DataFrame([financials])
    prediction = model.predict(df)[0]
    explanation = "기반 재무지표와 긍정적 뉴스로 인해 투자 성공 확률이 높습니다."
    return ("성공" if prediction == 1 else "실패", explanation)
