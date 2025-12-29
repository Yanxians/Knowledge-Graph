from neo4j import GraphDatabase

# 自定义一个类来管理连接
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None, db=None):
        with self.driver.session(database=db) as session:
            result = session.run(query, parameters)
            return list(result)
        
    def run(self, query, parameters=None, db="kanye"):
        return self.query(query, parameters, db)
    
    def create(self, node, db = None):
        label = node.labels
        properties = {key: value for key, value in node.items()}
        property_string = ', '.join([f"{key}: ${key}" for key in properties])
        query = f"CREATE (n:{label} {{{property_string}}})"
        self.query(query, properties, db)
    
    def merge(self,node):
        label = node.labels
        properties = {key: value for key, value in node.items()}
        property_string = ', '.join([f"{key}: ${key}" for key in properties])
        query = f"MERGE (n:{label} {{{property_string}}})"
        self.query(query, properties)
        
    def counts(self):
        records  = self.query("MATCH (n) RETURN count(n)")
        count = records[0][0]
        return count
    
    def relationship(self, start_node, end_node, edges, rel_type, rel_name, db = None):
        # 去重处理
        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge))
        all = len(set(set_edges))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = edge[0]
            q = edge[1]
            query = "match(p:%s),(q:%s) where p.name='%s' and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)
            try:
                self.query(query,None,db = db)
            except Exception as e:
                print(e)
        return
    
    def clear(self):
        query = "MATCH (n) DETACH DELETE n"
        self.query(query)

# 定义节点对象 
class Node:
    def __init__(self, labels, **properties):
        self.labels = labels
        self.properties = properties

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __delitem__(self, key):
        del self.properties[key]

    def __iter__(self):
        return iter(self.properties)

    def __len__(self):
        return len(self.properties)

    def items(self):
        return self.properties.items()