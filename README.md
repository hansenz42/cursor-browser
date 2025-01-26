# 一个 Cursor 浏览器 Agent 工具

使用 Cursor 自带的 AI Agent 自动搜索并总结网页内容。

前提条件：
- 在你的电脑里安装 Cursor IDE 并且拥有一个 Pro 账号
- 搭建一个 Python 环境（推荐用 conda 管理环境）

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

注意：你需要在 composer 中选择 Agent。