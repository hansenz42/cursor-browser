# 一个 Cursor 浏览器 Agent 工具

![screenshot](https://github.com/user-attachments/assets/75aa5540-ca48-4547-b57b-2898072d8c8e)

使用 Cursor 自带的 AI Agent 自动搜索并总结网页内容。

详细过程可查看我的博客：[原来 Cursor 还能这样用！动手做一个 AI 网页浏览器 | 阿森毛不多](https://www.assen.top/blog/2025-01-21-cursor-ai)

前提条件：
- 在你的电脑里安装 Cursor IDE 并且拥有一个 Pro 账号
- 搭建一个 Python 环境（推荐用 conda 管理环境）
- 因为使用了 duckduckgo 搜索 API，所以需要挂梯子

# 使用方法

## 1. clone 该 repo 到本地

```bash
git clone https://github.com/hansenz42/cursor-browser
```

## 2. 在 cursor 中打开该 repo

打开 cursor，文件 -> 打开文件夹 -> 选择该 repo 的目录

## 3. 在目录下创建 .env 文件，并写入 CHROME 路径

```bash
# 将此文件重命名为 .env 并放在根目录下，然后再运行 Agent
mv template.env .env
```

在 .env 文件中写入 CHROME 路径，例如：

```bash
CHROME_PATH=/opt/homebrew/bin/chromium
```

## 4. 安装依赖

```bash
pip install -r requirements.txt
```

## 5. 在 cursor 中打开 composer，并输入你的指令

打开 cursor 侧边栏，进入 composer，输入你的指令，例如：

```bash
请帮我总结关于苏轼的生平。
```

你即可看到 Cursor 自动搜索并总结了关于苏轼的生平。

注意：你在 composer 中选择 Agent，来运行你的命令。

![Xnip2025-01-26_14-26-03](https://github.com/user-attachments/assets/d5d1da85-cd52-4a63-8c6e-288f09968eca)
