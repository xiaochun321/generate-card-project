# generate-card-project

成语卡片解读项目，提供一个可用于生成成语解读卡片的网站。

## 网站入口

本地运行后可通过以下地址访问：

- http://127.0.0.1:8000/

## 功能说明

- 输入成语名称即可生成卡片预览
- 可选接入正常模型生成解释内容
- 可选接入生图模型生成插图
- 生成结果会保存为图片文件并提供下载

## 本地运行

```bash
cd generate-card-project
python3 -m pip install -r requirements.txt
python3 app.py
```

然后在浏览器中打开 http://127.0.0.1:8000/。
