from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "admin"
PASSWORD = "73@TuGraph"

driver = GraphDatabase.driver(URI,auth=(USER,PASSWORD))


print("开始导入")
with driver.session(database = 'finance') as session:
    session.run('''CALL db.createVertexLabel(
    'Executive', 'id', 
    'id', 'string', false, 
    'name', 'string', false, 
    'gender', 'string', true, 
    'age', 'int32', true
)''')
    session.run('''
    CALL db.createVertexLabel(
    'Stock', 'id', 
    'id', 'int64', false, 
    'name', 'string', false, 
    'code', 'string', false
)
    ''')
    session.run('''
    CALL db.createVertexLabel(
    'Concept', 'id', 
    'id', 'string', false, 
    'name', 'string', false
)
    ''')
    session.run('''
    CALL db.createVertexLabel(
    'Industry', 'id', 
    'id', 'string', false, 
    'name', 'string', false
)
    ''')
    session.run('''
    CALL db.createEdgeLabel(
    'EMPLOY_OF', 
    '[["Executive", "Stock"]]', 
    'jobs', 'string', true
)
    ''')
    session.run('''
    CALL db.createEdgeLabel(
    'CONCEPT_OF', 
    '[["Stock", "Concept"]]'
)
    ''')
    session.run('''
    CALL db.createEdgeLabel(
    'INDUSTRY_OF', 
    '[["Stock", "Industry"]]'
)
    ''')
    print("全部导入成功")