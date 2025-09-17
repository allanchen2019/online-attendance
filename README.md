# 线上学生考勤系统

一个基于 Python Flask + SQLite 的极简学生考勤系统，专为0经验开发者设计。

## 技术栈

- **后端:** Python, Flask
- **数据库:** SQLite
- **前端:** HTML, Bootstrap, jQuery
- **包管理:** uv

## 如何运行

**前提条件:** 你需要安装 Python 3.12+ 和 [uv](https://github.com/astral-sh/uv)。

1.  **克隆或下载项目**
    将所有文件放在一个名为 `online-attendance` 的文件夹中。

2.  **创建虚拟环境并安装依赖**
    在项目根目录（`online-attendance/`）下打开终端，运行：
    ```bash
    # 创建虚拟环境
    uv venv

    # 激活虚拟环境
    # Windows:
    .venv\Scripts\activate
    # macOS / Linux:
    source .venv/bin/activate

    # 安装 pyproject.toml 中定义的依赖 (flask)
    uv pip install -p python .
    ```

3.  **初始化数据库**
    这是**第一次运行前必须执行**的步骤，它会创建 `attendance.db` 文件并填充样本数据。
    ```bash
    python init_db.py
    ```
    你应该会看到成功信息。

4.  **启动Web服务**
    ```bash
    python app.py
    ```
    服务启动后，你应该会看到类似 `Running on http://0.0.0.0:5333` 的输出。

5.  **访问系统**
    打开你的浏览器，访问 [http://127.0.0.1:5333](http://127.0.0.1:5333)，你就可以开始使用了。
