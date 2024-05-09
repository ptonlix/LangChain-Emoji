# 🥳 LangChain-Emoji

简体中文 | [English](README-en.md)

<p>
	<p align="center">
		<img height=160 src="./docs/pic/emoji_logo.jpg">
	</p>
	<p align="center">
		<img height=50 src="./docs/pic/introduce.jpg"><br>
		<b face="雅黑">基于LangChain的开源表情包斗图Agent</b>
	<p>
</p>
<p align="center">
<img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue"/>
<img alt="LangChain" src="https://img.shields.io/badge/LangChain-0.1.16-yellowgreen"/>
<img alt="tcvectordb" src="https://img.shields.io/badge/Tcvectordb-1.3.2-yellow"/>
<img alt="license" src="https://img.shields.io/badge/license-Apache-lightgrey"/>
</p>

> 本项目表情包数据来源于智谱 AI 团队，数据来源和相关介绍如下  
> https://github.com/LLM-Red-Team/emo-visual-data  
> 感谢开源 一起玩转大模型 🎉🌟🌟

## 🚀 Quick Install

### 1.部署 Python 环境

- 安装 miniconda

```shell
mkdir ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
```

- 创建虚拟环境

```shell
# 创建环境
conda create -n LangChain-Emoji python==3.10.11
```

- 安装 poetry

```shell
# 安装
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. 运行 LangChain-Emoji

- 安装依赖

```shell
# 克隆项目代码到本地
git clone https://github.com/ptonlix/LangChain-Emoji.git
conda activate LangChain-Emoji # 激活环境
cd LangChain-Emoji # 进入项目
poetry install # 安装依赖
```

- 修改配置文件

[OpenAI 文档](https://platform.openai.com/docs/introduction)  
[ZhipuAI 文档](https://open.bigmodel.cn/dev/howuse/introduction)  
[LangChain API](https://smith.langchain.com)

```shell
# settings.yaml

配置文件录入或通过环境变量设置以下变量

# OPENAI 大模型API
OPENAI_API_BASE
OPENAI_API_KEY

# ZHIPUAI 智谱API
ZHIPUAI_API_KEY

# LangChain调试 API
LANGCHAIN_API_KEY

# 向量数据库，默认采用chromadb
embedding #配置向量模型，默认为zhipuai

# 腾讯云向量数据库配置(可选)
TCVERCTORDB_API_HOST
TCVERCTORDB_API_KEY

# Minio云盘配置（可选）
MINIO_HOST
MINIO_ACCESS_KEY
MINIO_SECRET_KEY

```

详情配置文件介绍见: [LangChain-Emoji 配置](./docs/config.md)

- 数据初始化

主要借助于 `tools/datainit.py `数据初始化工具完成相关操作

1. 采用数据本地文件部署

[➡️ 百度云盘下载](https://pan.baidu.com/s/11iwqoxLtjV-DOQli81vZ6Q?pwd=tab4)

```
从百度下载数据，解析
地址：https://pan.baidu.com/s/11iwqoxLtjV-DOQli81vZ6Q?pwd=tab4
下载到local_data，并解压
```

[➡️ 谷歌云盘下载](https://pan.baidu.com/s/11iwqoxLtjV-DOQli81vZ6Q?pwd=tab4)

```
cd tools
python datainit.py --download
# 等待数据包下载并解压完成
```

2. 采用 Minio 云盘部署（可选）

完成`步骤1`,将数据下载到 local_data 目录并解压完成

修改`settings.yaml`配置文件中 minio 的配置，填写好  
`MINIO_HOST`  
`MINIO_ACCESS_KEY`  
`MINIO_SECRET_KEY`  
填写好这三个参数

```
cd tools
python datainit.py --upload
# 等待数据上传到minio完成
```

3. 同步元数据到向量数据库 (默认采用 ChromaDB)

```
cd tools
python datainit.py --vectordb
# 等待数据上传到向量数据库完成
```

**腾讯云向量数据库(可选)**

> 修改`settings.yaml`配置文件中 向量数据库 的配置，填写好  
> `TCVERCTORDB_API_HOST`  
> `TCVERCTORDB_API_HOST`  
> 填写好这两个参数  
> `vectorstore` `database`选择 `tcvectordb`

- 启动项目

```shell
# 启动项目
python -m langchain_emoji

# 查看API
访问: http://localhost:8003/docs 获取 API 信息
```

- 启动 Web Demo

```shell
# 进入前端目录
cd frontend
# 启动
streamlit run emoji.py
```

## 💡 演示效果

[![IMAGE ALT TEXT](./docs/pic/example_video.gif)](./docs/pic/example_video.gif)

## 📖 项目介绍

### 1. 目录结构

```
├── docs  # 文档
├── local_data  # 数据集目录
├── langchain_emoji
│   ├── components #自定义组件
│   ├── server # API服务
│   ├── settings # 配置服务
│   ├── utils
│   ├── constants.py
│   ├── di.py
│   ├── launcher.py
│   ├── main.py
│   ├── paths.py
│   ├── __init__.py
│   ├── __main__.py #入口
│   └── __version__.py
├── log # 日志目录
```

### 2. 功能介绍

- 支持 openai 和 zhipuai 两种大模型
- 支持腾讯云向量数据库
- 支持 配置文件动态加载

## 🚩 Roadmap

- [x] 搭建 LangChain-Emoji 初步框架，完善基本功能
- [x] 支持本地向量数据库 Chroma
- [x] 搭建前端 Web Demo
  - [x] 选择 LLM
- [ ] 支持更多模型
  - [ ] 在线大模型: 深度求索 ⏳ 测试中
  - [ ] 本地大模型
- [ ] 接入微信客户端，开启斗图模式

## 🌏 项目交流讨论

<img height=240 src="https://img.gejiba.com/images/f0cf4242e87615dff574806169f9732a.png"/>

🎉 扫码联系作者，如果你也对本项目感兴趣  
🎉 欢迎加入 LangChain-X (帝阅开发社区) 项目群参与讨论交流

## 💥 贡献

欢迎大家贡献力量，一起共建 LangChain-Emoji，您可以做任何有益事情

- 报告错误
- 建议改进
- 文档贡献
- 代码贡献  
  ...  
  👏👏👏

---

### [帝阅介绍](https://dread.run/#/)

> 「帝阅」  
> 是一款个人专属知识管理与创造的 AI Native 产品  
> 为用户打造一位专属的侍读助理，帮助提升用户获取知识效率和发挥创造力  
> 让用户更好地去积累知识、管理知识、运用知识

LangChain-Emoji 是帝阅项目一个子项目

欢迎大家前往体验[帝阅](https://dread.run/#/) 给我们提出宝贵的建议

---

<p align="center">
    <a href="https://dread.run">
	    <img height=160 src="./docs/pic/logo.jpg"/><br>
    </a>
	<b face="雅黑">帝阅DeepRead</b>
</p>
