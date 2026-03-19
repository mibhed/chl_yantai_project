# 烟台近岸海域叶绿素a遥感分析与可视化系统

## 项目定位

本项目参考黄河口邻近海域叶绿素a机器学习反演论文的方法框架，
在没有烟台本地原位 Chl-a 数据的前提下，采用"论文方法复现 + 区域迁移应用"的思路，
构建烟台近岸海域叶绿素a遥感分析与可视化系统。

**2026年3月新增：MODIS L2 端到端反演能力！可直接上传 NASA MODIS L2 产品，实现从卫星影像到 Chl-a 分布图的全流程反演。**

## 项目目标

1. 复现多波段遥感特征 + 特征降维 + 机器学习回归的流程
2. 将模型框架迁移应用到烟台近岸区域
3. 实现叶绿素a时空分析与可视化展示
4. 支持真实卫星影像（MODIS等）的输入和处理
5. 提供完整的模型训练和管理功能
6. 构建现代化的前端界面，提升用户体验

## 目录结构

```
chl_yantai_project/
├── app/
│   ├── api/                     # FastAPI后端API
│   │   ├── __init__.py
│   │   └── main.py              # API主文件
│   ├── streamlit_app.py         # Streamlit可视化界面
│   └── flask_app.py             # Flask应用（备用）
├── frontend/                    # Vue 3前端
│   ├── src/                     # 源代码
│   │   ├── api/                 # API调用
│   │   ├── components/          # 组件
│   │   ├── views/               # 页面
│   │   ├── router/              # 路由
│   │   └── stores/              # 状态管理
│   ├── index.html               # 主页面
│   ├── package.json             # 前端依赖
│   └── vite.config.js           # Vite配置
├── src/                         # 核心模块
│   ├── __init__.py               # 包初始化
│   ├── config.py                 # 配置管理
│   ├── preprocess.py             # 数据预处理
│   ├── train.py                  # 模型训练
│   ├── analysis.py               # 空间分析
│   ├── validate.py               # 数据质量验证
│   ├── raster_processor.py       # TIFF影像处理
│   ├── image_quality.py          # 影像质量检查
│   └── model_manager.py          # 模型管理
├── tests/                        # 测试
│   └── test_core.py              # 单元测试
├── data/                         # 数据
│   ├── raw/                      # 原始数据
│   ├── processed/                # 预处理后数据
│   └── samples/                  # 样本数据
├── outputs/                      # 输出
│   ├── figures/                  # 图表输出
│   ├── maps/                    # 地图输出
│   ├── reports/                 # 报告输出
│   └── models/                  # 模型保存
├── venv/                         # 虚拟环境
├── requirements.txt              # 后端依赖
├── start_all.sh                  # 启动所有服务
├── start_api.sh                  # 启动API服务
├── start_app.sh                  # 启动Streamlit应用
└── README.md                     # 项目说明
```

## 功能特性

### 1. 多模型支持
- MLR（多元线性回归）
- RF（随机森林）
- GP（高斯过程）
- ET（Extra Trees）
- XGBoost
- LightGBM

### 2. 数据处理
- 模拟样本数据生成（基于 OC3 型波段比值公式，物理意义真实）
- CSV/Excel数据导入
- TIFF卫星影像处理（MODIS/Landsat/Sentinel-2）
- 派生特征计算（波段比值、差值、组合等）
- **MODIS L2 NetCDF/HDF5 文件读取**（NASA LAADS 标准格式）
- **水色指数计算（NDCI、CIgreen、CIred-edge、BRR等）**

### 3. 遥感反演（新增，2026年3月）
- MODIS L2 产品端到端反演（上传 .nc/.hdf → 输出 Chl-a 分布图）
- 自动 Rrs 波段提取 + 经纬度裁剪 + QA 质量过滤
- 烟台近岸海域预设区域
- ML 模型逐像素预测 Chl-a
- 输出 GeoTIFF + PNG 预览图

