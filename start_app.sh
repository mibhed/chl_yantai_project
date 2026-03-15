#!/bin/bash

echo "清理8501端口..."
fuser -k 8501/tcp 2>/dev/null
kill -9 $(lsof -t -i:8501) 2>/dev/null
pkill -9 -f streamlit 2>/dev/null
sleep 2

echo "启动Streamlit应用..."
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --logger.level warning