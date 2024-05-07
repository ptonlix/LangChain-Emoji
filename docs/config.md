## 配置文件说明

```yaml
# 服务器配置
server:
  env_name: ${APP_ENV:prod}
  port: ${PORT:8002}
  cors:
    enabled: false
    allow_origins: ["*"]
    allow_methods: ["*"]
    allow_headers: ["*"]
  auth:
    enabled: true #是否开启认证
    secret: "Basic c2VjcmV0OmtleQ==" # Http Authorization认证

# 大模型配置
# 选项有4个 openai zhipuai mock openai+zhipuai
# openai+zhipuai 表示同时支持两个模型，根据API传入参数决定使用哪个大模型
llm:
  mode: openai+zhipuai

# 向量模型
# 选项有3个 openai zhipuai mock
# 国内环境建议选择zhipuai比较稳定
# 如果使用腾讯云向量数据库，此参数可以忽略
embedding:
  mode: zhipuai

# openai模型参数
openai:
  temperature: 1
  modelname: "gpt-3.5-turbo-0125" #"gpt-3.5-turbo-1106"
  api_base: ${OPENAI_API_BASE:}
  api_key: ${OPENAI_API_KEY:}

# zhipuai模型参数
zhipuai:
  temperature: 0.95
  top_p: 0.6
  modelname: "glm-3-turbo"
  api_key: ${ZHIPUAI_API_KEY:}

# LangSmith调试参数
# 详情见 https://smith.langchain.com
langsmith:
  trace_version_v2: true
  api_key: ${LANGCHAIN_API_KEY:}

# 向量数据库参数
vectorstore:
  database: tcvectordb #向量数据库类型，目前暂时只支持腾讯云向量数据库
  tcvectordb: # 配置详情见 https://cloud.tencent.com/document/product/1709
    url: ${TCVERCTORDB_API_HOST:} #腾讯云API请求地址
    username: root #账号
    api_key: ${TCVERCTORDB_API_KEY:} #腾讯云向量数据库api key
    collection_name: EmojiCollection #表名称
    database_name: DeepReadDatabase #数据库名称

# 表情包数据集信息
dataset:
  name: emo-visual-data # 数据集文件名称
  google_driver_id: 1r3uO0wvgQ791M_6iIyBODo_8GekBjPMf # 谷歌云盘ID
  mode: local #采用何种数据集加载方式，目前支持 local(本地) 、 Minio(云盘)

# 数据本地存储信息
data:
  local_data_folder: local_data # 本地存储路径，以项目根目录为启始

# 采用Minio来存储数据
# https://www.minio.org.cn/docs/minio/linux/operations/installation.html
minio:
  host: ${MINIO_HOST:} #Minio 请求地址
  bucket_name: emoji #数据桶名称
  access_key: ${MINIO_ACCESS_KEY:} #密钥Key
  secret_key: ${MINIO_SECRET_KEY:} #密钥Key
```

## 私有配置文件

由于配置文件涉及一些 API KEY 等隐私信息，在不改动默认配置文件的情况下，可以新增一个单独的私有配置文件，进行加载

详情见 `langchain_emoji/settings` 代码

```shell
# 1. 设置环境变量
export LE_PROFILES=pro

# 2. 新增配置文件
vim settings-pro.yaml

# 3. 复制默认配置文件，增加API_KEY等信息

# 4. 启动项目，程序会自动合并两个配置文件，冲突地方以settings-pro.yaml为准

```

## 动态加载配置文件

通过监听 yaml 配置文件发生内容变化，程序会重新加载文件，方便实时调整参数

详情见 `langchain_emoji/__main__.py` 代码
