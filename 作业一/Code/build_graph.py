import pandas as pd
import re
from neo4j_driver import Neo4jConnection, Node


conn = Neo4jConnection(uri='neo4j://localhost:7687/', user='neo4j', password='neo4jnb.')

class GraphBuilder:
    def __init__(self, conn):
        self.conn = conn
        self.data_path =  "C:\\Users\\yanran\\Downloads\\QASystemOnMedicalKG-main\\医疗知识图谱\\data\\disease.csv"
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
        parts = []  # 部位
        departments = []  # 科室
        complications = []  # 并发症
        drugs = []  # 药品

        # 疾病的属性：age, infection, insurance, checklist, treatment, period, rate, money
        diseases_infos = []
        # 关系
        disease_to_symptom = []  # 疾病与症状关系
        disease_to_alias = []  # 疾病与别名关系
        diseases_to_part = []  # 疾病与部位关系
        disease_to_department = []  # 疾病与科室关系
        disease_to_complication = []  # 疾病与并发症关系
        disease_to_drug = []  # 疾病与药品关系

        all_data = pd.read_csv(self.data_path, encoding='gb18030').loc[:, :].values
        for data in all_data:
            disease_dict = {}  # 疾病信息
            # 疾病
            disease = str(data[0]).replace("...", " ").strip()
            diseases.append(disease)  # 添加到疾病列表
            disease_dict["name"] = disease
            # 别名
            line = re.sub("[，、；,.;]", " ", str(data[1])) if str(data[1]) else "未知"
            for alias in line.strip().split():
                aliases.append(alias)
                disease_to_alias.append([disease, alias])
            # 部位
            part_list = str(data[2]).strip().split() if str(data[2]) else "未知"
            for part in part_list:
                parts.append(part)
                diseases_to_part.append([disease, part])
            # 年龄
            age = str(data[3]).strip()
            disease_dict["age"] = age
            # 传染性
            infect = str(data[4]).strip()
            disease_dict["infection"] = infect
            # 医保
            insurance = str(data[5]).strip()
            disease_dict["insurance"] = insurance
            # 科室
            department_list = str(data[6]).strip().split()
            for department in department_list:
                departments.append(department)
                disease_to_department.append([disease, department])
            # 检查项
            check = str(data[7]).strip()
            disease_dict["checklist"] = check
            # 症状
            symptom_list = str(data[8]).replace("...", " ").strip().split()[:-1]
            for symptom in symptom_list:
                symptoms.append(symptom)
                disease_to_symptom.append([disease, symptom])
            # 并发症
            complication_list = str(data[9]).strip().split()[:-1] if str(data[9]) else "未知"
            for complication in complication_list:
                complications.append(complication)
                disease_to_complication.append([disease, complication])
            # 治疗方法
            treat = str(data[10]).strip()[:-4]
            disease_dict["treatment"] = treat
            # 药品
            drug_string = str(data[11]).replace("...", " ").strip()
            for drug in drug_string.split()[:-1]:
                drugs.append(drug)
                disease_to_drug.append([disease, drug])
            # 治愈周期
            period = str(data[12]).strip()
            disease_dict["period"] = period
            # 治愈率
            rate = str(data[13]).strip()
            disease_dict["rate"] = rate
            # 费用
            money = str(data[14]).strip() if str(data[14]) else "未知"
            disease_dict["money"] = money

            diseases_infos.append(disease_dict)

        return set(diseases), set(symptoms), set(aliases), set(parts), set(departments), set(complications), \
               set(drugs), disease_to_alias, disease_to_symptom, diseases_to_part, disease_to_department, \
               disease_to_complication, disease_to_drug, diseases_infos

    def create_disease_node(self, diseases):
        print('创建疾病节点')
        for disease in diseases:
            node = Node("Disease", **disease)
            self.conn.create(node)


    def create_nodes(self, type, sets):
        print(f'创建{type}节点')
        for i in sets:
            node = Node(type,name = i)
            self.conn.create(node)

    def create_relationships(self, disease_to_alias, disease_to_symptom, diseases_to_part, 
                            disease_to_department, disease_to_complication, disease_to_drug):
        """
        创建所有关系
        """
        print("开始创建关系...")
        
        # 创建疾病-别名关系
        print(f"创建疾病-别名关系，共 {len(disease_to_alias)} 条...")
        self.conn.relationship("Disease", "Alias", disease_to_alias, "ALIAS", "别名")
        
        # 创建疾病-症状关系
        print(f"创建疾病-症状关系，共 {len(disease_to_symptom)} 条...")
        self.conn.relationship("Disease", "Symptom", disease_to_symptom, "HAS_SYMPTOM", "症状")
        
        # 创建疾病-部位关系
        print(f"创建疾病-部位关系，共 {len(diseases_to_part)} 条...")
        self.conn.relationship("Disease", "Part", diseases_to_part, "LOCATED_IN", "部位")
        
        # 创建疾病-科室关系
        print(f"创建疾病-科室关系，共 {len(disease_to_department)} 条...")
        self.conn.relationship("Disease", "Department", disease_to_department, "BELONGS_TO", "科室")
        
        # 创建疾病-并发症关系
        print(f"创建疾病-并发症关系，共 {len(disease_to_complication)} 条...")
        self.conn.relationship("Disease", "Complication", disease_to_complication, "HAS_COMPLICATION", "并发症")
        
        # 创建疾病-药品关系
        print(f"创建疾病-药品关系，共 {len(disease_to_drug)} 条...")
        self.conn.relationship("Disease", "Drug", disease_to_drug, "TREATS_WITH", "药品")
        
        print("所有关系创建完成！")

    def build_graph(self):
        """
        构建完整的知识图谱
        """
        print("=" * 50)
        print("开始构建医疗知识图谱")
        print("=" * 50)
        
        # 清空现有数据（可选，根据需要注释）
        # print("清空现有数据...")
        # self.graph.clear()
        # print("数据清空完成！\n")
        
        # 读取数据
        print("读取数据文件...")
        diseases, symptoms, aliases, parts, departments, complications, drugs, \
        disease_to_alias, disease_to_symptom, diseases_to_part, disease_to_department, \
        disease_to_complication, disease_to_drug, diseases_infos = self.read_file()
        print("数据读取完成！\n")
        
        # 创建节点
        self.create_nodes(diseases, symptoms, aliases, parts, departments, 
                         complications, drugs, diseases_infos)
        print()
        
        # 创建关系
        self.create_relationships(disease_to_alias, disease_to_symptom, diseases_to_part,
                                 disease_to_department, disease_to_complication, disease_to_drug)
        print()
        
        # 统计信息
        node_count = self.graph.counts()
        print("=" * 50)
        print(f"知识图谱构建完成！共创建 {node_count} 个节点")
        print("=" * 50)

    def close(self):
        """
        关闭图数据库连接
        """
        self.conn.close()
        print("图数据库连接已关闭")


# 示例用法
if __name__ == "__main__":
    conn = Neo4jConnection(uri='neo4j://localhost:7687/', user='neo4j', password='neo4jnb.')
    # 创建GraphBuilder实例
    builder = GraphBuilder(conn)
    diseases, symptoms, aliases, parts, departments, complications, drugs,\
    disease_to_alias, disease_to_symptom, diseases_to_part, disease_to_department, \
    disease_to_complication, disease_to_drug, diseases_infos = builder.read_file()
    builder.create_disease_node(diseases_infos)
    builder.create_nodes("Symptom", symptoms)
    builder.create_nodes("Alias", aliases)
    builder.create_nodes("Part", parts)
    builder.create_nodes("Department", departments)
    builder.create_nodes("Complication", complications)
    builder.create_nodes("Drug", drugs)
    builder.create_relationships(disease_to_alias, disease_to_symptom, diseases_to_part,
                                 disease_to_department, disease_to_complication, disease_to_drug)

    builder.close()
