from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase
import openai
import os

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

driver = GraphDatabase.driver("neo4j+s://1c51267f.databases.neo4j.io", auth=("neo4j", "pAX5v1Wv4wof83koZS2RsWQFcsjG42Q51g9QKcBpfes"))


class QuestionInput(BaseModel):
    company: str
    year: int
    question: str


@app.post("/ask")
def ask_question(q: QuestionInput):
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {name: $company})-[:HAS_YEAR]->(y:Year {value: $year})-[:HAS_FINANCIAL]->(f),
                  (y)-[:HAS_RESULT]->(p)
            RETURN f.매출 AS 매출, f.영업이익 AS 영업이익, f.매출총이익 AS 매출총이익, p.result AS result
        """, company=q.company, year=q.year)
        record = result.single()
        if not record:
            return {"answer": "해당 회사의 데이터가 없습니다."}

        data = record.data()

    # GPT에게 질문 + 근거 정보 전달
    prompt = f"""
    사용자의 질문: \"{q.question}\"
    기업 이름: {q.company}, 연도: {q.year}
    📊 재무정보:
    - 매출: {data['매출']:,}원
    - 영업이익: {data['영업이익']:,}원
    - 매출총이익: {data['매출총이익']:,}원
    🔮 예측 결과: {data['result']}

    위 정보를 기반으로 투자자에게 자연스럽고 신뢰 있게 답변해줘.
    """
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "넌 투자 어드바이저야."},
            {"role": "user", "content": prompt}
        ]
    )

    return {"answer": gpt_response.choices[0].message.content}
