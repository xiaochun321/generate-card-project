# generate-card-project

成语卡片解读项目，提供一个可用于生成成语解读卡片的网站。

## 在线访问（GitHub Pages，长期有效，无需服务器）

访问以下地址即可直接使用成语卡片生成器：

https://xiaochun321.github.io/generate-card-project/

## 功能说明

- 输入成语名称即可生成卡片预览
- 拼音自动生成或手动填写
- 可选接入正常模型（兼容 OpenAI API）生成解释内容
- 可选接入生图模型（兼容 OpenAI images API）生成插图
- 卡片通过 Canvas 渲染，支持下载为 PNG 图片

## 本地运行（Flask 版本）

```bash
cd generate-card-project
python3 -m pip install -r requirements.txt
python3 app.py
```

然后在浏览器中打开 http://127.0.0.1:8000/。
