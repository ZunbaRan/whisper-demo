FROM python:3.9-slim

WORKDIR /app

# 安装 Poetry
RUN pip install poetry==1.6.1

# 禁用 Poetry 虚拟环境
RUN poetry config virtualenvs.create false

# 复制项目文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 设置环境变量
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["poetry", "run", "start"] 