#!/bin/bash

# ==========================================
# ディスクインテリジェンス・モニター v1.0
# 革新的なディスク監視システム
# ==========================================

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m'

# 履歴データ保存ディレクトリ
HISTORY_DIR="$HOME/.disk_monitor_history"
mkdir -p "$HISTORY_DIR"

# ==========================================
# メイン監視機能
# ==========================================

function show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}        ディスクインテリジェンス・モニター v1.0                ${CYAN}║${NC}"
    echo -e "${CYAN}║${WHITE}        AI搭載プロアクティブ監視システム                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# パーティション別詳細分析
function analyze_partitions() {
    echo -e "${BLUE}▶ パーティション使用状況分析${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # データ収集と履歴保存
    local timestamp=$(date +%s)
    local history_file="$HISTORY_DIR/partition_history_$(date +%Y%m%d).log"
    
    df -h | grep -E '^/dev/' | while read line; do
        local device=$(echo "$line" | awk '{print $1}')
        local size=$(echo "$line" | awk '{print $2}')
        local used=$(echo "$line" | awk '{print $3}')
        local avail=$(echo "$line" | awk '{print $4}')
        local use_percent=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local mount=$(echo "$line" | awk '{print $6}')
        
        # 履歴に保存
        echo "$timestamp,$device,$use_percent,$used,$avail" >> "$history_file"
        
        # ビジュアル表示
        printf "%-20s %s\n" "$device" "$mount"
        
        # プログレスバー表示
        local bar_length=50
        local filled_length=$((use_percent * bar_length / 100))
        local bar=""
        
        for ((i=0; i<filled_length; i++)); do
            bar="${bar}█"
        done
        for ((i=filled_length; i<bar_length; i++)); do
            bar="${bar}░"
        done
        
        # 色分け
        if [ "$use_percent" -gt 90 ]; then
            color=$RED
        elif [ "$use_percent" -gt 70 ]; then
            color=$YELLOW
        else
            color=$GREEN
        fi
        
        echo -e "${color}[$bar] ${use_percent}%${NC}"
        echo -e "容量: $size | 使用: $used | 空き: $avail"
        
        # 予測分析
        predict_capacity "$device" "$use_percent"
        echo ""
    done
}

# AI予測機能
function predict_capacity() {
    local device=$1
    local current_usage=$2
    local history_file="$HISTORY_DIR/partition_history_$(date +%Y%m%d).log"
    
    if [ -f "$history_file" ]; then
        # 過去24時間の増加率を計算
        local growth_rate=$(calculate_growth_rate "$device")
        
        if (( $(echo "$growth_rate > 0" | bc -l) )); then
            local days_to_full=$(echo "scale=1; (100 - $current_usage) / $growth_rate" | bc -l)
            
            if (( $(echo "$days_to_full < 7" | bc -l) )); then
                echo -e "${RED}⚠ 警告: このペースだと約${days_to_full}日で容量不足になります${NC}"
            elif (( $(echo "$days_to_full < 30" | bc -l) )); then
                echo -e "${YELLOW}📊 予測: 約${days_to_full}日で満杯になる可能性があります${NC}"
            fi
        fi
    fi
}