### 4. 质量检查
- 数据格式验证
- 影像质量检查
- 坐标系检查
- 异常值检测

### 5. 模型管理
- 模型训练与评估
- K折交叉验证
- 模型保存与加载
- 版本控制

### 5. 可视化
- 散点图（观测值vs预测值）
- 误差分布直方图
- 空间分布图
- 时序变化曲线
- 多区域/多年对比

### 6. 前端功能
- 现代化Vue 3界面
- 响应式设计
- 实时数据可视化
- 错误处理和用户反馈
- 支持TIFF文件上传
- 数据格式说明

## 快速开始

### 1. 安装依赖

**后端依赖**
```bash
pip install -r requirements.txt
```

**前端依赖**
```bash
cd frontend
npm install
```

### 2. 启动服务

**方式1：一键启动所有服务**
```bash
chmod +x start_all.sh
./start_all.sh
```

**方式2：单独启动**
```bash
# 启动API服务
chmod +x start_api.sh
./start_api.sh

# 启动前端开发服务器
cd frontend
npm run dev

# 启动Streamlit应用（可选）
chmod +x start_app.sh
./start_app.sh
```

### 3. 访问系统

- **前端界面**：`http://localhost:3000`
- **API文档**：`http://localhost:8501/docs`
- **Streamlit界面**：`http://localhost:8502`

## 使用流程

### 前端界面流程
1. **数据管理**：上传样本数据（CSV/Excel）或卫星影像（TIFF）
2. **遥感反演**：上传 MODIS L2 数据，直接生成 Chl-a 分布图（新增）
3. **模型训练**：选择模型类型和参数，点击开始训练
4. **空间分析**：选择区域、年份、月份，生成叶绿素a空间分布
5. **结果展示**：查看模型评估结果和生成的图表

### 数据导入流程
1. 进入"数据管理"页面
2. 上传CSV/Excel文件或TIFF影像
3. 系统会自动验证数据格式
4. 上传成功后可用于模型训练

### 模型训练流程
1. 进入"模型训练"页面
2. 选择模型类型和交叉验证折数
3. 点击"开始训练"
4. 查看训练结果和模型评估指标

### 空间分析流程
1. 进入"空间分析"页面
2. 选择分析区域、年份、月份和模型
3. 点击"开始分析"
4. 查看空间分布结果

### 时间序列分析流程
1. 进入"时间序列"页面
2. 选择分析类型（月度、多区域、多年）
3. 配置分析参数
4. 查看趋势图表

## 技术栈

### 后端
- **Python**: 3.10+
- **数据处理**: numpy, pandas
- **机器学习**: scikit-learn, xgboost, lightgbm
- **API框架**: FastAPI
- **可视化**: matplotlib, plotly, streamlit
- **影像处理**: tifffile, rasterio

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **UI组件**: Element Plus
- **图表库**: ECharts
- **HTTP客户端**: Axios
- **状态管理**: Pinia
- **路由**: Vue Router

## 注意事项

1. 首次运行需要较长时间加载模型
2. 大型影像处理可能需要较长时间
3. 建议使用Chrome或Edge浏览器
4. 确保服务器安全组已开放8501、8502、3000端口
5. 样本数据需要包含`chl_a`列作为目标变量
6. 支持的遥感反射率波段：Rrs_412, Rrs_443, Rrs_469, Rrs_488, Rrs_531, Rrs_547, Rrs_555, Rrs_645, Rrs_667, Rrs_678

## 版本历史

- **V1.0**: 初始版本
- **V10**: 统一文件导入导出、TIFF解析预览、Excel接入导出、高清图导出、LGB/ET模型对比
- **V11**: 新增卫星影像处理、影像质量检查、坐标系检查、模型管理功能
- **V12**: 新增Vue 3前端、FastAPI后端、现代化界面、TIFF上传支持、数据格式说明

## 许可证

MIT License
