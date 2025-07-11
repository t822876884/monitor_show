FROM ubuntu:22.04

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# 替换 apt 源：适配 ARM64，修复 ubuntu-ports 错误路径
RUN sed -i 's|http://mirrors.aliyun.com/ubuntu|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --fix-missing python3 python3-pip ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 软链接
RUN ln -s /usr/bin/python3 /usr/bin/python

# 项目代码
COPY . .

# 安装依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 创建目录
RUN mkdir -p db downloads

EXPOSE 5000
CMD ["python", "run.py"]
