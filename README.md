# generate-card-project

成语卡片解读项目，提供一个可用于生成成语解读卡片的网站。

## 网站入口

在当前的 GitHub Codespaces / 预览环境中，可通过端口转发地址访问：

- https://animated-memory-x79x74r647jfp4vj-8000.app.github.dev/

如果你是在本机直接运行，也可以访问：

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
