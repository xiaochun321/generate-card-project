# generate-card-project

成语卡片解读项目，提供一个可用于生成成语解读卡片的网站。

## 在线访问（GitHub Pages，长期有效，无需服务器）

静态网站已部署到 `docs/` 目录。启用 GitHub Pages 后，访问以下地址即可使用：

https://xiaochun321.github.io/generate-card-project/

### 启用 GitHub Pages（一次性设置）

1. 打开仓库设置页：https://github.com/xiaochun321/generate-card-project/settings/pages
2. "Build and deployment" > Source 选择 **Deploy from a branch**
3. Branch 选择 **main**，文件夹选择 **/docs**
4. 点击 Save，等待 1-2 分钟部署完成

完成后即可通过以上地址永久访问，无需任何服务器或保持电脑开机。

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
