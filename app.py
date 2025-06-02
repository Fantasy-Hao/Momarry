import logging
import os
import re

import jieba
import jieba.posseg as pseg
import torch
from flask import Flask, request, jsonify
from gensim.models import KeyedVectors
from transformers import BertTokenizer, BertModel

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量存储模型
model_w2v = None
tokenizer = None
bert_model = None
BRANDS = set()
SERVICE_TYPES = set()
ATTRIBUTES = set()
AREAS = set()


# 📚 自定义词典加载
def load_dict(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(word.strip() for word in f if word.strip())
        else:
            logger.warning(f"词典文件 {file_path} 不存在，使用默认词典")
            return set()
    except Exception as e:
        logger.error(f"加载词典文件失败: {e}")
        return set()


# 🧹 预处理搜索语句
def preprocess_query(query):
    # 保留中文、英文、数字和基本符号
    query = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\-~至到元万]', '', query)
    return query.strip().lower()


# 🧠 BERT 对整句生成句向量
def get_bert_sentence_embedding(query):
    try:
        if tokenizer and bert_model:
            inputs = tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=128)
            with torch.no_grad():
                outputs = bert_model(**inputs)
            sentence_vector = torch.mean(outputs.last_hidden_state, dim=1)
            return sentence_vector.numpy().flatten().tolist()[:10]
        else:
            return [len(query), query.count('的'), query.count('区'), len(jieba.lcut(query))]
    except Exception as e:
        logger.error(f"BERT句向量提取失败: {e}")
        return [len(query), query.count('的'), query.count('区'), len(jieba.lcut(query))]


# 🪙 同义词扩展（Word2Vec）
def get_similar_words(word, model, topn=3):
    try:
        if model and word in model:
            return [w for w, _ in model.most_similar(word, topn=topn)]
        return []
    except Exception as e:
        logger.error(f"获取同义词失败: {e}")
        return []


# 📝 提取并结构化关键词
def extract_keywords(query):
    query = preprocess_query(query)
    words = pseg.lcut(query)

    keywords = {
        "范围": [],
        "品牌": [],
        "档次": [],
        "分店": [],
        "类型": [],
        "地址": [],
        "模式": [],
        "价格": None,
        "价格条件": None,
        "语义扩展": {
            "品牌扩展": [],
            "档次扩展": [],
            "模式扩展": []
        },
        "句向量": []
    }

    # 基础关键词提取
    for word, flag in words:
        if word in AREAS:
            keywords['范围'].append(word)
            keywords['地址'].append(word)
        elif word in BRANDS:
            keywords['品牌'].append(word)
        elif word in SERVICE_TYPES:
            keywords['类型'].append(word)
        elif word in ATTRIBUTES:
            if word in ['高档', '豪华', '经济型', '中档', '超高档']:
                keywords['档次'].append(word)
            elif word in ['专业', '全职专家', '24小时护理', '一对一', '台式护理', '母婴同室']:
                keywords['模式'].append(word)
        elif flag == "m" and word.isdigit():
            keywords['价格'] = int(word)

    # 使用正则辅助提取价格
    if keywords['价格'] is None:
        price_patterns = [
            (r'(\d+)万?[\-~至到](\d+)万?', 'range'),
            (r'(?:最多|不超过|之内|低于|以下|控制在)(?:.*?)(\d+)万?', 'lt'),
            (r'(?:高于|超过|以上)(?:.*?)(\d+)万?', 'gt'),
            (r'(\d+)(?:万|元)', 'exact')
        ]

        for pattern, condition in price_patterns:
            match = re.search(pattern, query)
            if match:
                if condition == 'range':
                    keywords['价格条件'] = 'range'
                    min_price = int(match.group(1))
                    max_price = int(match.group(2))
                    # 处理万元单位
                    if '万' in match.group(0):
                        min_price *= 10000
                        max_price *= 10000
                    keywords['价格'] = {"min": min_price, "max": max_price}
                elif condition in ['lt', 'gt', 'exact']:
                    keywords['价格条件'] = condition
                    price = int(match.group(1))
                    if '万' in match.group(0):
                        price *= 10000
                    if condition == 'lt':
                        keywords['价格'] = {"min": 0, "max": price}
                        keywords['价格条件'] = 'range'
                    else:
                        keywords['价格'] = price
                break

    # 语义扩展关键词
    if model_w2v:
        for brand in keywords['品牌']:
            keywords['语义扩展']['品牌扩展'].extend(get_similar_words(brand, model_w2v))
        for grade in keywords['档次']:
            keywords['语义扩展']['档次扩展'].extend(get_similar_words(grade, model_w2v))
        for mode in keywords['模式']:
            keywords['语义扩展']['模式扩展'].extend(get_similar_words(mode, model_w2v))

    # 去重
    keywords['语义扩展']['品牌扩展'] = list(set(keywords['语义扩展']['品牌扩展']))
    keywords['语义扩展']['档次扩展'] = list(set(keywords['语义扩展']['档次扩展']))
    keywords['语义扩展']['模式扩展'] = list(set(keywords['语义扩展']['模式扩展']))

    # 提取句向量
    keywords['句向量'] = get_bert_sentence_embedding(query)

    return keywords


