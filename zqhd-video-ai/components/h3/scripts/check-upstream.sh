#!/bin/bash
# MiniMax H3 官方 h3-prompt-writing 同步检查脚本
#
# 用法:
#   scripts/check-upstream.sh          只检查，不改动任何文件
#   scripts/check-upstream.sh --apply  同步官方原文文件（references/base-en.txt、references/ref-en.txt）
#   scripts/check-upstream.sh --ack    确认已人工合并官方 SKILL.md 的变化，清除提醒
#
# 范围:
#   references/base-en.txt、references/ref-en.txt  官方原文，可自动同步
#   SKILL.md                                        本机中文增强版，只报告官方变化，由人工合并
#   agents/openai.yaml                              本机自有，不参与同步
#
# 退出码: 0=已是最新  1=有更新待处理  2=网络或环境错误

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO="MiniMax-AI/MiniMax-H3"
DIR_PATH="skills/h3-prompt-writing"
RAW_BASE="https://raw.githubusercontent.com/$REPO/main/$DIR_PATH"
API_BASE="https://api.github.com/repos/$REPO"
STATE_FILE="$SKILL_DIR/.upstream-state"

APPLY=0
ACK=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --ack) ACK=1 ;;
    *) echo "未知参数: ${arg}（可用: --apply、--ack）"; exit 2 ;;
  esac
done

for bin in python3 curl git; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "错误: 缺少命令 $bin"
    exit 2
  fi
done

# 读取上次记录的状态（不存在时使用空值）
LAST_COMMIT=""
LAST_COMMIT_DATE=""
SKILL_MD_REMOTE_SHA=""
BASE_EN_REMOTE_SHA=""
REF_EN_REMOTE_SHA=""
if [ -f "$STATE_FILE" ]; then
  . "$STATE_FILE"
fi

short() {
  printf '%s' "$1" | cut -c1-10
}

json_field() {
  printf '%s' "$1" | python3 -c "import sys,json;d=json.load(sys.stdin);print($2)" 2>/dev/null
}

fetch_remote_sha() {
  curl -fsSL --max-time 20 "$API_BASE/contents/$DIR_PATH/$1?ref=$LATEST_COMMIT" 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("sha",""))' 2>/dev/null
}

set_state() {
  if [ "$1" = "BASE_EN" ]; then
    BASE_EN_REMOTE_SHA="$2"
  else
    REF_EN_REMOTE_SHA="$2"
  fi
}

echo "== MiniMax H3 官方同步检查 =="
echo "基准: $REPO / ${DIR_PATH}（main 分支）"
echo ""

COMMIT_JSON="$(curl -fsSL --max-time 20 "$API_BASE/commits?sha=main&path=$DIR_PATH&per_page=1" 2>/dev/null)"
LATEST_COMMIT="$(json_field "$COMMIT_JSON" 'd[0]["sha"] if isinstance(d,list) and d else ""')"
LATEST_DATE="$(json_field "$COMMIT_JSON" 'd[0]["commit"]["committer"]["date"] if isinstance(d,list) and d else ""')"
LATEST_MSG="$(json_field "$COMMIT_JSON" 'd[0]["commit"]["message"].splitlines()[0] if isinstance(d,list) and d else ""')"

if [ -z "$LATEST_COMMIT" ]; then
  echo "错误: 无法获取官方提交信息（网络问题或 GitHub 限流），请稍后再试"
  exit 2
fi

echo "官方最新提交: $(short "$LATEST_COMMIT")  $LATEST_DATE"
echo "提交说明: $LATEST_MSG"
echo ""
RAW_BASE="https://raw.githubusercontent.com/$REPO/$LATEST_COMMIT/$DIR_PATH"

PENDING=0
FAILED=0
NEW_SKILL_MD_SHA="$SKILL_MD_REMOTE_SHA"

# ---- SKILL.md：只报告官方变化，不自动覆盖 ----
REMOTE_SKILL_SHA="$(fetch_remote_sha "SKILL.md")"
if [ -z "$REMOTE_SKILL_SHA" ]; then
  echo "[异常] SKILL.md: 无法获取官方信息"
  FAILED=1
  PENDING=1
elif [ "$ACK" = "1" ]; then
  echo "[记录] SKILL.md: 官方基线已记录（$(short "$REMOTE_SKILL_SHA")）"
  NEW_SKILL_MD_SHA="$REMOTE_SKILL_SHA"
elif [ -z "$SKILL_MD_REMOTE_SHA" ]; then
  echo "[待处理] SKILL.md: 尚未记录已审查基线；人工核对后使用 --ack"
  PENDING=1
