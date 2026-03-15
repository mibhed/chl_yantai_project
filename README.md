# 烟台近岸海域叶绿素a遥感分析与可视化系统

## 项目定位

本项目参考黄河口邻近海域叶绿素a机器学习反演论文的方法框架，
在没有烟台本地原位 Chl-a 数据的前提下，采用"论文方法复现 + 区域迁移应用"的思路，
构建烟台近岸海域叶绿素a遥感分析与可视化系统。

## 项目目标

1. 复现多波段遥感特征 + 特征降维 + 机器学习回归的流程
2. 将模型框架迁移应用到烟台近岸区域
3. 实现叶绿素a时空分析与可视化展示
4. 支持真实卫星影像（MODIS等）的输入和处理
5. 提供完整的模型训练和管理功能

## 目录结构

```
chl_yantai_project/
├── app/
│   └── streamlit_app.py          # Streamlit可视化界面
├── src/
│   ├── __init__.py               # 包初始化
│   ├── config.py                 # 配置管理
│   ├── preprocess.py             # 数据预处理
│   ├── train.py                  # 模型训练
│   ├── analysis.py               # 空间分析
│   ├── validate.py               # 数据质量验证
│   ├── raster_processor.py       # TIFF影像处理
│   ├── image_quality.py          # 影像质量检查
│   └── model_manager.py          # 模型管理
├── tests/
│   └── test_core.py              # 单元测试
├── data/
│   ├── raw/                      # 原始数据
│   ├── processed/                # 预处理后数据
│   └── samples/                  # 样本数据
├── outputs/
│   ├── figures/                  # 图表输出
│   ├── maps/                    # 地图输出
│   ├── reports/                 # 报告输出
│   └── models/                  # 模型保存
├── venv/                         # 虚拟环境
├── requirements.txt              # 依赖列表
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
- 模拟样本数据生成
- CSV/Excel数据导入
- TIFF卫星影像处理
- 派生特征计算（波段比值、差值、组合等）

### 3. 质量检查
- 数据格式验证
- 影像质量检查
- 坐标系检查
- 异常值检测

### 4. 模型管理
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

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
source venv/bin/activate
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### 3. 访问系统

打开浏览器访问：`http://your-server-ip:8501`

## 使用流程

### 基本流程
1. 选择参数（区域、年份、月份、模型）
2. 点击"生成分析结果"
3. 查看分析结果和可视化

### 数据导入流程
1. 进入"文件导入与导出"标签页
2. 上传CSV/Excel文件
3. 点击"使用数据训练模型"
4. 在"模型结果"查看性能

### 卫星影像处理流程
1. 进入"卫星影像处理"标签页
2. 上传TIFF影像文件
3. 配置波段映射
4. 点击"检查影像质量"
5. 点击"处理影像"
6. 下载处理后的数据

### 模型管理流程
1. 进入"模型结果"标签页
2. 滚动到底部"模型管理"
3. 选择模型类型和参数
4. 点击"训练并保存模型"
5. 查看和删除已保存的模型

## 技术栈

- **Python**: 3.10+
- **数据处理**: numpy, pandas
- **机器学习**: scikit-learn, xgboost, lightgbm
- **可视化**: matplotlib, plotly, streamlit
- **影像处理**: tifffile, rasterio

## 注意事项

1. 首次运行需要较长时间加载模型
2. 大型影像处理可能需要较长时间
3. 建议使用Chrome或Edge浏览器
4. 确保服务器安全组已开放8501端口

## 版本历史

- **V1.0**: 初始版本
- **V10**: 统一文件导入导出、TIFF解析预览、Excel接入导出、高清图导出、LGB/ET模型对比
- **V11**: 新增卫星影像处理、影像质量检查、坐标系检查、模型管理功能

## 许可证

MIT License
