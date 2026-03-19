#!/bin/bash
#
# 烟台近岸海域叶绿素a遥感分析与可视化系统
# 一键清理并启动所有服务
#
# 用法: ./start_all.sh
#

set -e

# ── 颜色定义 ──────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'   # No Color

# ── 路径配置 ──────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_LOG="$PROJECT_ROOT/logs/backend.log"
FRONTEND_LOG="$PROJECT_ROOT/logs/frontend.log"

# ── 端口配置 ──────────────────────────────────────
BACKEND_PORT=8501
FRONTEND_PORT=3000

# ── 辅助函数 ──────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       🌊 叶绿素a遥感分析与可视化系统                 ║${NC}"
    echo -e "${CYAN}║       MODIS L2 端到端遥感反演 · v2026.03           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 1. 清理旧进程 ─────────────────────────────────
cleanup_processes() {
    echo -e "\n${BLUE}▶ Step 1: 清理旧进程...${NC}"

    for port in $BACKEND_PORT $FRONTEND_PORT; do
        if fuser -s $port/tcp 2>/dev/null; then
            PID=$(fuser $port/tcp 2>/dev/null | tr -s ' ' '\n' | grep -v '^$' | head -1)
            if [ -n "$PID" ]; then
                info "杀死端口 $port 上的进程 (PID=$PID)"
                fuser -k $port/tcp 2>/dev/null || true
            fi
        fi
    done

    # 杀死可能的残留 Python/Vite 进程
    pkill -f "uvicorn app.api.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true

    sleep 1
    success "旧进程清理完毕"
}

# ── 2. 清理旧日志 ─────────────────────────────────
cleanup_logs() {
    echo -e "\n${BLUE}▶ Step 2: 清理旧日志与缓存...${NC}"

    mkdir -p "$PROJECT_ROOT/logs"

    # 保留最近 5 份日志
    if [ -f "$BACKEND_LOG" ]; then
        cp "$BACKEND_LOG" "$PROJECT_ROOT/logs/backend_prev.log" 2>/dev/null || true
        : > "$BACKEND_LOG"
    fi
    if [ -f "$FRONTEND_LOG" ]; then
        cp "$FRONTEND_LOG" "$PROJECT_ROOT/logs/frontend_prev.log" 2>/dev/null || true
        : > "$FRONTEND_LOG"
    fi

    success "日志已清理"
}

# ── 3. 环境检查 ───────────────────────────────────
check_environment() {
    echo -e "\n${BLUE}▶ Step 3: 环境检查...${NC}"

    # Python
    if ! command -v python3 &>/dev/null; then
        error "未找到 python3，请先安装 Python 3.10+"
        exit 1
    fi
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python 版本: $PYTHON_VERSION"

    # pip 依赖
    info "检查 Python 依赖..."
    MISSING=""
    for pkg in numpy pandas scikit-learn fastapi uvicorn rasterio tifffile netCDF4 h5py; do
        if ! python3 -c "import $pkg" 2>/dev/null; then
            MISSING="$MISSING $pkg"
        fi
    done
    if [ -n "$MISSING" ]; then
        warn "缺少依赖:$MISSING"
        warn "正在安装缺失依赖..."
        pip install $MISSING -q 2>/dev/null || pip install $MISSING
    fi
    success "Python 依赖就绪"

    # Node / npm
    if command -v npm &>/dev/null; then
        info "npm 版本: $(npm --version)"
        info "检查前端依赖..."
        if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
            info "安装前端依赖..."
            cd "$PROJECT_ROOT/frontend" && npm install --silent 2>&1 | tail -3
        fi
        success "前端依赖就绪"
    else
        warn "未找到 npm，跳过前端安装（可单独安装 Node.js）"
    fi
}

# ── 4. 启动后端 ───────────────────────────────────
start_backend() {
    echo -e "\n${BLUE}▶ Step 4: 启动后端服务 (端口 $BACKEND_PORT)...${NC}"

    mkdir -p "$PROJECT_ROOT/logs"

    export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src"
    export MPLCONFIGDIR=/tmp/matplotlib_$$

    cd "$PROJECT_ROOT"

    nohup python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'src')
import uvicorn
uvicorn.run(
    'app.api.main:app',
    host='0.0.0.0',
    port=$BACKEND_PORT,
    log_level='info',
    access_log=False,
)
" >> "$BACKEND_LOG" 2>&1 &

    BACKEND_PID=$!
    info "后端进程 PID=$BACKEND_PID"

    # 等待后端就绪
    for i in $(seq 1 15); do
        if curl -sf http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    if curl -sf http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        VERSION=$(curl -sf http://localhost:$BACKEND_PORT/api/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null || echo "?")
        success "后端启动成功 (PID=$BACKEND_PID, v$VERSION)"
    else
        error "后端启动超时，请检查: tail -50 $BACKEND_LOG"
        exit 1
    fi
}

# ── 5. 启动前端 ───────────────────────────────────
start_frontend() {
    echo -e "\n${BLUE}▶ Step 5: 启动前端服务 (端口 $FRONTEND_PORT)...${NC}"

    cd "$PROJECT_ROOT/frontend"

    nohup npx vite --host 0.0.0.0 --port $FRONTEND_PORT >> "$FRONTEND_LOG" 2>&1 &

    FRONTEND_PID=$!
    info "前端进程 PID=$FRONTEND_PID"

    # 等待前端就绪
    for i in $(seq 1 20); do
        if curl -sf http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    if curl -sf http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        success "前端启动成功 (PID=$FRONTEND_PID)"
    else
        warn "前端启动可能超时，请检查: tail -30 $FRONTEND_LOG"
    fi
}

# ── 6. 最终验证 ───────────────────────────────────
final_check() {
    echo -e "\n${BLUE}▶ Step 6: 服务状态检查...${NC}"
    echo ""

    # 后端
    if curl -sf http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        BACKEND_VER=$(curl -sf http://localhost:$BACKEND_PORT/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null || echo "?")
        echo -e "  ${GREEN}✅${NC} 后端 API  (端口 $BACKEND_PORT)  [v$BACKEND_VER]"
    else
        echo -e "  ${RED}❌${NC} 后端 API  (端口 $BACKEND_PORT)  [离线]"
    fi

    # 前端
    if curl -sf http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} 前端界面  (端口 $FRONTEND_PORT)"
    else
        echo -e "  ${RED}❌${NC} 前端界面  (端口 $FRONTEND_PORT)  [离线]"
    fi

    # MODIS 端点
    if curl -sf http://localhost:$BACKEND_PORT/api/modis/regions > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} MODIS L2 端点"
    else
        echo -e "  ${YELLOW}⚠️${NC}  MODIS L2 端点  [未就绪]"
    fi

    echo ""
}

# ── 主流程 ─────────────────────────────────────────
main() {
    print_banner

    cleanup_processes
    cleanup_logs
    check_environment
    start_backend
    start_frontend
    final_check

    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  🌐  前端界面:   ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  🔌  后端 API:   ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  📖  API 文档:   ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  📁  后端日志:   ${YELLOW}tail -f $BACKEND_LOG${NC}"
    echo -e "  📁  前端日志:   ${YELLOW}tail -f $FRONTEND_LOG${NC}"
    echo ""
    echo -e "  ${GREEN}✅ 系统启动完成！${NC}"
    echo ""
    echo "  快捷操作:"
    echo "    查看后端日志:  tail -f $BACKEND_LOG"
    echo "    查看前端日志:  tail -f $FRONTEND_LOG"
    echo "    重启脚本:      ./start_all.sh"
    echo ""
}

main "$@"
