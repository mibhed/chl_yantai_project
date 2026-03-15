# 叶绿素a遥感分析系统 - 新架构文档

## 架构概述

本系统采用 **Streamlit + FastAPI + Vue3** 的分层架构：

```
┌─────────────────────────────────────────────────────────┐
│                    Vue3 前端 (端口 3000)                 │
│  - Element Plus UI 组件                                  │
│  - ECharts 数据可视化                                     │
│  - Pinia 状态管理                                         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI 后端 (端口 8501)                 │
│  - RESTful API 接口                                      │
│  - 业务逻辑处理                                          │
│  - 模型训练与推理                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  核心业务模块 (src/)                      │
│  - train.py: 模型训练                                     │
│  - analysis.py: 空间分析                                  │
│  - raster_processor.py: 影像处理                          │
│  - image_quality.py: 质量检查                             │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 方式一：保留Streamlit原型（快速验证）

```bash
# 使用优化后的启动脚本
./start_app.sh
```

访问: http://localhost:8501

### 方式二：使用FastAPI + Vue3（推荐生产环境）

#### 1. 启动后端 (FastAPI)

```bash
cd /root/projects/chl_yantai_project
pip install fastapi uvicorn python-multipart

# 启动API服务
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8501 --reload
```

#### 2. 启动前端 (Vue3)

```bash
cd /root/projects/chl_yantai_project/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问: http://localhost:3000

## API 接口文档

启动后端后访问: http://localhost:8501/docs

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/regions` | GET | 获取分析区域列表 |
| `/api/models` | GET | 获取可用模型列表 |
| `/api/upload/samples` | POST | 上传样本数据 |
| `/api/upload/tiff` | POST | 上传卫星影像 |
| `/api/training` | POST | 训练模型 |
| `/api/training/results` | GET | 获取训练结果 |
| `/api/analysis/spatial` | POST | 空间分析 |
| `/api/analysis/monthly` | POST | 月度分析 |
| `/api/analysis/multi-region` | POST | 多区域对比 |
| `/api/analysis/multi-year` | POST | 多年趋势 |

## 项目结构

```
chl_yantai_project/
├── app/
│   ├── streamlit_app.py      # Streamlit原型
│   ├── flask_app.py         # Flask备选
│   └── api/
│       ├── __init__.py
│       └── main.py           # FastAPI主程序
├── src/                     # 核心业务模块
│   ├── train.py
│   ├── analysis.py
│   ├── raster_processor.py
│   ├── image_quality.py
│   └── ...
├── frontend/                # Vue3前端
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── api/             # API调用
│   │   ├── stores/          # 状态管理
│   │   └── router/          # 路由配置
│   └── package.json
├── data/                    # 数据目录
├── outputs/                 # 输出结果
├── start_app.sh             # Streamlit启动脚本
└── README.md
```

## 开发流程建议

1. **原型验证阶段**: 使用Streamlit快速验证功能和流程
2. **API开发阶段**: 将验证通过的逻辑封装为FastAPI接口
3. **前端开发阶段**: 使用Vue3开发生产级界面
4. **联调阶段**: 前后端对接测试
5. **部署阶段**: 容器化部署到生产环境

## 技术栈版本

- Python: 3.8+
- FastAPI: 0.100+
- Vue3: 3.4+
- Element Plus: 2.4+
- Vite: 5.0+

## 注意事项

1. 首次启动前端需要安装依赖: `npm install`
2. 后端需要安装依赖: `pip install fastapi uvicorn python-multipart`
3. 确保8501端口未被占用
4. 前后端联调时，前端代理配置在 `vite.config.js` 中

## 联系方式

如有问题，请查看API文档或联系开发团队。