# 🔗 API 路由
@app.route("/parse", methods=["POST"])
def parse_query():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须是JSON格式"}), 400

        query_text = data.get("query")
        if not query_text:
            return jsonify({"error": "未提供查询内容，请传入 'query'"}), 400

        result = extract_keywords(query_text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "月子中心查询API服务运行正常"})


# 🚀 初始化函数
def initialize_models():
    global model_w2v, tokenizer, bert_model, BRANDS, SERVICE_TYPES, ATTRIBUTES, AREAS

    logger.info("正在初始化模型和词典...")

    # 加载自定义词典
    BRANDS = load_dict("./data/brands.txt")
    SERVICE_TYPES = load_dict("./data/service_types.txt")
    ATTRIBUTES = load_dict("./data/attributes.txt")
    AREAS = load_dict("./data/areas.txt")

    # 添加默认词典（如果文件不存在）
    if not BRANDS:
        BRANDS = {"爱帝宫", "馨月汇", "美华妇儿", "圣贝拉", "喜月", "月子印象"}
    if not SERVICE_TYPES:
        SERVICE_TYPES = {"酒店式", "家庭式", "医院式", "公寓式", "别墅式"}
    if not ATTRIBUTES:
        ATTRIBUTES = {"高档", "豪华", "经济型", "中档", "专业", "全职专家", "24小时护理"}
    if not AREAS:
        AREAS = {"鼓楼区", "玄武区", "秦淮区", "建邺区", "雨花台区", "栖霞区"}

    # 加载jieba用户词典
    try:
        if os.path.exists("custom_words.txt"):
            jieba.load_userdict("custom_words.txt")
            logger.info("jieba用户词典加载成功")
    except Exception as e:
        logger.warning(f"jieba用户词典加载失败: {e}")

    # 尝试加载Word2Vec模型（可选）
    try:
        w2v_model_path = "models/chinese-w2v.kv"
        if os.path.exists(w2v_model_path):
            model_w2v = KeyedVectors.load(w2v_model_path)
            logger.info("Word2Vec模型加载成功")
        else:
            logger.info("Word2Vec模型文件不存在，跳过加载")
    except Exception as e:
        logger.warning(f"Word2Vec模型加载失败: {e}")

    # 尝试加载BERT模型（可选）
    try:
        tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        bert_model = BertModel.from_pretrained("bert-base-chinese")
        logger.info("BERT模型加载成功")
    except Exception as e:
        logger.warning(f"BERT模型加载失败: {e}，将使用简化的特征提取")

    logger.info("模型初始化完成")


# 🚪 启动服务
if __name__ == "__main__":
    initialize_models()
    app.run(host="0.0.0.0", port=5000, debug=False)
