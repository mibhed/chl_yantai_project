# 真实TIFF影像处理指南

## 概述

本系统现已支持真实的卫星影像数据处理，包括MODIS、Landsat和Sentinel-2三种主要卫星数据。系统提供了完整的影像验证、格式转换和数据处理功能。

## 支持的卫星类型

### 1. MODIS
- **卫星**: Aqua/Terra
- **波段数量**: 10个标准Rrs波段
- **波长范围**: 412-678 nm
- **分辨率**: 约1km
- **文件命名特征**: 包含"MODIS"、"MOD"、"AQUA"、"TERRA"、"MYD"等关键词

### 2. Landsat
- **卫星**: Landsat 8/7/5
- **波段数量**: 11个波段
- **波长范围**: 443-12000 nm
- **分辨率**: 30m (多光谱)
- **文件命名特征**: 包含"Landsat"、"LC08"、"LE07"、"LT05"等关键词

### 3. Sentinel-2
- **卫星**: Sentinel-2A/2B
- **波段数量**: 13个波段
- **波长范围**: 443-2190 nm
- **分辨率**: 10-60m
- **文件命名特征**: 包含"Sentinel"、"S2"、"S2A"、"S2B"、"MSI"等关键词

## 使用流程

### 步骤1: 启动系统

```bash
cd /root/projects/chl_yantai_project
bash start_all.sh
```

系统将在以下端口启动：
- 前端: http://localhost:3000
- 后端API: http://localhost:8501

### 步骤2: 访问前端界面

在浏览器中打开: http://localhost:3000

### 步骤3: 验证TIFF影像格式

1. 点击"数据管理"菜单
2. 选择"卫星影像验证"标签页
3. 拖拽或点击上传你的TIFF文件
4. 点击"验证影像格式"按钮
5. 查看验证结果，包括：
   - 卫星类型识别
   - 格式兼容性检查
   - 错误和警告信息
   - 转换建议

### 步骤4: 转换影像到标准格式

1. 选择"卫星影像转换"标签页
2. 上传你的TIFF文件
3. 配置转换参数：
   - **卫星类型**: 可选择自动识别或手动指定（MODIS/Landsat/Sentinel2）
   - **目标分辨率**: 可选，设置重采样分辨率（米）
   - **重采样方法**: 最近邻/双线性/三次卷积
4. 点击"转换影像"按钮
5. 等待转换完成
6. 下载转换后的标准格式影像

### 步骤5: 使用转换后的影像

转换后的影像可以直接用于：
- 模型训练
- 空间分析
- 叶绿素a浓度反演
- 时间序列分析

## API接口说明

### 1. 验证卫星影像

**接口**: `POST /api/satellite/validate`

**参数**:
- `file`: TIFF文件 (multipart/form-data)

**返回**:
```json
{
  "success": true,
  "message": "影像验证完成",
  "data": {
    "valid": true,
    "satellite_type": "MODIS",
    "errors": [],
    "warnings": [],
    "suggestions": []
  }
}
```

### 2. 转换卫星影像

**接口**: `POST /api/satellite/convert`

**参数**:
- `file`: TIFF文件 (multipart/form-data)
- `satellite_type`: 卫星类型 (可选，自动识别)
- `target_resolution`: 目标分辨率 (可选，米)
- `resampling_method`: 重采样方法 (可选，默认nearest)

**返回**:
```json
{
  "success": true,
  "message": "影像转换成功",
  "data": {
    "original_file": "MODIS_2025.tif",
    "converted_file": "converted_MODIS_2025.tif",
    "satellite_type": "MODIS",
    "shape": [10, 1000, 1000],
    "dtype": "float32",
    "output_path": "/path/to/converted.tif",
    "download_url": "/api/satellite/download/converted_xxx.tif"
  }
}
```

### 3. 下载转换后的影像

**接口**: `GET /api/satellite/download/{filename}`

**参数**:
- `filename`: 文件名

**返回**: TIFF文件

### 4. 批量转换

**接口**: `POST /api/satellite/batch-convert`

**参数**:
- `files`: 多个TIFF文件
- `satellite_type`: 卫星类型 (可选)
- `target_resolution`: 目标分辨率 (可选)

**返回**:
```json
{
  "success": true,
  "message": "批量转换完成，共处理5个文件",
  "data": {
    "total_files": 5,
    "successful": 4,
    "failed": 1,
    "results": [...],
    "output_directory": "/path/to/output"
  }
}
```

## 命令行使用

### 验证TIFF文件

```bash
python src/satellite_converter.py /path/to/image.tif
```

### 转换TIFF文件

```bash
python src/satellite_converter.py /path/to/image.tif --convert
```

### 批量转换目录

```bash
python src/satellite_converter.py /input/dir /output/dir --batch
```

## 数据格式要求

### 输入格式
- 文件类型: GeoTIFF (.tif, .tiff)
- 数据类型: 支持整数和浮点型
- 坐标系: 建议包含投影信息
- 波段数量: 根据卫星类型而定

### 输出格式
- 文件类型: GeoTIFF
- 数据类型: float32
- 波段数量: 9个标准Rrs波段
- 波段名称: Rrs_412, Rrs_443, Rrs_488, Rrs_531, Rrs_547, Rrs_555, Rrs_645, Rrs_667, Rrs_678

## 波段映射说明

### MODIS → 标准Rrs波段
MODIS影像已经是标准格式，无需特殊映射。

### Landsat → 标准Rrs波段
```
Rrs_412 ← B1 (443nm)
Rrs_443 ← B2 (482nm)
Rrs_488 ← B2 (482nm)
Rrs_531 ← B3 (562nm)
Rrs_547 ← B3 (562nm)
Rrs_555 ← B3 (562nm)
Rrs_645 ← B4 (655nm)
Rrs_667 ← B4 (655nm)
Rrs_678 ← B4 (655nm)
```

### Sentinel-2 → 标准Rrs波段
```
Rrs_412 ← B1 (443nm)
Rrs_443 ← B2 (490nm)
Rrs_488 ← B2 (490nm)
Rrs_531 ← B3 (560nm)
Rrs_547 ← B3 (560nm)
Rrs_555 ← B3 (560nm)
Rrs_645 ← B4 (665nm)
Rrs_667 ← B4 (665nm)
Rrs_678 ← B4 (665nm)
```

## 注意事项

1. **文件大小**: 大型影像文件可能需要较长处理时间
2. **内存要求**: 处理高分辨率影像需要足够内存
3. **坐标系**: 建议使用投影坐标系而非地理坐标系
4. **数据质量**: 确保影像数据质量良好，无大量云层遮挡
5. **波段顺序**: 不同卫星的波段顺序可能不同，系统会自动处理

## 故障排除

### 问题1: 验证失败
- 检查文件是否为有效的TIFF格式
- 确认文件未损坏
- 检查文件命名是否包含卫星类型关键词

### 问题2: 转换失败
- 确认影像包含足够的波段
- 检查数据类型是否支持
- 验证坐标系信息是否完整

### 问题3: 下载失败
- 检查文件是否存在于服务器
- 确认文件路径正确
- 验证文件权限

## 技术支持

如遇到问题，请检查：
1. 后端日志: `tail -f backend.log`
2. 前端日志: 浏览器开发者工具控制台
3. 系统状态: 访问 http://localhost:8501/api/health

## 更新日志

### v1.0.1 (2026-03-18)
- 新增卫星影像验证功能
- 新增卫星影像转换功能
- 支持MODIS、Landsat、Sentinel-2
- 新增批量转换功能
- 更新前端界面支持新功能