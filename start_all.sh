#!/bin/bash

echo "=== 叶绿素a分析系统启动脚本 ==="

# 清理端口
echo "1. 清理端口..."
fuser -k 8501/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
sleep 1

# 进入项目目录
cd /root/projects/chl_yantai_project || { echo "项目目录不存在"; exit 1; }

# 设置环境变量
export PYTHONPATH=/tmp/fastapi:/tmp/streamlit:/root/projects/chl_yantai_project
export MPLCONFIGDIR=/tmp/matplotlib

# 启动后端（直接使用uvicorn，更稳定）
echo "2. 启动后端服务..."
cd /root/projects/chl_yantai_project
nohup python3 -m uvicorn app.api.main:app --host 0.0.0.0 --port 8501 > backend.log 2>&1 &

# 等待后端启动
echo "   等待后端启动..."
for i in {1..10}; do
    if curl -s http://localhost:8501/api/health > /dev/null 2>&1; then
        echo "   ✅ 后端启动成功！"
        break
    fi
    sleep 1
done

# 启动前端
echo "3. 启动前端服务..."
cd /root/projects/chl_yantai_project/frontend
nohup python3 -m http.server 3000 > frontend.log 2>&1 &

# 等待前端启动
sleep 2

# 验证服务
echo "4. 检查服务状态..."
echo ""

# 检查后端
if curl -s http://localhost:8501/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常 (端口8501)"
else
    echo "❌ 后端服务启动失败，请检查日志：tail -30 backend.log"
fi

# 检查前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务运行正常 (端口3000)"
else
    echo "❌ 前端服务启动失败，请检查日志：tail -10 frontend/frontend.log"
fi

echo ""
echo "=== 访问地址 ==="
echo "前端网站：http://60.205.196.114:3000"
echo "后端API：http://60.205.196.114:8501/api"
echo "API文档：http://60.205.196.114:8501/docs"
echo ""
echo "✅ 系统启动完成！"