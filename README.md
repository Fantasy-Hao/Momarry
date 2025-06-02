


          
# Momarry - 月子中心智能查询API

🏥 一个基于自然语言处理的月子中心信息提取和分析API服务，支持智能关键词识别、语义扩展和结构化数据输出。

## ✨ 功能特性

- 🔍 **智能关键词提取**：自动识别区域、品牌、档次、服务类型等关键信息
- 💰 **价格智能解析**：支持价格范围、条件判断（如"10万以内"）
- 🧠 **BERT句向量**：生成查询语句的语义向量，支持相似度计算
- 🔗 **语义扩展**：基于Word2Vec模型进行同义词扩展
- 📊 **结构化输出**：返回标准化的JSON格式数据
- 🚀 **RESTful API**：简单易用的HTTP接口

## 🏗️ 项目结构

```
Momarry/
├── app.py                 # 主应用文件
├── data/                  # 词典数据目录
│   ├── areas.txt         # 区域词典（南京各区）
│   ├── brands.txt        # 月子中心品牌词典
│   ├── service_types.txt # 服务类型词典
│   └── attributes.txt    # 属性词典（档次、模式等）
├── bert-base-chinese/     # BERT模型文件
├── models/               # Word2Vec模型目录
└── requirements.txt      # 依赖包列表
```

## 🛠️ 技术栈

- **Python 3.7+**
- **Flask** - Web框架
- **jieba** - 中文分词
- **transformers** - BERT模型
- **gensim** - Word2Vec语义扩展
- **torch** - 深度学习框架

## 📦 安装部署

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## 🚀 API使用

### 健康检查

```bash
GET /health
```

**响应示例：**
```json
{
  "status": "healthy",
  "message": "月子中心查询API服务运行正常"
}
```

### 查询解析

```bash
POST /parse
Content-Type: application/json

{
  "query": "帮我找鼓楼区的月子中心，高档一点的，价格控制在10万以内，最好是酒店式风格的，要专业，最好有全职专家驻店"
}
```

**响应示例：**
```json
{
  "范围": ["鼓楼区"],
  "品牌": [],
  "档次": ["高档"],
  "分店": [],
  "类型": ["酒店式"],
  "地址": ["鼓楼区"],
  "模式": ["专业", "全职专家"],
  "价格": {
    "min": 0,
    "max": 100000
  },
  "价格条件": "range",
  "语义扩展": {
    "品牌扩展": [],
    "档次扩展": ["高档", "超高档"],
    "模式扩展": ["全职专家", "台式护理", "母婴同室"]
  },
  "句向量": [0.23, 0.12, -0.01, ...]
}
```

## 📝 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| 范围 | Array | 查询的地理范围 |
| 品牌 | Array | 识别的月子中心品牌 |
| 档次 | Array | 服务档次（高档、豪华等） |
| 分店 | Array | 具体分店信息 |
| 类型 | Array | 服务类型（酒店式、家庭式等） |
| 地址 | Array | 地址信息 |
| 模式 | Array | 服务模式（全职专家、24小时护理等） |
| 价格 | Number/Object | 价格信息，支持单值和范围 |
| 价格条件 | String | 价格条件（range/lt/gt/exact） |
| 语义扩展 | Object | 基于Word2Vec的同义词扩展 |
| 句向量 | Array | BERT生成的句子语义向量 |

## 🎯 使用场景

- **月子中心搜索平台**：智能解析用户查询意图
- **客服机器人**：理解用户需求，提供精准推荐
- **数据分析**：提取用户偏好，进行市场分析
- **推荐系统**：基于语义向量计算相似度

## 🔧 配置说明

### 词典文件

- `data/areas.txt`：支持的查询区域
- `data/brands.txt`：月子中心品牌库
- `data/service_types.txt`：服务类型分类
- `data/attributes.txt`：属性标签（档次、模式等）

### 模型文件

- `bert-base-chinese/`：BERT中文预训练模型
- `models/chinese-w2v.kv`：Word2Vec中文词向量模型（可选）

## 🧪 测试示例

```bash
# 使用curl测试
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d '{"query":"我想在建邺区找个豪华的月子中心，预算15万左右，要24小时护理的"}'

# 使用PowerShell测试
$body = @{ query = "玄武区有没有经济型的月子中心，5万以内的" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5000/parse" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body $body
```

## 🔄 扩展开发

### 添加新词典

1. 在 `data/` 目录下创建新的词典文件
2. 在 `app.py` 中添加对应的加载逻辑
3. 在 `extract_keywords()` 函数中添加识别规则

### 自定义价格解析

修改 `app.py` 中的 `price_patterns` 正则表达式列表，支持更多价格表达方式。

### 集成新的NLP模型

在 `initialize_models()` 函数中添加新模型的加载逻辑。

## 📋 依赖要求

```txt
Flask==2.3.3
jieba==0.42.1
torch==1.13.1
transformers==4.21.3
gensim==4.3.2
numpy==1.24.3
```

## 🐛 常见问题

**Q: BERT模型加载失败？**
A: 确保 `bert-base-chinese/` 目录包含完整的模型文件，或检查torch版本兼容性。

**Q: Word2Vec扩展不工作？**
A: Word2Vec模型是可选的，如果 `models/chinese-w2v.kv` 不存在，系统会跳过语义扩展功能。

**Q: 识别准确率不高？**
A: 可以通过更新词典文件和调整正则表达式来提高识别准确率。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

---

**开发者**: Momarry Team  
**版本**: 1.0.0  
**更新时间**: 2025年
        