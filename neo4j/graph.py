from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

def save_prediction_graph(company, year, financials, result, ontology_data):
    with driver.session() as session:
        session.run("""
            MERGE (c:Company {name: $company})
            MERGE (y:Year {value: $year})
            MERGE (c)-[:HAS_YEAR]->(y)
            MERGE (r:Result {value: $result})
            MERGE (y)-[:HAS_RESULT]->(r)
        """, company=company, year=year, result=result)
        # Add financials & ontology as needed...