# 宠物知识库语料

这个目录是知识库的**唯一真源**。新增知识只需往这里放文件，然后执行一次灌库：

```bash
cd services/agent
python -m app.knowledge.cli init-db     # 首次
python -m app.knowledge.cli ingest      # 灌入（同 id 会整体替换，可重复执行）
python -m app.knowledge.cli search "猫尿不出来"  # 自测召回效果
```

## 目录名就是分类

子目录决定 `source_type`，加载器会把复数转成单数：

| 目录 | source_type | 用途 | 检索权重倾向 |
| --- | --- | --- | --- |
| `diseases/` | disease | 疾病与症状知识 | +0.05 |
| `first-aid/` | first_aid | 家庭急救与处置 | +0.06 |
| `faq/` | faq | 常见问答 | +0.03 |
| `care/` | care | 日常养护与免疫驱虫 | +0.02 |
| `breeds/` | breed | 品种特征与易感疾病 | 基准 |

希望新增分类？直接建目录即可，`loaders._infer_source_type` 会自动识别。

## 文档格式（Markdown）

```markdown
---
id: kb-cat-lower-urinary      # 必填，同 id 整篇替换；不填则用文件名
title: 猫下泌尿道疾病与尿闭
tags: 猫,泌尿系统,急诊
species: cat                   # dog | cat | all
---

# 猫下泌尿道疾病与尿闭     ← 一级标题会被提取为文档标题

## 什么是下泌尿道疾病      ← 二级标题会成为 chunk 的 heading
正文……

## 需要警惕的表现
正文……
```

## 写作要求

这几条直接影响检索质量，请务必遵守：

1. **标题要有信息量**。`## 症状` 不如 `## 需要警惕的表现`——检索时 heading 会参与召回。
2. **一个二级标题讲一件事**。切分按标题优先，混在一起的多个要点会互相稀释。
3. **每段控制在 400 字以内**。超过会二次滑窗，语义被打断。
4. **把"什么情况必须就医"单独成段**。这是最容易被引用的内容，也是安全边界。
5. **不要写具体药物剂量**。任何处方级内容都会被 `guardrails` 拦截，属于无效语料。

## 也支持 JSON / CSV

适合批量导入问答对：

- JSON：`[{ "id": "...", "title": "...", "content": "...", "species": "cat" }]` 或 `{"items": [...]}`
- CSV/TSV：需包含 `title` 与 `content`（或 `question` / `answer`）列

## 换 Embedding 模型后必须重建

向量维度不一致会导致写库失败。流程：

```bash
# 1. 在 .env 改 PW_AGENT_EMBEDDING_PROVIDER / MODEL / EMBEDDING_DIM
python -m app.knowledge.cli ingest --rebuild
```
