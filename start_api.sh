#!/bin/bash

# 设置Python路径
export PYTHONPATH=/tmp/fastapi:/tmp/streamlit:$PYTHONPATH

# 清理端口
echo "清理8501端口..."
fuser -k 8501/tcp 2>/dev/null
kill -9 $(lsof -t -i:8501) 2>/dev/null
sleep 2

# 检查依赖
echo "检查依赖..."
python3 -c "import fastapi" 2>/dev/null || pip3 install fastapi uvicorn python-multipart --target=/tmp/fastapi --quiet
python3 -c "import pandas" 2>/dev/null || pip3 install pandas numpy scikit-learn matplotlib --target=/tmp/streamlit --quiet

echo "启动FastAPI后端..."
PYTHONPATH=/tmp/fastapi:/tmp/streamlit python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8501 --reload
