import fitz  # PyMuPDF
import pandas as pd
import re
from neo4j import GraphDatabase
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ✅ 1. PDF에서 손익계산서/재무상태표 텍스트 추출
def extract_pages_by_keywords(pdf_path, keywords):
    doc = fitz.open(pdf_path)
    result = {}
    for page in doc:
        text = page.get_text()
        for kw in keywords:
            if kw in text:
                result[kw] = text
    return result

def extract_financial_numbers(text):
    lines = text.split("\n")
    data = {}

    for i, line in enumerate(lines):
        clean_line = line.strip()

        if "매출총이익" in clean_line:
            key = "매출총이익"
        elif "영업이익" in clean_line:
            key = "영업이익"
        elif "매출액" in clean_line:
            key = "매출"
        else:
            continue

        # 숫자는
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            numbers = re.findall(r"[\d,]+", next_line)
            if numbers:
                value = int(numbers[0].replace(",", ""))
                data[key] = value
                print(f"✅ 추출 성공: {key} → {value}")
            else:
                print(f"⚠️ 숫자 추출 실패: {key}")
        else:
            print(f"❌ 다음 줄 없음: {line}")

    return data





# ✅ 3. ML 학습
def train_model(df):
    X = df.drop("Success", axis=1)
    y = df["Success"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=200)
    model.fit(X_train, y_train)
    acc = accuracy_score(y_test, model.predict(X_test))
    joblib.dump(model, "investment_model.pkl")
    print(f"\n✅ 모델 저장 완료 (정확도: {acc:.2f})")

# ✅ 4. Neo4j 저장
def save_to_neo4j(company, year, data_dict, result):
    data_dict.setdefault("매출", 0)
    data_dict.setdefault("영업이익", 0)
    data_dict.setdefault("매출총이익", 0)

    driver = GraphDatabase.driver("neo4j+s://1c51267f.databases.neo4j.io", auth=("neo4j", "pAX5v1Wv4wof83koZS2RsWQFcsjG42Q51g9QKcBpfes"))
    with driver.session() as session:
        session.run("""
            MERGE (c:Company {name: $company})
            MERGE (y:Year {value: $year})
            MERGE (c)-[:HAS_YEAR]->(y)
            MERGE (f:Financials {매출: $매출, 영업이익: $영업이익, 매출총이익: $매출총이익})
            MERGE (y)-[:HAS_FINANCIAL]->(f)
            MERGE (p:Prediction {result: $result}) 
            MERGE (y)-[:HAS_RESULT]->(p)
        """, company=company, year=year, result=result, **data_dict)
    driver.close()

# ✅ 5. 전체 실행 흐름
def main():
    pdf_path = "[삼성전자]사업보고서(2025.03.11).pdf"
    sections = extract_pages_by_keywords(pdf_path, ["연결 손익계산서", "연결 재무상태표"])
    print("\n📄 추출된 페이지 요약:", list(sections.keys()))

    data = extract_financial_numbers(sections.get("연결 손익계산서", ""))
    print("\n📊 추출된 재무 데이터:", data)

    # ✅ 학습용 예시 DataFrame 구성
    df = pd.DataFrame([
        {"매출": 200_000_000, "영업이익": 30_000_000, "매출총이익": 25_000_000, "Success": 1},
        {"매출": 180_000_000, "영업이익": 15_000_000, "매출총이익": 10_000_000, "Success": 0},
        {"매출": data.get("매출", 0), "영업이익": data.get("영업이익", 0), "매출총이익": data.get("매출총이익", 0), "Success": 1},
    ])

    train_model(df)

    # ✅ 모델 예측
    model = joblib.load("investment_model.pkl")
    pred = model.predict(df.drop("Success", axis=1))[-1]
    result = "성공" if pred == 1 else "실패"

    # ✅ 온톨로지 저장
    save_to_neo4j("삼성전자", 2023, data, result)
    print(f"\n🧠 온톨로지 저장 완료 — 예측 결과: {result}")

if __name__ == "__main__":
    main()
