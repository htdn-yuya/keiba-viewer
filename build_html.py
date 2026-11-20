import argparse
import json
import os
from pathlib import Path

# ================= デフォルト設定 =================
DEFAULT_JSON_PATH = Path(r"C:\keiba\keiba_pipeline\reports\latest_prediction.json")
DEFAULT_OUTPUT_HTML = Path(r"C:\Streamlit_app\index.html")
ENV_PATH = Path(r"C:\keiba_env\.env")
# ================================================


def _parse_args():
    parser = argparse.ArgumentParser(description="AI競馬予測ビューアーHTML生成")
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help="入力予測JSONパス（省略時は latest_prediction.json）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="出力HTMLパス（省略時は index.html）",
    )
    return parser.parse_args()


def get_env_value(key_name: str, env_file: Path) -> str:
    if key_name in os.environ:
        return os.environ[key_name]
    if not env_file.is_file():
        raise FileNotFoundError(f"❌ .envファイルが見つかりません: {env_file}")

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key_name:
                    return v.strip().strip("'\"")

    raise KeyError(f"❌ '{key_name}' が {env_file} 内に見つかりません。")


args = _parse_args()
JSON_PATH = args.json
OUTPUT_HTML = args.out
APP_PASSWORD = get_env_value("APP_PASSWORD", ENV_PATH)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    races_data = json.load(f)

