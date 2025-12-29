from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
import os
from langchain_core.prompts import ChatPromptTemplate
import re
from neo4j import GraphDatabase

os.environ["OPENAI_API_KEY"] = "sk-2HwJCZPfaG9EA7UcySdd44bUFsftmRiTrAaF8FlmtCjtl99H"

# 手动指定schema，避免APOC依赖问题
schema = """
节点类型：
- Disease: 疾病节点，具有name属性
- Symptom: 症状节点，具有name属性
- Alias: 别名节点，具有name属性
- Department: 科室节点，具有name属性
- Drug: 药品节点，具有name属性

关系类型：
- (Disease)-[:ALIAS]->(Alias): 疾病的别名
- (Disease)-[:HAS_SYMPTOM]->(Symptom): 疾病的症状
- (Disease)-[:BELONGS_TO]->(Department): 疾病所属科室
- (Disease)-[:TREATS_WITH]->(Drug): 疾病的治疗药品
"""

def neo4j_answer(query):

    graph = Neo4jGraph(
    url="bolt://localhost:7687", 
    username="neo4j", 
    password="neo4jnb."
)


    chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(model="gpt-3.5-turbo",temperature=0.1,base_url="https://api.chatanywhere.tech"),
    graph=graph,
    allow_dangerous_requests=True, 
    verbose=False)
    
    response = chain.invoke({"query": query})
    print("最终回答：", response['result'])

#neo4j_answer("糖尿病有什么症状")

def tugraph_answer(query):

    URI = "bolt://localhost:7687"
    USER = "admin"
    PASSWORD = "73@TuGraph"

    SCHEMA_TEXT = """
节点类型：
- Disease: 疾病节点，具有name属性
- Symptom: 症状节点，具有name属性
- Alias: 别名节点，具有name属性
- Department: 科室节点，具有name属性
- Drug: 药品节点，具有name属性

关系类型：
- (Disease)-[:ALIAS]->(Alias): 疾病的别名
- (Disease)-[:HAS_SYMPTOM]->(Symptom): 疾病的症状
- (Disease)-[:BELONGS_TO]->(Department): 疾病所属科室
- (Disease)-[:TREATS_WITH]->(Drug): 疾病的治疗药品
"""

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    # 2. 准备 Prompt，让 GPT 生成 Cypher
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature=0.1,
        base_url="https://api.chatanywhere.tech"
    )
    
    prompt = ChatPromptTemplate.from_template("""
    你是一个图数据库专家。请根据下面的数据库结构(Schema)，将用户的自然语言问题转换为标准的 Cypher 查询语句。
    
    注意：
    1. 只返回 Cypher 语句，不要包含 ```cypher ... ``` 标记，也不要包含任何解释。
    2. 确保关系名称和属性名称完全匹配 Schema。
    3. TuGraph 暂时不支持复杂的事务，请生成简单的查询。
    
    数据库结构 Schema:
    {schema}
    
    用户问题: {question}
    """)
    
    # 3. 获取 GPT 生成的 Cypher
    chain = prompt | llm
    response = chain.invoke({"schema": SCHEMA_TEXT, "question": query})
    cypher_query = response.content.strip()
    
    # 清理一下可能的 markdown 符号
    cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
    
    
    # 4. 执行查询 (关键：直接用 session.run 避开事务报错)
    results = []
    try:
        with driver.session(database = 'kanye') as session:
            # TuGraph 只需要 run，不需要 begin_transaction
            result_cursor = session.run(cypher_query)
            results = [record.data() for record in result_cursor]
            
    except Exception as e:
        print(f"--> 查询执行出错: {e}")
        driver.close()
        return

    driver.close()

    if not results:
        print("最终回答：抱歉，数据库中没有找到相关信息。")
    else:
        # 这一步是让 GPT 把数据组织成人类语言
        summary_prompt = ChatPromptTemplate.from_template("""
        用户问: {question}
        数据库查到的数据是: {data}
        请根据数据简洁地回答用户问题。
        """)
        summary_chain = summary_prompt | llm
        final_answer = summary_chain.invoke({"question": query, "data": str(results)})
        print("最终回答：", final_answer.content)

# 运行
tugraph_answer("糖尿病可以吃什么药物")

tugraph_answer("感冒了应该去哪挂号？")