import json
import os
from pathlib import Path

# ================= 設定 =================
JSON_PATH = Path(r"C:\keiba\keiba_pipeline\reports\latest_prediction.json")
OUTPUT_HTML = Path(r"C:\Streamlit_app\index.html")
ENV_PATH = Path(r"C:\keiba_env\.env")
# ========================================


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
    :root {{ --primary: #0f766e; --bg: #f8fafc; --card: #ffffff; --border: #cbd5e1; --text: #0f172a; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ background: var(--bg); color: var(--text); padding: 16px; max-width: 1000px; margin: auto; }}

    #lock-modal {{ position: fixed; inset: 0; background: rgba(15,23,42,0.85); display: flex; align-items: center; justify-content: center; z-index: 9999; backdrop-filter: blur(4px); }}
    .lock-box {{ background: white; padding: 28px; border-radius: 12px; max-width: 360px; width: 90%; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
    .lock-box input {{ width: 100%; padding: 10px; margin: 12px 0; border: 1px solid var(--border); border-radius: 6px; font-size: 1rem; }}
    .lock-box button {{ width: 100%; padding: 10px; background: var(--primary); color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}

    .header-bar {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 16px; background: white; padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border); }}
    select {{ padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border); font-weight: bold; background: white; }}

    .tabs-row {{ display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 14px; scrollbar-width: thin; }}
    .r-btn {{ padding: 8px 14px; border: 1px solid var(--border); background: white; border-radius: 6px; cursor: pointer; font-weight: bold; white-space: nowrap; }}
    .r-btn.active {{ background: var(--primary); color: white; border-color: var(--primary); }}

    .sub-tabs {{ display: flex; border-bottom: 2px solid var(--border); margin-bottom: 16px; }}
    .sub-btn {{ padding: 8px 16px; border: none; background: none; cursor: pointer; font-weight: bold; color: #64748b; }}
    .sub-btn.active {{ color: var(--primary); border-bottom: 3px solid var(--primary); }}

    .tbl-wrap {{ overflow-x: auto; background: white; border-radius: 8px; border: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; white-space: nowrap; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid #e2e8f0; text-align: center; }}
    th {{ background: #f1f5f9; color: #475569; }}
    td.left {{ text-align: left; }}

    .badge {{ display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 0.72rem; font-weight: bold; }}
    .badge-iron {{ background:#fef3c7; color:#b45309; border:1px solid #fcd34d; }}
    .badge-hon {{ background:#dcfce7; color:#15803d; border:1px solid #86efac; }}
    .badge-aite {{ background:#e0f2fe; color:#0369a1; border:1px solid #7dd3fc; }}
    .badge-burst {{ background:#ffedd5; color:#c2410c; border:1px solid #fdba74; }}
    .badge-solid {{ background:#f3e8ff; color:#6d28d9; border:1px solid #d8b4fe; }}
    .badge-none {{ color:#94a3b8; }}
    .num-circle {{ display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: var(--primary); color: white; font-weight: bold; font-size: 0.75rem; }}

    .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }}
    .metric-card {{ background: white; border: 1px solid var(--border); padding: 12px; border-radius: 8px; text-align: center; }}
    .box {{ background: white; border: 1px solid var(--border); padding: 14px; border-radius: 8px; margin-bottom: 12px; }}
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
      <h2>🏇 AI競馬予測ビューアー</h2>
      <div>
        <label style="font-size:0.85rem; font-weight:bold;">競馬場: </label>
        <select id="venue-select" onchange="onVenueChange()"></select>
      </div>
    </div>

    <div class="tabs-row" id="race-tabs"></div>
    <div class="box" id="race-info" style="margin-bottom:12px;"></div>

    <div class="sub-tabs">
      <button class="sub-btn active" onclick="switchSubTab('list')">📋 AI予測一覧</button>
      <button class="sub-btn" onclick="switchSubTab('pace')">🏁 レース展開</button>
      <button class="sub-btn" onclick="switchSubTab('detail')">🐎 馬詳細</button>
    </div>

    <div id="view-list" class="tab-content"></div>
    <div id="view-pace" class="tab-content" style="display:none;"></div>
    <div id="view-detail" class="tab-content" style="display:none;"></div>
  </div>

  <script>
    const RAW_DATA = {json.dumps(races_data, ensure_ascii=False)};
    const APP_PWD = "{APP_PASSWORD}";

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
    let currentSubTab = "list";

    function extractVenue(details) {{
      const m = details.match(/\\d+回\\s*\\n\\s*([^\\s\\d]+)/);
      return m ? m[1].trim() : "その他";
    }}

    // SABCDランクの色・絵文字装飾関数
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
      RAW_DATA.forEach(r => r.venue = extractVenue(r.details || ""));
      const venues = [...new Set(RAW_DATA.map(r => r.venue))];
      const sel = document.getElementById("venue-select");
      sel.innerHTML = venues.map(v => `<option value="${{v}}">${{v}}</option>`).join("");
      currentVenue = venues[0];
      onVenueChange();
    }}

    function onVenueChange() {{
      currentVenue = document.getElementById("venue-select").value;
      currentRaces = RAW_DATA.filter(r => r.venue === currentVenue);
      currentRaces.sort((a,b) => parseInt(a.id||0) - parseInt(b.id||0));
      currentRaceIdx = 0;
      renderRaceTabs();
      renderCurrentRace();
    }}

    function renderRaceTabs() {{
      const tabsEl = document.getElementById("race-tabs");
      tabsEl.innerHTML = currentRaces.map((r, i) => `
        <button class="r-btn ${{i === currentRaceIdx ? 'active' : ''}}" onclick="selectRace(${{i}})">${{r.id || (i+1)}}R</button>
      `).join("");
    }}

    function selectRace(idx) {{
      currentRaceIdx = idx;
      renderRaceTabs();
      renderCurrentRace();
    }}

    function switchSubTab(tab) {{
      currentSubTab = tab;
      document.querySelectorAll(".sub-btn").forEach((b, i) => {{
        b.classList.toggle("active", ["list", "pace", "detail"][i] === tab);
      }});
      document.getElementById("view-list").style.display = tab === "list" ? "block" : "none";
      document.getElementById("view-pace").style.display = tab === "pace" ? "block" : "none";
      document.getElementById("view-detail").style.display = tab === "detail" ? "block" : "none";
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

      const singleDetails = (race.details || "").replace(/\\s+/g, ' ');
      document.getElementById("race-info").innerHTML = `
        <h3>${{race.id || ''}}R: ${{race.name}}</h3>
        <p style="font-size:0.85rem; color:#64748b; margin-top:4px;">📍 ${{singleDetails}}</p>
      `;

      const horses = race.horses || [];
      document.getElementById("view-list").innerHTML = `
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>順位</th><th>評価</th><th>馬番</th><th class="left">馬名</th><th class="left">騎手</th><th>脚質</th><th>単勝</th><th>地力</th><th>適性</th></tr></thead>
            <tbody>
              ${{horses.map(h => `
                <tr>
                  <td><b>${{h.rank}}位</b></td>
                  <td><span class="badge ${{getBadgeClass(h.main_badge||'—')}}">${{h.main_badge||'—'}}</span></td>
                  <td><span class="num-circle">${{h.num}}</span></td>
                  <td class="left"><b>${{h.name}}</b></td>
                  <td class="left" style="color:#64748b;">${{h.jockey}}</td>
                  <td><span style="background:#e2e8f0; padding:2px 5px; border-radius:4px; font-size:0.75rem;">${{h.running_style}}</span></td>
                  <td style="color:var(--primary); font-weight:bold;">${{h.odds}}倍</td>
                  <td>${{formatRank(h.base_rank, h.base_score)}}</td>
                  <td>${{formatRank(h.cond_rank, parseFloat(h.plus_sum||0)+parseFloat(h.minus_sum||0))}}</td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;

      const pace = race.pace_forecast || {{}};
      const cands = pace.front_runner_candidates || [];
      document.getElementById("view-pace").innerHTML = `
        <div class="metric-grid">
          <div class="metric-card"><small>⏱️ 想定ペース</small><br><b>${{pace.pace || '不明'}}</b></div>
          <div class="metric-card"><small>⚔️ 先行争い</small><br><b>${{pace.competition_risk || '不明'}}</b></div>
          <div class="metric-card"><small>🚩 前方候補</small><br><b>${{pace.candidate_count || 0}}頭</b></div>
        </div>
        <div class="box">
          <h4 style="margin-bottom:8px;">🚀 展開を引っ張る注目馬</h4>
          ${{cands.length ? cands.map(c => `
            <div style="margin-bottom:6px;">
              <span class="num-circle" style="width:20px; height:20px; font-size:0.7rem;">${{c.number}}</span>
              <b>${{c.name}}</b> <small style="color:#64748b;">(圧力: ${{c.pressure}})</small>
            </div>
          `).join('') : '<p style="color:#94a3b8; font-size:0.85rem;">候補なし</p>'}}
        </div>
      `;

      document.getElementById("view-detail").innerHTML = `
        <div style="margin-bottom:12px;">
          <select id="horse-sel" style="width:100%;" onchange="renderHorseDetail()">
            ${{horses.map((h, i) => `<option value="${{i}}">${{h.rank}}位: ${{h.num}}番 ${{h.name}}</option>`).join('')}}
          </select>
        </div>
        <div id="horse-detail-content"></div>
      `;
      renderHorseDetail();
    }}

    function renderHorseDetail() {{
      const race = currentRaces[currentRaceIdx];
      const hIdx = document.getElementById("horse-sel").value;
      const h = race.horses[hIdx];
      if (!h) return;

      const baseVal = parseFloat(h.base_score || 0);
      const plusVal = parseFloat(h.plus_sum || 0);
      const minusVal = parseFloat(h.minus_sum || 0);
      const condVal = plusVal + minusVal;
      const totalVal = baseVal + condVal;

      const signals = (h.one_change_signals || []).map(s => `
        <span style="display:inline-block; padding:2px 6px; background:#e0f2fe; color:#0369a1; border-radius:4px; font-size:0.75rem; font-weight:bold; margin-right:4px;">${{s}}</span>
      `).join('') || '<span style="color:#94a3b8; font-size:0.85rem;">なし</span>';

      document.getElementById("horse-detail-content").innerHTML = `
        <div class="box">
          <h3 style="color:var(--primary); margin-bottom:8px;">${{h.num}}番 ${{h.name}} <small style="color:#64748b;">(${{h.rank}}位)</small></h3>
          <p><b>🏷️ 評価:</b> <span class="badge ${{getBadgeClass(h.main_badge||'—')}}">${{h.main_badge||'—'}}</span></p>
          <p style="margin-top:4px;"><b>🏇 騎手 / 脚質:</b> ${{h.jockey}} / ${{h.running_style}}</p>
          <p style="margin-top:4px;"><b>💰 単勝オッズ:</b> ${{h.odds}}倍</p>
          <p style="margin-top:8px;"><b>⚡ 特筆シグナル:</b> ${{signals}}</p>
          <hr style="margin:10px 0; border:0; border-top:1px solid #e2e8f0;">
          <b>📊 スコア内訳:</b>
          <div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:0.85rem; margin-top:6px; line-height:1.6;">
            • 地力評価: ${{formatRank(h.base_rank, baseVal)}}<br>
            • 条件適性: ${{formatRank(h.cond_rank, condVal)}} (加点: <span style="color:#047857; font-weight:bold;">${{plusVal > 0 ? '+' : ''}}${{plusVal.toFixed(2)}}</span> / 減点: <span style="color:#b91c1c; font-weight:bold;">${{minusVal.toFixed(2)}}</span>)<br>
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
