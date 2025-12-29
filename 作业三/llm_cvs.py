import os
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


# 设置你的 OpenAI API Key
os.environ["OPENAI_API_KEY"] = "别看我害羞，i am shy"


TEXT_COLUMN_NAME = 'answer'
# 输入文件路径
INPUT_FILE = './data/sample.csv'
# 输出文件路径
OUTPUT_FILE = 'results.csv'

### 定义数据结构
class DiseaseExtraction(BaseModel):
    name: str = Field(description="文本中提到的主要疾病名称")
    alias: str = Field(description="疾病的别名")
    symptom: List[str] = Field(description="疾病表现出的所有症状列表")
    drug: Optional[List[str]] = Field(description="建议使用的药物，如果没有提到则为空")
    department: str = Field(description="建议挂号的科室，例如心内科、呼吸科")

# =================第二步：定义 3 种不同的 Prompt=================
prompts_dict = {
    "Prompt_Simple": ChatPromptTemplate.from_messages([
        ("system", "你是一个医疗数据提取助手。"),
        ("user", "请从以下文本中提取疾病信息：\n{text}")
    ]),

    "Prompt_RolePlay_Expert": ChatPromptTemplate.from_messages([
        ("system", "你是一位拥有20年经验的资深临床医生。你的任务是精准识别病历中的关键结构化信息，忽略无关的闲聊，专注于医学事实。"),
        ("user", "分析以下医生回答记录并提取结构化数据：\n{text}")
    ]),

    "Prompt_CoT": ChatPromptTemplate.from_messages([ # Chain of Thought 思维链风格
        ("system", "你是一个细致的医疗AI。在提取信息之前，请先一步步分析患者的主诉、现病史和用药情况，然后总结出最终的结构化结果。"),
        ("user", "这是医生的回答记录：\n{text}")
    ])
}

temperatures = [0.5, 1.0, 1.5]

def process_data_test():
    # 1. 读取数据 (这里创建一个模拟数据，实际使用时请 pd.read_csv(INPUT_FILE))
    # df = pd.read_csv(INPUT_FILE)
    
    # 模拟数据
    data = {
        'id': [1, 2],
        TEXT_COLUMN_NAME: [
            "患者男，45岁，主诉胸痛三天，伴有左肩放射痛，含服硝酸甘油缓解。怀疑是不稳定型心绞痛。",
            "小孩昨晚开始发烧，体温39度，流鼻涕，嗓子疼。吃了布洛芬退烧了，现在精神还可以。"
        ]
    }
    df = pd.DataFrame(data)
    
    results = []

    print(f"开始处理，共 {len(df)} 条数据，测试 3种Prompt * 3种Temperature...")

    # 循环：遍历每一行数据
    for index, row in df.iterrows():
        original_text = row[TEXT_COLUMN_NAME]
        
        # 循环：遍历 3 种 Temperature
        for temp in temperatures:
            # 初始化 LLM (使用支持 function calling 的模型效果最好，如 gpt-4o 或 gpt-3.5-turbo)
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=temp, base_url="https://api.chatanywhere.tech")
            
            # 使用 .with_structured_output 强制输出结构化数据 (最稳定的方法)
            structured_llm = llm.with_structured_output(DiseaseExtraction)

            # 循环：遍历 3 种 Prompt
            for prompt_name, prompt_template in prompts_dict.items():
                print(f"正在处理 ID:{row['id']} | Temp:{temp} | Prompt:{prompt_name}")
                
                try:
                    # 构建链：Prompt -> LLM (强制结构化)
                    chain = prompt_template | structured_llm
                    
                    # 执行调用
                    extraction: DiseaseExtraction = chain.invoke({"text": original_text})
                    
                    # 收集结果
                    results.append({
                        "temperature": temp,
                        "prompt_name": prompt_name,
                        # 以下是提取出的字段
                        "ext_disease": extraction.name,
                        "ext_symptoms": ", ".join(extraction.symptom),  
                        "ext_drugs": ", ".join(extraction.drug) if extraction.drug else "", 
                        "ext_department": extraction.department,
                        "ext_alias": extraction.alias,
                        "original_id": row['id']  # 保持数据一致性
                    })
                    
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    results.append({
                        "original_id": row['id'],
                        "temperature": temp,
                        "prompt_name": prompt_name,
                        "error": str(e)
                    })

    # =================第五步：保存结果=================
    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n处理完成！结果已保存至 {OUTPUT_FILE}")

def process_data():
    count = 0
    df = pd.read_csv(r"C:\Users\yanran\Downloads\QASystemOnMedicalKG-main\作业三\data\sample.csv", encoding='gb2312')

    results = []
    print(f"开始处理，共{len(df)}条数据")

    # 选择一个prompt（这里使用CoT prompt）
    prompt_template = prompts_dict["Prompt_CoT"]

    for index, row in df.iterrows():
        count += 1  # 计数器应该在这里递增
        if count > 100:
            break

        original_text = row[TEXT_COLUMN_NAME]
        temp = 1.0
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=temp, base_url="https://api.chatanywhere.tech")

        # 使用 .with_structured_output 强制输出结构化数据 (最稳定的方法)
        structured_llm = llm.with_structured_output(DiseaseExtraction)

        try:
            chain = prompt_template | structured_llm

            # 执行调用
            extraction: DiseaseExtraction = chain.invoke({"text": original_text})

            # 收集结果
            results.append({
                "original_id": row.get('id', index),  # 使用index作为fallback
                "ext_disease": extraction.name,
                "ext_symptoms": ", ".join(extraction.symptom),
                "ext_drugs": ", ".join(extraction.drug) if extraction.drug else "",
                "ext_department": extraction.department,
                "ext_alias": extraction.alias
            })

        except Exception as e:
            print(f"Error processing row {index}: {e}")
            results.append({
                "original_id": row.get('id', index),
                "error": str(e)
            })

    # 保存结果
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n处理完成！结果已保存至 {OUTPUT_FILE}")

process_data()


