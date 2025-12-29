import pandas as pd
import re
from neo4j_driver import Neo4jConnection, Node


conn = Neo4jConnection(uri='bolt://127.0.0.1:7687/', user='admin', password='73@TuGraph')

class GraphBuilder:
    def __init__(self, conn):
        self.conn = conn
        self.data_path =  "C:\\Users\\yanran\\Downloads\\QASystemOnMedicalKG-main\\作业三\\data\\results.csv"
    def read_file(self):
        """
        读取文件，获得实体，实体关系
        :return:
        """
        # cols = ["name", "alias", "part", "age", "infection", "insurance", "department", "checklist", "symptom",
        #         "complication", "treatment", "drug", "period", "rate", "money"]
        # 实体
        diseases = []  # 疾病
        aliases = []  # 别名
        symptoms = []  # 症状
        departments = []  # 科室
        drugs = []  # 药品
        # 关系
        disease_to_symptom = []  # 疾病与症状关系
        disease_to_alias = []  # 疾病与别名关系
        disease_to_department = []  # 疾病与科室关系
        disease_to_drug = []  # 疾病与药品关系

        all_data = pd.read_csv(self.data_path, encoding='utf-8').loc[:, :].values
        for data in all_data:
            disease_dict = {}  # 疾病信息
            # 疾病
            disease = str(data[1]).replace("...", " ").strip()
            diseases.append(disease)  # 添加到疾病列表
            disease_dict["name"] = disease
            # 别名
            line = re.sub("[，、；,.;]", " ", str(data[5])) if str(data[5]) else "未知"
            for alias in line.strip().split():
                aliases.append(alias)
                disease_to_alias.append([disease, alias])
            # 科室
            department_list = str(data[4]).strip().split()
            for department in department_list:
                departments.append(department)
                disease_to_department.append([disease, department])
            # 症状
            symptom_list = str(data[2]).replace("...", " ").strip().split()[:-1]
            for symptom in symptom_list:
                symptoms.append(symptom)
                disease_to_symptom.append([disease, symptom])
            # 药品
            drug_string = str(data[3]).replace("...", " ").strip()
            for drug in drug_string.split()[:-1]:
                drugs.append(drug)
                disease_to_drug.append([disease, drug])

        return set(diseases), set(symptoms), set(aliases), set(departments), \
               set(drugs), disease_to_alias, disease_to_symptom, disease_to_department, \
                disease_to_drug


    def create_nodes(self, type, sets):
        print(f'创建{type}节点')
        for i in sets:
            node = Node(type,name = i)
            self.conn.create(node, db = 'kanye')

    def create_relationships(self, disease_to_alias, disease_to_symptom, 
                            disease_to_department,disease_to_drug):
        print("开始创建关系...")
        
        # 创建疾病-别名关系
        print(f"创建疾病-别名关系，共 {len(disease_to_alias)} 条...")
        self.conn.relationship("Disease", "Alias", disease_to_alias, "ALIAS", "别名", "kanye")
        
        # 创建疾病-症状关系
        print(f"创建疾病-症状关系，共 {len(disease_to_symptom)} 条...")
        self.conn.relationship("Disease", "Symptom", disease_to_symptom, "HAS_SYMPTOM", "症状", "kanye")
        
        # 创建疾病-科室关系
        print(f"创建疾病-科室关系，共 {len(disease_to_department)} 条...")
        self.conn.relationship("Disease", "Department", disease_to_department, "BELONGS_TO", "科室", "kanye")
        
        # 创建疾病-药品关系
        print(f"创建疾病-药品关系，共 {len(disease_to_drug)} 条...")
        self.conn.relationship("Disease", "Drug", disease_to_drug, "TREATS_WITH", "药品","kanye")
        
        print("所有关系创建完成！")

    def close(self):
        """
        关闭图数据库连接
        """
        self.conn.close()
        print("图数据库连接已关闭")


# 示例用法
if __name__ == "__main__":
    conn = Neo4jConnection(uri='bolt://localhost:7687/', user='admin', password='73@TuGraph')
    # 创建GraphBuilder实例
    builder = GraphBuilder(conn)
    db = 'kanye'

    diseases, symptoms, aliases,departments, drugs,\
    disease_to_alias, disease_to_symptom, disease_to_department, \
    disease_to_drug = builder.read_file()


#     # 构造schema,仅第一次运行需要
#     schemas_v = []
#     schema_disease = """
# CALL db.createVertexLabel(
#     'Disease', 'name', 
#     'name', 'string', false
# )
# """
#     schemas_v.append(schema_disease)
#     schema_aliases = """
#     CALL db.createVertexLabel(
#     'Alias', 'name', 
#     'name', 'string', false)
#     """
#     schemas_v.append(schema_aliases)
#     schema_symptoms = """
# CALL db.createVertexLabel(
#     'Symptom', 'name', 
#     'name', 'string', false)
# """
#     schemas_v.append(schema_symptoms)


#     schema_departments = """
# CALL db.createVertexLabel(
#     'Department', 'name', 
#     'name', 'string', false)
# """
#     schemas_v.append(schema_departments)


#     schema_drugs = """
# CALL db.createVertexLabel(
#     'Drug', 'name', 
#     'name', 'string', false)
# """
#     schemas_v.append(schema_drugs)
#     for sql in schemas_v:
#         builder.conn.run(sql)

#     builder.conn.query("CALL db.createEdgeLabel('ALIAS', '[[\"Disease\",\"Alias\"]]', 'name', 'string', true)", db='kanye')
#     builder.conn.query("CALL db.createEdgeLabel('HAS_SYMPTOM', '[[\"Disease\",\"Symptom\"]]', 'name', 'string', true)", db='kanye')
#     builder.conn.query("CALL db.createEdgeLabel('BELONGS_TO', '[[\"Disease\",\"Department\"]]', 'name', 'string', true)", db='kanye')
#     builder.conn.query("CALL db.createEdgeLabel('TREATS_WITH', '[[\"Disease\",\"Drug\"]]', 'name', 'string', true)", db='kanye')



    builder.create_nodes("Disease", diseases)
    builder.create_nodes("Symptom", symptoms)
    builder.create_nodes("Alias", aliases)
    builder.create_nodes("Department", departments)
    builder.create_nodes("Drug", drugs)
    builder.create_relationships(disease_to_alias, disease_to_symptom, 
                                 disease_to_department, disease_to_drug)

    builder.close()