# 成長率計算
function calculate_growth_rate() {
    local device=$1
    local history_file="$HISTORY_DIR/partition_history_$(date +%Y%m%d).log"
    
    if [ -f "$history_file" ]; then
        # 簡易的な成長率計算（実際にはもっと複雑な計算が必要）
        local first_usage=$(grep "$device" "$history_file" | head -1 | cut -d',' -f3)
        local last_usage=$(grep "$device" "$history_file" | tail -1 | cut -d',' -f3)
        local time_diff=1  # 簡易的に1日として計算
        
        if [ -n "$first_usage" ] && [ -n "$last_usage" ]; then
            echo "scale=2; ($last_usage - $first_usage) / $time_diff" | bc -l
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

# I/Oパフォーマンス監視
function monitor_io_performance() {
    echo -e "${BLUE}▶ I/Oパフォーマンス分析${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # iostatがインストールされているか確認
    if command -v iostat &> /dev/null; then
        iostat -dx 1 2 | tail -n +4 | grep -E '^(sd|nvme)' | while read line; do
            local device=$(echo "$line" | awk '{print $1}')
            local r_await=$(echo "$line" | awk '{print $10}')
            local w_await=$(echo "$line" | awk '{print $11}')
            local util=$(echo "$line" | awk '{print $14}')
            
            echo -e "${CYAN}デバイス: $device${NC}"
            
            # パフォーマンスビジュアライゼーション
            visualize_performance "読み込み遅延" "$r_await" "ms"
            visualize_performance "書き込み遅延" "$w_await" "ms"
            visualize_performance "使用率" "$util" "%"
            echo ""
        done
    else
        echo -e "${YELLOW}注意: iostatがインストールされていません。詳細なI/O分析には 'sysstat' パッケージが必要です。${NC}"
        
        # 代替手段でI/O情報を表示
        if [ -f /proc/diskstats ]; then
            echo -e "${WHITE}基本的なI/O統計:${NC}"
            awk '{if ($3 ~ /^(sd|nvme)/) print $3 ": 読み込み=" $4 ", 書き込み=" $8}' /proc/diskstats
        fi
    fi
}

# パフォーマンスビジュアライゼーション
function visualize_performance() {
    local label=$1
    local value=$2
    local unit=$3
    
    # 値を整数に変換（小数点がある場合）
    local int_value=$(echo "$value" | cut -d'.' -f1)
    
    # バーの長さを計算（最大30文字）
    local max_bar=30
    local bar_length=$((int_value * max_bar / 100))
    
    # 最小1、最大30に制限
    [ "$bar_length" -lt 1 ] && bar_length=1
    [ "$bar_length" -gt "$max_bar" ] && bar_length=$max_bar
    
    printf "  %-15s: " "$label"
    
    # 色分け
    if [ "$int_value" -gt 80 ]; then
        color=$RED
    elif [ "$int_value" -gt 50 ]; then
        color=$YELLOW
    else
        color=$GREEN
    fi
    
    # バー表示
    echo -ne "${color}"
    for ((i=0; i<bar_length; i++)); do echo -n "▓"; done
    for ((i=bar_length; i<max_bar; i++)); do echo -n "░"; done
    echo -e " ${value}${unit}${NC}"
}

# ファイルシステム健全性チェック
function check_filesystem_health() {
    echo -e "${BLUE}▶ ファイルシステム健全性チェック${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # iノード使用状況
    echo -e "${CYAN}iノード使用状況:${NC}"
    df -i | grep -E '^/dev/' | while read line; do
        local device=$(echo "$line" | awk '{print $1}')
        local iused_percent=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local mount=$(echo "$line" | awk '{print $6}')
        
        if [ "$iused_percent" != "-" ]; then
            printf "  %-20s %-20s " "$device" "$mount"
            
            if [ "$iused_percent" -gt 80 ]; then
                echo -e "${RED}iノード使用率: ${iused_percent}% ⚠${NC}"
            elif [ "$iused_percent" -gt 60 ]; then
                echo -e "${YELLOW}iノード使用率: ${iused_percent}%${NC}"
            else
                echo -e "${GREEN}iノード使用率: ${iused_percent}%${NC}"
            fi
        fi
    done
    
    echo ""
    
    # 大きなファイルの検出
    echo -e "${CYAN}大容量ファイル検出（上位5件）:${NC}"
    find / -xdev -type f -size +100M 2>/dev/null | head -5 | while read file; do
        if [ -f "$file" ]; then
            local size=$(du -h "$file" 2>/dev/null | cut -f1)
            echo -e "  ${YELLOW}$size${NC} - $file"
        fi
    done
    
    echo ""
    
    # 古いファイルの検出
    echo -e "${CYAN}長期間アクセスされていないファイル:${NC}"
    local old_files=$(find /tmp -atime +30 -type f 2>/dev/null | wc -l)
    echo -e "  /tmp内の30日以上アクセスされていないファイル: ${YELLOW}${old_files}個${NC}"
}

# 3Dビジュアライゼーション（ASCIIアート）
function show_3d_visualization() {
    echo -e "${BLUE}▶ 3Dストレージビジュアライゼーション${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # パーティション情報を取得
    local partitions=()
    local usages=()
    
    while IFS= read -r line; do
        local use_percent=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local mount=$(echo "$line" | awk '{print $6}')
        partitions+=("$mount")
        usages+=("$use_percent")
    done < <(df -h | grep -E '^/dev/')
    
    # 3D風ASCII表現
    echo -e "${CYAN}     ╱─────────────────────────────╲${NC}"
    echo -e "${CYAN}    ╱                               ╲${NC}"
    
    for i in "${!partitions[@]}"; do
        local partition="${partitions[$i]}"
        local usage="${usages[$i]}"
        local height=$((usage / 10))
        
        # 色分け
        if [ "$usage" -gt 80 ]; then
            color=$RED
        elif [ "$usage" -gt 60 ]; then
            color=$YELLOW
        else
            color=$GREEN
        fi
        
        # 3D柱の描画
        printf "   "
        for ((j=0; j<height; j++)); do
            echo -ne "${color}█${NC}"
        done
        for ((j=height; j<10; j++)); do
            echo -ne "░"
        done
        printf " %-15s %3d%%\n" "$partition" "$usage"
    done
    
    echo -e "${CYAN}   ╲_______________________________╱${NC}"
}

# レポート生成
function generate_report() {
    local report_file="$HISTORY_DIR/disk_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "ディスク監視レポート"
        echo "生成日時: $(date)"
        echo "================================"
        echo ""
        
        echo "パーティション使用状況:"
        df -h
        echo ""
        
        echo "iノード使用状況:"
        df -i
        echo ""
        
        if command -v iostat &> /dev/null; then
            echo "I/Oパフォーマンス:"
            iostat -dx 1 1
        fi
    } > "$report_file"
    
    echo -e "${GREEN}レポートを生成しました: $report_file${NC}"
}

# メイン実行
function main() {
    show_header
    analyze_partitions
    monitor_io_performance
    check_filesystem_health
    show_3d_visualization
    
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}オプション:${NC}"
    echo -e "  ${CYAN}R${NC} - レポート生成"
    echo -e "  ${CYAN}Q${NC} - 終了"
    echo -e "  ${CYAN}その他${NC} - 更新"
    
    read -n1 -p "選択してください: " choice
    echo ""
    
    case "$choice" in
        [Rr])
            generate_report
            ;;
        [Qq])
            echo -e "${GREEN}監視を終了します。${NC}"
            exit 0
            ;;
        *)
            main
            ;;
    esac
}

# 実行
main