elif [ "$REMOTE_SKILL_SHA" != "$SKILL_MD_REMOTE_SHA" ]; then
  echo "[待处理] SKILL.md: 官方有更新（$(short "$SKILL_MD_REMOTE_SHA") 到 $(short "$REMOTE_SKILL_SHA")）"
  echo "         需人工合并进本机 SKILL.md；合并后运行 scripts/check-upstream.sh --ack 清除提醒"
  PENDING=1
else
  echo "[一致] SKILL.md: 官方内容无新变化（$(short "$REMOTE_SKILL_SHA")）"
fi

# ---- 官方原文文件：可安全自动同步 ----
check_original() {
  local rel="$1"
  local name="$2"
  local local_file="$SKILL_DIR/$rel"
  local last_sha local_sha remote_sha tmpfile new_sha
  if [ "$name" = "BASE_EN" ]; then
    last_sha="$BASE_EN_REMOTE_SHA"
  else
    last_sha="$REF_EN_REMOTE_SHA"
  fi
  remote_sha="$(fetch_remote_sha "$rel")"
  if [ -z "$remote_sha" ]; then
    echo "[异常] $rel: 无法获取官方信息"
    FAILED=1
    PENDING=1
    return
  fi
  if [ ! -f "$local_file" ]; then
    local_sha=""
  else
    local_sha="$(git hash-object "$local_file" 2>/dev/null)"
  fi
  if [ "$local_sha" = "$remote_sha" ]; then
    echo "[一致] $rel: 与官方一致（$(short "$remote_sha")）"
    set_state "$name" "$remote_sha"
    return
  fi
  if [ -n "$local_sha" ] && { [ -z "$last_sha" ] || [ "$local_sha" != "$last_sha" ]; }; then
    echo "[待处理] $rel: 本机内容与上次官方版本不同（可能被本地修改），未自动同步，请人工核对"
    PENDING=1
    return
  fi
  if [ "$APPLY" != "1" ]; then
    echo "[待处理] $rel: 官方已更新待同步（本机未改过该文件，可安全自动同步）"
    PENDING=1
    return
  fi
  tmpfile="$(mktemp "$SKILL_DIR/.h3-upstream.XXXXXX" 2>/dev/null)"
  if [ -z "$tmpfile" ]; then
    echo "[待处理] $rel: 无法创建临时文件"
    FAILED=1
    PENDING=1
    return
  fi
  if curl -fsSL --max-time 60 -o "$tmpfile" "$RAW_BASE/$rel" 2>/dev/null && [ -s "$tmpfile" ]; then
    new_sha="$(git hash-object "$tmpfile" 2>/dev/null)"
    if [ "$new_sha" = "$remote_sha" ]; then
      if ! mv "$tmpfile" "$local_file"; then
        FAILED=1
        PENDING=1
        rm -f "$tmpfile"
        return
      fi
      echo "[已同步] $rel: 已更新到官方最新（$(short "$new_sha")）"
      set_state "$name" "$remote_sha"
    else
      echo "[待处理] $rel: 下载校验不一致，本机文件未改动"
      FAILED=1
      PENDING=1
    fi
  else
    echo "[待处理] $rel: 下载失败或内容异常，本机文件未改动"
    FAILED=1
    PENDING=1
  fi
  rm -f "$tmpfile"
}

check_original "references/base-en.txt" "BASE_EN"
check_original "references/ref-en.txt" "REF_EN"

echo ""
if [ "$PENDING" = "0" ]; then
  echo "== 结果: 本机已与官方 main 同步 =="
else
  echo "== 结果: 有项目待处理（见上方标记）=="
  if [ "$APPLY" != "1" ]; then
    echo "   官方原文文件可运行 scripts/check-upstream.sh --apply 自动同步"
  fi
fi

if { [ "$APPLY" = "1" ] || [ "$ACK" = "1" ]; } && [ "$FAILED" = "0" ]; then
state_tmp="$(mktemp "$SKILL_DIR/.upstream-state.XXXXXX")" || exit 2
cat > "$state_tmp" <<STATE_EOF
# 由 scripts/check-upstream.sh 自动维护，请勿手改
LAST_COMMIT=$LATEST_COMMIT
LAST_COMMIT_DATE=$LATEST_DATE
SKILL_MD_REMOTE_SHA=$NEW_SKILL_MD_SHA
BASE_EN_REMOTE_SHA=$BASE_EN_REMOTE_SHA
REF_EN_REMOTE_SHA=$REF_EN_REMOTE_SHA
STATE_EOF
mv "$state_tmp" "$STATE_FILE" || exit 2
fi

if [ "$FAILED" = "1" ]; then
  exit 2
fi
if [ "$PENDING" = "1" ]; then
  exit 1
fi
exit 0