html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI競馬予測ビューアー</title>
  <style>
    :root {{ --primary: #0f766e; --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0; --text: #0f172a; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: "Yu Gothic UI", "Meiryo", "Noto Sans JP", -apple-system, BlinkMacSystemFont, sans-serif; }}
    body {{ background: var(--bg); color: var(--text); padding: 14px; max-width: 960px; margin: auto; font-size: 14px; }}

    #lock-modal {{ position: fixed; inset: 0; background: rgba(15,23,42,0.85); display: flex; align-items: center; justify-content: center; z-index: 9999; backdrop-filter: blur(4px); }}
    .lock-box {{ background: white; padding: 28px; border-radius: 12px; max-width: 360px; width: 90%; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
    .lock-box input {{ width: 100%; padding: 10px; margin: 12px 0; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1rem; }}
    .lock-box button {{ width: 100%; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}

    .header-bar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin-bottom: 12px; background: white; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(15,23,42,0.05); }}
    select {{ padding: 7px 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: bold; background: white; color: var(--text); }}

    .tabs-row {{ display: flex; gap: 6px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 12px; scrollbar-width: thin; }}
    .r-btn {{ padding: 7px 13px; border: 1px solid #cbd5e1; background: white; border-radius: 7px; cursor: pointer; font-weight: bold; white-space: nowrap; color: #334155; }}
    .r-btn.active {{ background: var(--primary); color: white; border-color: var(--primary); }}

    /* 新聞風レースヘッダー（generate_race_images.py準拠） */
    .race-header {{ background: linear-gradient(135deg, #0f766e, #14b8a6); color: #fff; border-radius: 14px; padding: 18px 20px; margin-bottom: 12px; box-shadow: 0 4px 14px rgba(15,118,110,0.15); }}
    .race-header h1 {{ font-size: 20px; margin: 0 0 6px; line-height: 1.3; }}
    .race-header p {{ margin: 0; font-size: 12.5px; color: #ecfeff; }}

    .volatility-card {{ border: 1px solid; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; }}
    .volatility-card b {{ font-size: 0.95rem; }}
    .volatility-card span {{ font-size: 0.85rem; color: #475569; }}
    .volatility-card small {{ color: #64748b; }}

    .sub-tabs {{ display: flex; border-bottom: 2px solid #cbd5e1; margin-bottom: 14px; overflow-x: auto; scrollbar-width: none; }}
    .sub-btn {{ padding: 8px 14px; border: none; background: none; cursor: pointer; font-weight: bold; color: #64748b; white-space: nowrap; font-size: 0.88rem; }}
    .sub-btn.active {{ color: var(--primary); border-bottom: 3px solid var(--primary); }}

    .panel {{ background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 14px; box-shadow: 0 1px 4px rgba(15,23,42,0.05); }}
    .panel h2 {{ margin: 0 0 10px; color: #0f172a; font-size: 15.5px; }}

    .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px; }}
    .metric-card {{ background: #fff; border: 1px solid #cbd5e1; padding: 9px 6px; border-radius: 9px; text-align: center; box-shadow: 0 1px 2px rgba(15,23,42,0.05); }}
    .metric-card small {{ display: block; font-size: 10.5px; color: #64748b; margin-bottom: 3px; }}
    .metric-card strong {{ display: block; font-size: 13.5px; color: #0f172a; }}

    .candidate-list {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 9px 11px; }}
    .candidate-list > strong {{ display: block; font-size: 0.8rem; color: #334155; margin-bottom: 6px; }}
    .candidate-tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
    .candidate-tag {{ display: inline-flex; align-items: center; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 3px 8px; font-size: 0.78rem; }}
    .candidate-tag small {{ margin-left: 4px; color: #475569; }}

    .tbl-wrap {{ overflow-x: auto; background: white; border-radius: 8px; border: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; white-space: nowrap; background: #fff; }}
    th {{ background: #f1f5f9; color: #334155; font-weight: 700; padding: 8px 5px; border-bottom: 2px solid #cbd5e1; text-align: center; }}
    td {{ padding: 7px 5px; border-bottom: 1px solid #e2e8f0; text-align: center; vertical-align: middle; }}
    tr:last-child td {{ border-bottom: 0; }}
    td.left {{ text-align: left; }}
    tr.top-rank td {{ background-color: #f0fdf4; }}
    .rank-cell {{ font-weight: 800; color: #0f766e; }}
    tr.top-rank td.rank-cell {{ font-size: 0.9rem; }}

    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 999px; font-size: 0.72rem; font-weight: bold; }}
    .badge-iron {{ background:#fef3c7; color:#b45309; border:1px solid #fcd34d; }}
    .badge-hon {{ background:#dcfce7; color:#15803d; border:1px solid #86efac; }}
    .badge-aite {{ background:#e0f2fe; color:#0369a1; border:1px solid #7dd3fc; }}
    .badge-burst {{ background:#ffedd5; color:#c2410c; border:1px solid #fdba74; }}
    .badge-solid {{ background:#f3e8ff; color:#6d28d9; border:1px solid #d8b4fe; }}
    .badge-none {{ color:#94a3b8; font-size: 0.8rem; }}

    .num-circle {{ display: inline-flex; align-items: center; justify-content: center; min-width: 21px; height: 21px; padding: 0 3px; border-radius: 50%; background: var(--primary); color: white; font-weight: 800; font-size: 10px; }}
    .style-badge {{ display: inline-block; padding: 2px 5px; border-radius: 5px; background: #e2e8f0; color: #1e293b; font-weight: 700; font-size: 10.5px; }}
    .position-badge {{ display: inline-block; padding: 2px 5px; border-radius: 5px; font-size: 10px; font-weight: 700; }}
    .position-good {{ background: #dcfce7; color: #166534; }}
    .position-warn {{ background: #ffedd5; color: #9a3412; }}
    .position-unknown {{ background: #e2e8f0; color: #475569; }}
    .position-neutral {{ background: #f1f5f9; color: #334155; }}
    .signal-badge {{ display: inline-block; padding: 1px 5px; margin-left: 3px; border-radius: 4px; font-size: 10px; cursor: help; font-weight: 700; }}
    .signal-detail-badge {{ display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 4px; margin-bottom: 3px; }}
    .sig-info {{ background: #f3e8ff; color: #6d28d9; border: 1px solid #d8b4fe; }}
    .sig-pos {{ background: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
    .sig-neg {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}

    /* 1着時の堅実相手・穴馬推奨チップ */
    .pair-rec-main {{ display: inline-flex; align-items: center; gap: 4px; font-weight: 700; }}
    .pair-rec-sub {{ display: inline-flex; align-items: center; gap: 4px; opacity: 0.72; }}
    .pair-chip {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 700; cursor: help; }}
    .pair-solid {{ background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }}
    .pair-upset {{ background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }}
    .pair-upset-strong {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fca5a5; }}
    .pair-2nd {{ background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; }}
    .pair-3rd {{ background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }}
    .pair-arrow {{ color: #94a3b8; font-size: 10px; }}
    tr.selected-winner-row td {{ background-color: #ecfeff; font-weight: 700; }}

    .box {{ background: white; border: 1px solid var(--border); padding: 14px; border-radius: 10px; margin-bottom: 12px; }}
    .prob-bar-bg {{ background-color: #e2e8f0; height: 8px; border-radius: 4px; width: 80px; margin: 0 auto; overflow: hidden; }}
    .prob-bar-fill {{ background-color: #3b82f6; height: 100%; transition: width 0.3s; }}
    .rank-1 {{ background-color: #ffd700; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; display: inline-block; }}
    .rank-2 {{ background-color: #c0c0c0; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; display: inline-block; }}
    .rank-3 {{ background-color: #cd7f32; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; display: inline-block; }}
  </style>
</head>
<body>

  <div id="lock-modal">
    <div class="lock-box">
      <h3>🔒 閲覧認証</h3>
      <p style="font-size:0.85rem; color:#64748b; margin-top:4px;">パスワードを入力してください</p>
      <input type="password" id="pwd-input" placeholder="Password">
      <button onclick="checkPassword()">認証して開く</button>
      <p id="pwd-err" style="color:red; font-size:0.8rem; margin-top:8px; display:none;">パスワードが違います</p>
    </div>
  </div>

  <div id="app-root" style="display:none;">
    <div class="header-bar">
      <h2 style="font-size:1.1rem; color:#0f172a;">🏇 AI競馬予測ビューアー</h2>
      <div>
        <label style="font-size:0.85rem; font-weight:bold;">競馬場: </label>
        <select id="venue-select" onchange="onVenueChange()"></select>
      </div>
    </div>

    <div class="tabs-row" id="race-tabs"></div>
    <div id="race-header-area"></div>

    <div class="sub-tabs">
      <button class="sub-btn active" onclick="switchSubTab('list')">📋 能力指数＆展開予測シート</button>
      <button class="sub-btn" onclick="switchSubTab('cond')">🎯 連動予測(1着固定)</button>
      <button class="sub-btn" onclick="switchSubTab('detail')">🐎 馬詳細</button>
    </div>

    <div id="view-list" class="tab-content"></div>
    <div id="view-cond" class="tab-content" style="display:none;">
      <div class="box">
        <label style="font-weight:bold; color:var(--primary);">🎯 1着想定馬（展開の軸）を選択:</label>
        <select id="winner-select" style="width:100%; margin-top:8px;" onchange="renderConditionalList()"></select>
        <p style="font-size:0.8rem; color:#64748b; margin-top:8px;">選択した馬が1着になる世界線を想定した場合の、<b>🛡️ 堅実相手（1頭）</b>と<b>🚀 穴馬（予測5位以下・純粋リフト最上位1頭）</b>の連動推奨です。</p>
      </div>
      <div id="cond-pair-picks" style="margin-bottom:12px;"></div>
      <div class="tbl-wrap">
        <table>
          <thead>
            <tr>
              <th>AI順位</th>
              <th>1着想定馬</th>
              <th>評価</th>
              <th>🛡️ 堅実相手（AI順位 / シェア）</th>
              <th>🚀 穴馬（AI順位 / リフト）</th>
              <th>1着馬単勝</th>
            </tr>
          </thead>
          <tbody id="cond-tbody"></tbody>
        </table>
      </div>
    </div>
    <div id="view-detail" class="tab-content" style="display:none;"></div>
  </div>

  <script>
    const RAW_DATA = {json.dumps(races_data, ensure_ascii=False)};
    const APP_PWD = "{APP_PASSWORD}";
    const VENUES = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"];
    const VENUE_CODES = {{"01":"札幌","02":"函館","03":"福島","04":"新潟","05":"東京","06":"中山","07":"中京","08":"京都","09":"阪神","10":"小倉"}};

    function checkPassword() {{
      const input = document.getElementById("pwd-input").value;
      if (input === APP_PWD) {{
        unlock();
      }} else {{
        document.getElementById("pwd-err").style.display = "block";
      }}
    }}

    function unlock() {{
      document.getElementById("lock-modal").style.display = "none";
      document.getElementById("app-root").style.display = "block";
      initApp();
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      const params = new URLSearchParams(window.location.search);
      if (params.get("pwd") === APP_PWD) {{
        unlock();
      }}
    }});

    let currentVenue = "";
    let currentRaces = [];
    let currentRaceIdx = 0;

    function extractVenue(race) {{
      for (const k of ["venue", "track_name", "track"]) {{
        const v = String(race[k] || "").trim();
        if (VENUES.includes(v)) return v;
      }}
      const text = `${{race.details || ""}}\\n${{race.name || ""}}`;
      for (const v of VENUES) {{
        if (text.includes(v)) return v;
      }}
      const rid = String(race.race_id || "").replace(/\\D/g, "");
      if (rid.length >= 10 && VENUE_CODES[rid.slice(4, 6)]) {{
        return VENUE_CODES[rid.slice(4, 6)];
      }}
      return "その他";
    }}

    function formatCleanDetails(details) {{
      const text = String(details || "").replace(/\\u00a0|\\u3000/g, " ");
      const items = [];
      const track = text.match(/(芝|ダート|ダ|障害)\\s*\\d{{3,4}}\\s*m/i);
      if (track) items.push(track[0].replace(/\\s+/g, "").replace("ダート", "ダ"));
      const course = text.match(/\\b(右|左)(?:\\s*(?:外|内))?(?:\\s*[A-D])?\\b/);
      if (course) items.push(course[0].replace(/\\s+/g, ""));
      const cond = ["不良", "稍重", "重", "良"].find(v => text.includes(v));
      if (cond) items.push(cond);
      const weather = ["晴", "曇", "小雨", "雨", "雪"].find(v => text.includes(v));
      if (weather) items.push(weather);
      return items.length ? [...new Set(items)].join(" / ") : "条件情報なし";
    }}

    function extractStartTime(details) {{
      const m = String(details || "").match(/(\\d{{1,2}}:\\d{{2}})\\s*発走/);
      return m ? `発走 ${{m[1]}}` : "";
    }}

    function getRaceNum(race, idx) {{
      if (race && race.race_num) return Number(race.race_num);
      if (race && race.race_no) return Number(race.race_no);
      if (race && race.race_id && String(race.race_id).length >= 2) {{
        const lastTwo = parseInt(String(race.race_id).slice(-2), 10);
        if (!isNaN(lastTwo) && lastTwo >= 1 && lastTwo <= 12) return lastTwo;
      }}
      if (idx !== undefined && idx !== null) return idx + 1;
      return 1;
    }}

    function horseKey(val) {{
      const n = parseInt(val, 10);
      return isNaN(n) ? String(val || "").trim() : String(n);
    }}

    function positionBadgeHtml(label) {{
      const text = String(label || "判定材料不足");
      let cls = "position-neutral";
      if (text.includes("自在型") || text.includes("脚質適性あり")) cls = "position-good";
      else if (text.includes("不安定")) cls = "position-warn";
      else if (text.includes("判定材料不足")) cls = "position-unknown";
      return `<span class="position-badge ${{cls}}">${{text}}</span>`;
    }}

    function pairRecommendationHtml(horse, horses, rank) {{
      const winnerKey = horseKey(horse.num || horse.horse_number);
      if (!winnerKey) return '<span style="color:#64748b;">—</span>';

      const hasBadge = (horse.main_badge && horse.main_badge !== "—");
      const wrapCls = (Number(rank) <= 5 || hasBadge) ? "pair-rec-main" : "pair-rec-sub";

      // 1. 新形式（堅実相手 solid ＋ 穴馬 upset）
      const detailsMap = horse.conditional_partner_details;
      const picksMap = horse.conditional_partner_picks;
      if (detailsMap && detailsMap[winnerKey]) {{
        const d = detailsMap[winnerKey];
        const s = d.solid || {{}};
        const u = d.upset || {{}};
        const sNum = horseKey(s.num);
        const uNum = horseKey(u.num);
        if (sNum && uNum) {{
          const sTitle = `堅実相手: ${{sNum}}番 ${{s.name || ''}} (AI${{s.ai_rank || '?'}}位 / シェア${{((s.share || 0) * 100).toFixed(1)}}%)`;
          const liftVal = Number(u.lift || 1.0).toFixed(2);
          const uTitle = `穴馬候補: ${{uNum}}番 ${{u.name || ''}} (AI${{u.ai_rank || '?'}}位 / リフト${{liftVal}}x / 2-3着率${{((u.place23_prob || 0) * 100).toFixed(1)}}%)`;
          const uCls = u.is_strong_upset ? "pair-upset-strong" : "pair-upset";
          const uIcon = u.is_strong_upset ? "🔥" : "🚀";
          return `<span class="${{wrapCls}}"><span class="pair-chip pair-solid" title="${{sTitle}}">🛡️${{sNum}}番</span><span class="pair-chip ${{uCls}}" title="${{uTitle}}">${{uIcon}}${{uNum}}番</span></span>`;
        }}
      }} else if (picksMap && picksMap[winnerKey]) {{
        const sNum = horseKey(picksMap[winnerKey].solid);
        const uNum = horseKey(picksMap[winnerKey].upset);
        if (sNum && uNum) {{
          return `<span class="${{wrapCls}}"><span class="pair-chip pair-solid">🛡️${{sNum}}番</span><span class="pair-chip pair-upset">🚀${{uNum}}番</span></span>`;
        }}
      }}

      // 2. 旧形式（後方互換フォールバック）
      const oldPicks = horse.conditional_pair_picks;
      if (oldPicks && typeof oldPicks === "object" && oldPicks[winnerKey]) {{
        const secNum = horseKey(oldPicks[winnerKey].second);
        const thdNum = horseKey(oldPicks[winnerKey].third);
        if (secNum && thdNum) {{
          return `<span class="${{wrapCls}}"><span class="pair-chip pair-2nd">🥈${{secNum}}番</span><span class="pair-arrow">▸</span><span class="pair-chip pair-3rd">🥉${{thdNum}}番</span></span>`;
        }}
      }}

      return '<span style="color:#64748b;">—</span>';
    }}

    function formatRank(rank, score) {{
      const colors = {{
        'S': {{ color: '#047857', label: '👑 S' }},
        'A': {{ color: '#059669', label: '🟢 A' }},
        'B': {{ color: '#d97706', label: '🟡 B' }},
        'C': {{ color: '#ea580c', label: '🟠 C' }},
        'D': {{ color: '#dc2626', label: '🔴 D' }}
      }};
      const conf = colors[rank] || {{ color: '#64748b', label: rank || '—' }};
      const scoreNum = parseFloat(score || 0);
      const sign = scoreNum > 0 ? '+' : '';
      return `<span style="color:${{conf.color}}; font-weight:bold;">${{conf.label}}</span> <small style="color:#64748b;">(${{sign}}${{scoreNum.toFixed(2)}})</small>`;
    }}

    function initApp() {{
      RAW_DATA.forEach(r => r.venue = extractVenue(r));
      const venues = [...new Set(RAW_DATA.map(r => r.venue))];
      venues.sort((a, b) => {{
        const ia = VENUES.indexOf(a), ib = VENUES.indexOf(b);
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      }});
      const sel = document.getElementById("venue-select");
      sel.innerHTML = venues.map(v => `<option value="${{v}}">${{v}}</option>`).join("");
      currentVenue = venues.includes("東京") ? "東京" : venues[0];
      sel.value = currentVenue;
      onVenueChange();
    }}

    function onVenueChange() {{
      currentVenue = document.getElementById("venue-select").value;
      currentRaces = RAW_DATA.filter(r => r.venue === currentVenue);
      currentRaces.sort((a, b) => getRaceNum(a, 0) - getRaceNum(b, 0));
      currentRaceIdx = 0;
      renderRaceTabs();
      renderCurrentRace();
    }}

    function renderRaceTabs() {{
      const tabsEl = document.getElementById("race-tabs");
      tabsEl.innerHTML = currentRaces.map((r, i) => `
        <button class="r-btn ${{i === currentRaceIdx ? 'active' : ''}}" onclick="selectRace(${{i}})">${{getRaceNum(r, i)}}R</button>
      `).join("");
    }}

    function selectRace(idx) {{
      currentRaceIdx = idx;
      renderRaceTabs();
      renderCurrentRace();
    }}

    function switchSubTab(tab) {{
      document.querySelectorAll(".sub-btn").forEach((b, i) => {{
        b.classList.toggle("active", ["list", "cond", "detail"][i] === tab);
      }});
      document.getElementById("view-list").style.display = tab === "list" ? "block" : "none";
      document.getElementById("view-cond").style.display = tab === "cond" ? "block" : "none";
      document.getElementById("view-detail").style.display = tab === "detail" ? "block" : "none";
    }}

    function getSignalCategoryClass(signalStr) {{
      const s = String(signalStr || "");
      // 1. データ起点アラート（紫）
      if (s.includes("🌍") || s.includes("🔰") || s.includes("データ少") || s.includes("キャリア浅")) {{
        return "sig-info";
      }}
      // 2. ネガティブ・割引材料（赤）
      if (
        s.includes("🩹") || s.includes("🚚") || s.includes("⚠️") ||
        s.includes("🔄") || s.includes("📏") || s.includes("🧱") ||
        s.includes("馬体重増減") || s.includes("休み明け") || s.includes("遠征") ||
        s.includes("大幅増") || s.includes("弱化") || s.includes("延長") || s.includes("昇級")
      ) {{
        return "sig-neg";
      }}
      // 3. ポジティブ・一変好材料（緑）
      return "sig-pos";
    }}

    function formatSignalIcons(signals) {{
      if (!signals || !signals.length) return "";
      return signals.map(s => {{
        const str = String(s).trim();
        const icon = str.split(/\\s+/)[0] || str;
        const cls = getSignalCategoryClass(str);
        return `<span class="signal-badge ${{cls}}" title="${{str}}">${{icon}}</span>`;
      }}).join("");
    }}

    function getBadgeClass(badge) {{
      if (badge.includes("鉄板")) return "badge-iron";
      if (badge.includes("本命")) return "badge-hon";
      if (badge.includes("相手")) return "badge-aite";
      if (badge.includes("バースト")) return "badge-burst";
      if (badge.includes("堅実")) return "badge-solid";
      return "badge-none";
    }}

    function renderCurrentRace() {{
      const race = currentRaces[currentRaceIdx];
      if (!race) return;

      const raceNum = getRaceNum(race, currentRaceIdx);
      const cleanDetails = formatCleanDetails(race.details);
      const startTime = extractStartTime(race.details);
      const metaLine = [currentVenue, cleanDetails, startTime].filter(Boolean).join(" / ");

      const vol = race.volatility || {{}};
      const volLabel = vol.label || "🟡 混戦";
      const volDecision = vol.decision || "";
      const volReason = vol.reason || "";
      const volBg = volLabel.includes("堅軸") ? "#f0fdf4" : (volLabel.includes("波乱") ? "#fef2f2" : "#fffbeb");
      const volBorder = volLabel.includes("堅軸") ? "#bbf7d0" : (volLabel.includes("波乱") ? "#fecaca" : "#fde68a");

      document.getElementById("race-header-area").innerHTML = `
        <header class="race-header">
          <h1>🎯 ${{raceNum}}R：${{race.name}}</h1>
          <p>📍 ${{metaLine}}</p>
        </header>
        <section class="volatility-card" style="background:${{volBg}}; border-color:${{volBorder}};">
          <b>${{volLabel}}</b> <span>(${{volDecision}})</span><br>
          <small>💡 ${{volReason}}</small>
        </section>
      `;

      const horses = [...(race.horses || [])].sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));
      const pace = race.pace_forecast || {{}};
      const cands = pace.front_runner_candidates || [];
      const profiles = pace.style_profiles || [];
      const aptByNum = {{}};
      profiles.forEach(p => {{
        const k = horseKey(p.horse_number || p.number || p.num);
        if (k) aptByNum[k] = p.aptitude_label || "判定材料不足";
      }});

      const candsHtml = cands.length ? cands.map(c => `
        <span class="candidate-tag">
          <span class="num-circle" style="width:18px; height:18px; font-size:0.68rem; margin-right:4px;">${{c.number}}</span>
          <strong>${{c.name}}</strong> <small>(圧力:${{Number(c.pressure || 0).toFixed(2)}})${{c.outside_draw_effort ? ' ↗️外' : ''}}</small>
        </span>
      `).join('') : '<span style="color:#64748b; font-size:0.8rem;">前方候補なし（またはデータ不足）</span>';

      document.getElementById("view-list").innerHTML = `
        <section class="panel">
          <h2>🏁 レース展開 ＆ ペース予測</h2>
          <div class="metrics">
            <div class="metric-card"><small>⏱️ 想定ペース</small><strong>${{pace.pace || '不明'}}</strong></div>
            <div class="metric-card"><small>⚔️ 先行争い激度</small><strong>${{pace.competition_risk || '不明'}}</strong></div>
            <div class="metric-card"><small>🚩 前方展開候補</small><strong>${{pace.candidate_count || 0}}頭</strong></div>
          </div>
          <div class="candidate-list">
            <strong>🚀 展開を引っ張る注目馬</strong>
            <div class="candidate-tags">${{candsHtml}}</div>
          </div>
        </section>

        <section class="panel">
          <h2>📊 出走馬予測ランキング（右端：各馬1着時の🛡️堅実相手・🚀穴馬推奨）</h2>
          <div class="tbl-wrap">
            <table>
              <thead>
                <tr>
                  <th>順位</th>
                  <th>メイン評価</th>
                  <th>馬番</th>
                  <th class="left">馬名 / 特筆</th>
                  <th class="left">騎手</th>
                  <th>脚質</th>
                  <th>位置適性</th>
                  <th>単勝</th>
                  <th>地力評価</th>
                  <th>条件適性</th>
                  <th>1着時の相手・穴推奨</th>
                </tr>
              </thead>
              <tbody>
                ${{horses.map((h, i) => {{
                  const rVal = Number(h.rank || i + 1);
                  const apt = h.aptitude_label || aptByNum[horseKey(h.num)] || '判定材料不足';
                  const badge = h.main_badge || h.tag || '—';
                  const baseHtml = h.base_display || formatRank(h.base_rank, h.base_score);
                  const condHtml = h.cond_display || formatRank(h.cond_rank, parseFloat(h.plus_sum || 0) + parseFloat(h.minus_sum || 0));
                  const pairHtml = pairRecommendationHtml(h, horses, rVal);
                  const listSignals = Array.isArray(h.summary_signals) ? h.summary_signals : (h.one_change_signals || []);
                  return `
                  <tr class="${{rVal === 1 ? 'top-rank' : ''}}">
                    <td class="rank-cell">${{rVal}}位</td>
                    <td><span class="badge ${{getBadgeClass(badge)}}">${{badge}}</span></td>
                    <td><span class="num-circle">${{h.num}}</span></td>
                    <td class="left" style="font-weight:700;">${{h.name}}${{formatSignalIcons(listSignals)}}</td>
                    <td class="left" style="color:#475569;">${{h.jockey || '不明'}}</td>
                    <td><span class="style-badge">${{h.running_style || '不明'}}</span></td>
                    <td>${{positionBadgeHtml(apt)}}</td>
                    <td style="font-weight:700; color:var(--primary);">${{h.odds}}倍</td>
                    <td>${{baseHtml}}</td>
                    <td>${{condHtml}}</td>
                    <td>${{pairHtml}}</td>
                  </tr>
                `;
                }}).join('')}}
              </tbody>
            </table>
          </div>
        </section>
      `;

      document.getElementById("view-detail").innerHTML = `
        <div style="margin-bottom:12px;">
          <select id="horse-sel" style="width:100%; padding:8px;" onchange="renderHorseDetail()">
            ${{horses.map((h, i) => `<option value="${{i}}">${{h.rank}}位: ${{h.num}}番 ${{h.name}}</option>`).join('')}}
          </select>
        </div>
        <div id="horse-detail-content"></div>
      `;
      renderHorseDetail();

      const winSel = document.getElementById("winner-select");
      winSel.innerHTML = horses.map(h => {{
        const b = h.main_badge && h.main_badge !== '—' ? ` [${{h.main_badge}}]` : '';
        return `<option value="${{h.num}}">${{h.num}}番 ${{h.name}} (AI ${{h.rank}}位)${{b}}</option>`;
      }}).join('');
      renderConditionalList();
    }}

    function renderConditionalList() {{
      const race = currentRaces[currentRaceIdx];
      const winnerNumStr = horseKey(document.getElementById("winner-select").value);
      if (!race || !winnerNumStr) return;

      const horses = [...(race.horses || [])].sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));
      const byNum = {{}};
      horses.forEach(h => {{ byNum[horseKey(h.num)] = h; }});

      const selectedWinner = byNum[winnerNumStr];
      const detail = (selectedWinner && selectedWinner.conditional_partner_details && selectedWinner.conditional_partner_details[winnerNumStr])
        ? selectedWinner.conditional_partner_details[winnerNumStr]
        : null;

      const pairBox = document.getElementById("cond-pair-picks");
      if (detail && detail.solid && detail.upset) {{
        const s = detail.solid;
        const u = detail.upset;
        const sHorse = byNum[horseKey(s.num)] || {{}};
        const uHorse = byNum[horseKey(u.num)] || {{}};
        const strongTag = u.is_strong_upset
          ? '<span class="badge badge-burst" style="margin-left:6px;">🔥 強穴(リフト≥1.30x)</span>'
          : '';
        const uBorder = u.is_strong_upset ? "#dc2626" : "#ea580c";

        pairBox.innerHTML = `
          <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:10px;">
            <div class="metric-card" style="border-left:4px solid #0284c7; text-align:left; padding:12px 14px;">
              <small style="color:#0369a1; font-weight:bold;">🛡️ 堅実相手（最有力1頭）</small>
              <div style="font-size:1.05rem; font-weight:bold; color:#0f172a; margin-top:4px;">${{s.num}}番 ${{s.name}} <small style="color:#64748b;">(AI ${{s.ai_rank}}位)</small></div>
              <small style="color:var(--primary); font-weight:bold;">相手シェア: ${{(Number(s.share || 0) * 100).toFixed(1)}}% / 単勝 ${{sHorse.odds || 'N/A'}}倍</small>
            </div>
            <div class="metric-card" style="border-left:4px solid ${{uBorder}}; text-align:left; padding:12px 14px;">
              <small style="color:${{uBorder}}; font-weight:bold;">🚀 確率の高い穴馬（予測5位以下・純粋リフト1位）${{strongTag}}</small>
              <div style="font-size:1.05rem; font-weight:bold; color:#0f172a; margin-top:4px;">${{u.num}}番 ${{u.name}} <small style="color:#64748b;">(AI ${{u.ai_rank}}位)</small></div>
              <small style="color:${{uBorder}}; font-weight:bold;">超過リフト: ${{Number(u.lift || 1.0).toFixed(2)}}x / 2-3着率: ${{(Number(u.place23_prob || 0) * 100).toFixed(1)}}% / 単勝 ${{uHorse.odds || 'N/A'}}倍</small>
            </div>
          </div>
        `;
      }} else {{
        pairBox.innerHTML = '<div class="box" style="color:#64748b; font-size:0.85rem;">このレースの条件付き相手・穴馬データがありません。</div>';
      }}

      // 全出走馬それぞれが1着になった場合の「堅実相手 vs 穴馬」一覧比較表
      const tbody = document.getElementById("cond-tbody");
      tbody.innerHTML = horses.map(h => {{
        const wKey = horseKey(h.num);
        const isSel = wKey === winnerNumStr;
        const badge = h.main_badge || h.tag || '—';
        const d = (h.conditional_partner_details && h.conditional_partner_details[wKey]) ? h.conditional_partner_details[wKey] : null;

        let solidCell = '<span style="color:#94a3b8;">—</span>';
        let upsetCell = '<span style="color:#94a3b8;">—</span>';
        if (d && d.solid) {{
          const s = d.solid;
          solidCell = `<span class="pair-chip pair-solid">🛡️${{s.num}}番 ${{s.name}}</span> <small style="color:#475569;">(${{s.ai_rank}}位 / ${{(Number(s.share || 0) * 100).toFixed(1)}}%)</small>`;
        }}
        if (d && d.upset) {{
          const u = d.upset;
          const uCls = u.is_strong_upset ? "pair-upset-strong" : "pair-upset";
          const uIcon = u.is_strong_upset ? "🔥" : "🚀";
          upsetCell = `<span class="pair-chip ${{uCls}}">${{uIcon}}${{u.num}}番 ${{u.name}}</span> <small style="color:#475569;">(${{u.ai_rank}}位 / <b>${{Number(u.lift || 1.0).toFixed(2)}}x</b>)</small>`;
        }}

        return `
          <tr class="${{isSel ? 'selected-winner-row' : ''}}" style="cursor:pointer;" onclick="document.getElementById('winner-select').value='${{h.num}}'; renderConditionalList();">
            <td class="rank-cell">${{h.rank}}位</td>
            <td class="left"><span class="num-circle" style="margin-right:4px;">${{h.num}}</span><b>${{h.name}}</b></td>
            <td><span class="badge ${{getBadgeClass(badge)}}">${{badge}}</span></td>
            <td class="left">${{solidCell}}</td>
            <td class="left">${{upsetCell}}</td>
            <td style="color:var(--primary); font-weight:bold;">${{h.odds}}倍</td>
          </tr>
        `;
      }}).join("");
    }}

    function renderHorseDetail() {{
      const race = currentRaces[currentRaceIdx];
      const sortedHorses = [...(race.horses || [])].sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));
      const hIdx = document.getElementById("horse-sel").value;
      const h = sortedHorses[hIdx];
      if (!h) return;

      const baseVal = parseFloat(h.base_score || 0);
      const plusVal = parseFloat(h.plus_sum || 0);
      const minusVal = parseFloat(h.minus_sum || 0);
      const condVal = plusVal + minusVal;
      const totalVal = baseVal + condVal;
      const badge = h.main_badge || h.tag || '—';

      const signals = (h.one_change_signals || []).map(s => `
        <span class="signal-detail-badge ${{getSignalCategoryClass(s)}}">${{s}}</span>
      `).join('') || '<span style="color:#94a3b8; font-size:0.85rem;">なし</span>';

      document.getElementById("horse-detail-content").innerHTML = `
        <div class="box">
          <h3 style="color:var(--primary); margin-bottom:8px;">${{h.num}}番 ${{h.name}} <small style="color:#64748b;">(${{h.rank}}位)</small></h3>
          <p><b>🏷️ 評価:</b> <span class="badge ${{getBadgeClass(badge)}}">${{badge}}</span></p>
          <p style="margin-top:4px;"><b>🏇 騎手 / 脚質:</b> ${{h.jockey}} / ${{h.running_style}}</p>
          <p style="margin-top:4px;"><b>💰 単勝オッズ:</b> ${{h.odds}}倍</p>
          <p style="margin-top:8px;"><b>⚡ 特筆シグナル:</b> ${{signals}}</p>
          <hr style="margin:10px 0; border:0; border-top:1px solid #e2e8f0;">
          <b>📊 スコア内訳:</b>
          <div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:0.85rem; margin-top:6px; line-height:1.6;">
            • 地力評価: ${{h.base_display || formatRank(h.base_rank, baseVal)}}<br>
            • 条件適性: ${{h.cond_display || formatRank(h.cond_rank, condVal)}} (加点: <span style="color:#047857; font-weight:bold;">${{plusVal > 0 ? '+' : ''}}${{plusVal.toFixed(2)}}</span> / 減点: <span style="color:#b91c1c; font-weight:bold;">${{minusVal.toFixed(2)}}</span>)<br>
            <hr style="margin:4px 0; border:0; border-top:1px dashed #cbd5e1;">
            <b>🎯 最終トータルスコア: ${{totalVal > 0 ? '+' : ''}}${{totalVal.toFixed(2)}}</b>
          </div>
          <div style="margin-top:10px;">
            <b>📈 要因分析:</b>
            <div style="background:#f8fafc; padding:10px; border-radius:6px; font-size:0.85rem; color:#334155; margin-top:4px;">
              ${{h.reasons || '特記事項なし'}}
            </div>
          </div>
        </div>
      `;
    }}
  </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_template)

print("index.html が正常に生成されました！")
