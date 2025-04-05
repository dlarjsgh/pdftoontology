from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from neo4j import GraphDatabase

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class UserQuestion(BaseModel):
    company: str
    year: int
    question: str

@app.post("/ask")
def ask_investment(q: UserQuestion):
    # 1. Neo4j에서 관련 재무 정보 조회
    driver = GraphDatabase.driver("neo4j+s://1c51267f.databases.neo4j.io", auth=("neo4j", "pAX5v1Wv4wof83koZS2RsWQFcsjG42Q51g9QKcBpfes"))
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year {value: $year})-[:HAS_FINANCIAL]->(f),
                  (y)-[:HAS_RESULT]->(p)
            RETURN f.매출 AS 매출, f.영업이익 AS 영업이익, f.매출총이익 AS 매출총이익, p.result AS result
        """, company=q.company, year=q.year)
        row = result.single()
        financials = row.data()

    # 2. GPT에게 질문과 재무 정보 전달
    prompt = f"""
    사용자가 "{q.question}" 이라고 물었습니다.
    다음은 해당 기업의 재무 정보입니다:

    - 매출: {financials['매출']:,}원
    - 영업이익: {financials['영업이익']:,}원
    - 매출총이익: {financials['매출총이익']:,}원
    - 예측 결과: {financials['result']}

    이 정보를 기반으로 자연스럽고 설득력 있게 답변해줘.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "넌 투자 어드바이저야."},
            {"role": "user", "content": prompt}
        ]
    )

    return {"answer": response.choices[0].message.content}
