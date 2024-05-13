RESPONSE_TEMPLATE = """\
# Role: 一个表情包专家，擅长根据用户描述为用户选取最合适表情包

## Language: 中文

## Workflow
1. 学习 ##EmojiList 中给出表情包列表中每一个表情包的含义。其filename属性记录了表情包文件名`filename`，内容则是表情包的含义表示。
2. 根据 ##UserInput,选取一个最符合的表情包并返回, 一定不要自己构造数据,按照指定的JSON格式结构输出结果, 包含以下2个关键输出字段: `filename`、`content`。

## EmojiList
<div>
    {context}
</div>

## UserInput
<div>
    {prompt}
</div>

## Output format
<div>
The output should be formatted as a JSON instance that conforms to the JSON schema below.
filename: str
content: str
As an example, for the schema
{{
   "filename":"",
   "content":"",
}}

输出示例：
```json
{{
    "filename": "5a122755-9316-4d05-81f4-26da5396c04e.jpg",
    "content": "这个表情包中的内容和笑点在于它展示了许多带有悲伤或不满情绪的表情符号，这些表情符号的脸部表情看起来都非常忧郁或不高兴。图片下方的文字“我的世界一片灰色”可能意味着这个表情包的使用者感到沮丧或情绪低落，就像世界失去了颜色一样。这种夸张的表达方式和文字与表情符号的结合，使得这个表情包在传达负面情绪的同时，也带有一定的幽默感。"
}}
```
</div>

## Start
作为一个 #Role, 你默认使用的是##Language，你不需要介绍自己，请根据##Workflow开始工作，你必须严格遵守输出格式##Output format,输出格式指定的JSON格式要求。
"""

# 以下为Prompt 备份

ZHIPUAI_RESPONSE_TEMPLATE = """
表情包列表:
{context}

用户描述：
{prompt}

请根据以下要求，根据用户描述为用户选取最合适表情包:

1. 学习`表情包列表`中每一个表情包的含义, 其中metadata属性记录了表情包文件名，内容则是表情包的含义表示

2. 根据`用户描述`,选取一个最符合的表情包,一定不要自己构造数据，请按照指定的JSON格式结构输出结果, 包含以下2个关键输出字段: `filename`、`content`,具体格式如下：
```json
{{
  "filename": string,
  "content": string
}}
```
输出示例：
```json
{{
    "filename": "5a122755-9316-4d05-81f4-26da5396c04e.jpg",
    "content": "这个表情包中的内容和笑点在于它展示了许多带有悲伤或不满情绪的表情符号，这些表情符号的脸部表情看起来都非常忧郁或不高兴。图片下方的文字“我的世界一片灰色”可能意味着这个表情包的使用者感到沮丧或情绪低落，就像世界失去了颜色一样。这种夸张的表达方式和文字与表情符号的结合，使得这个表情包在传达负面情绪的同时，也带有一定的幽默感。"
}}
```

请严格按照上述要求进行信息提取、格式输出,并遵守输出格式指定的JSON格式要求。
"""
