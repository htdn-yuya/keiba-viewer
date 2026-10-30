import html
import json
from pathlib import Path

import streamlit as st


# keiba_pipeline/app.py のスマホ向け設定を踏襲
st.set_page_config(
    page_title="AI競馬予測システム",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .main { background-color: #f8fafc; }
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: bold;
        background-color: #0f766e; color: white; padding: 10px;
    }
    .stButton>button:hover { background-color: #115e59; color: white; }
    .app-title {
        font-size: 1.5rem !important; font-weight: bold; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis; color: #0f172a;
    }
    .metric-card {
        background: white; border: 1px solid #cbd5e1; padding: 10px;
        border-radius: 8px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .horse-detail-box {
        background: white; border: 1px solid #cbd5e1; padding: 14px;
        border-radius: 8px; margin-bottom: 10px;
    }
    .mobile-table-wrap {
        width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;
    }
    .mobile-table {
        width: 100%; min-width: 760px; border-collapse: collapse;
        font-size: .85rem; background: white; border-radius: 8px; overflow: hidden;
    }
    .mobile-table th {
        padding: 10px 6px; text-align: center; white-space: nowrap;
        background: #f1f5f9; color: #334155; border-bottom: 2px solid #cbd5e1;
    }
    .mobile-table td {
        padding: 8px 4px; border-bottom: 1px solid #e2e8f0; white-space: nowrap;
    }
    .mobile-table tr:last-child td { border-bottom: 0; }
    .horse-number {
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; border-radius: 50%; background: #0f766e;
        color: white; font-weight: bold; font-size: .7rem;
    }
    .horse-tag {
        display: inline-block; padding: 2px 4px; border-radius: 999px;
        font-size: .65rem; font-weight: bold; background: #f1f5f9;
        color: #0f766e; border: 1px solid #cbd5e1;
    }
    .style-badge {
        display: inline-block; padding: 2px 4px; border-radius: 4px;
        font-size: .7rem; background: #e2e8f0; color: #1e293b; font-weight: bold;
    }
    @media (max-width: 600px) {
        .block-container { padding-left: .65rem; padding-right: .65rem; }
        .stTabs [data-baseweb="tab"] { padding-left: 8px; padding-right: 8px; }
    }
</style>
""",
    unsafe_allow_html=True,
)

RACECOURSES = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]


def safe_text(value, default="—"):
    if value is None or value == "":
        return default
    return str(value)


def esc(value, default="—"):
    return html.escape(safe_text(value, default))


def number_value(value, default=999.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def horse_number(horse):
    return horse.get("num", horse.get("horse_number", horse.get("number", "—")))


def extract_venue(race):
    details = str(race.get("details", ""))
    name = str(race.get("name", ""))
    for venue in RACECOURSES:
        if venue in details or venue in name:
            return venue
    return safe_text(race.get("venue"), "その他")


def to_maru_num(value):
    try:
        n = int(value)
        if 1 <= n <= 20:
            return chr(0x2460 + n - 1)
    except (TypeError, ValueError):
        pass
    return safe_text(value)


def sorted_horses(race):
    horses = race.get("horses") or []
    return sorted(
        [horse for horse in horses if isinstance(horse, dict)],
        key=lambda horse: number_value(horse.get("rank")),
    )


def load_prediction_file():
    # 既存ビューアのJSON読込優先順位を維持
    candidates = (
        sorted(Path(".").glob("predict_results_*.json"), reverse=True)
        + [Path("predict_results.json"), Path("latest_prediction.json")]
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                data = data.get("races", data.get("predictions", [data]))
            if isinstance(data, list):
                races = [item for item in data if isinstance(item, dict)]
                if races:
                    return path, races, None
            return path, [], "JSON内にレース一覧がありません。"
        except (OSError, json.JSONDecodeError) as exc:
            return path, [], f"JSONの読み込みに失敗しました: {exc}"
    return None, [], "予測JSONが見つかりません。"


def render_pace_reference(race):
    pace = race.get("pace_forecast")
    if not isinstance(pace, dict):
        return
    with st.expander("🏁 ペース展開予測（参考情報）", expanded=False):
        st.caption("ペース予測は参考情報です。AIランキング・各馬の評価スコアには加算していません。")
        coverage = pace.get("data_coverage")
        coverage_text = f"{float(coverage):.0%}" if isinstance(coverage, (int, float)) else "不明"
        st.write(f"**想定ペース：** {safe_text(pace.get('pace'), '判定保留')}")
        st.write(f"**先行争い：** {safe_text(pace.get('competition_risk'), '判定保留')}")
        st.write(f"**データ利用率：** {coverage_text}")
        st.write(f"**データ品質：** {safe_text(pace.get('data_quality'), '不明')}")
        candidates = pace.get("front_runner_candidates") or []
        if candidates:
            st.markdown("**🚩 前方候補**")
            for candidate in candidates:
                if isinstance(candidate, dict):
                    st.write(
                        f"・{to_maru_num(candidate.get('number', '—'))}番 "
                        f"{safe_text(candidate.get('name'), '不明')} / "
                        f"前方圧力：{safe_text(candidate.get('pressure'))}"
                    )
        for reason in pace.get("reasons") or []:
            st.write(f"・{reason}")
        if pace.get("scope_note"):
            st.caption(str(pace["scope_note"]))


def render_ranking(horses):
    if not horses:
        st.warning("出走馬データがありません。")
        return

    table_html = (
        '<div class="mobile-table-wrap"><table class="mobile-table">'
        '<thead><tr>'
        '<th>順位</th><th>タグ</th><th>馬番</th><th style="text-align:left">馬名</th>'
        '<th style="text-align:left">騎手</th><th>脚質</th><th>単勝</th>'
        '<th>妙味判定</th><th>軸度</th><th>穴度</th>'
        '</tr></thead><tbody>'
    )
    for horse in horses:
        rank = f"{esc(horse.get('rank'))}位"
        tag = esc(horse.get("tag"), "-")
        num = esc(horse_number(horse))
        name = esc(horse.get("name"), "不明")
        jockey = esc(horse.get("jockey"), "不明")
        style = esc(horse.get("running_style"), "不明")
        odds = esc(horse.get("odds"), "N/A")
        myumi = str(horse.get("myumi_tag") or "")
        axis = esc(horse.get("axis_stars"), "")
        hole = esc(horse.get("hole_stars"), "")

        if "旨味" in myumi:
            myumi_badge = '<span style="color:#d97706;font-weight:bold;font-size:.7rem;">🔥 旨味大</span>'
        elif "トリガミ" in myumi:
            myumi_badge = '<span style="color:#dc2626;font-weight:bold;font-size:.7rem;">⚠️ 注意</span>'
        else:
            myumi_badge = "-"

        table_html += (
            '<tr>'
            f'<td style="text-align:center;font-weight:bold;color:#0f172a;">{rank}</td>'
            f'<td style="text-align:center;"><span class="horse-tag">{tag}</span></td>'
            f'<td style="text-align:center;"><span class="horse-number">{num}</span></td>'
            f'<td style="text-align:left;font-weight:bold;color:#0f172a;">{name}</td>'
            f'<td style="text-align:left;color:#475569;">{jockey}</td>'
            f'<td style="text-align:center;"><span class="style-badge">{style}</span></td>'
            f'<td style="text-align:center;font-weight:bold;color:#0f766e;">{odds}倍</td>'
            f'<td style="text-align:center;">{myumi_badge}</td>'
            f'<td style="text-align:center;color:#d97706;font-size:.75rem;">{axis}</td>'
            f'<td style="text-align:center;color:#d97706;font-size:.75rem;">{hole}</td>'
            '</tr>'
        )
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.caption("スマホでは表を左右にスワイプして確認できます。")


def render_prediction_tab(race):
    horses = sorted_horses(race)
    volatility = race.get("volatility") or {}
    top_horse = horses[0] if horses else None
    top_odds = top_horse.get("odds", "N/A") if top_horse else "N/A"

    st.markdown("### 🧠 レースインサイト")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="metric-card"><small>レース性質</small><br><b>{esc(volatility.get("label"), "未判定")}</b></div>',
            unsafe_allow_html=True,
        )
    with col2:
        top_display = f'{esc(horse_number(top_horse))}番 ({esc(top_odds)}倍)' if top_horse else "—"
        st.markdown(
            f'<div class="metric-card"><small>本命予測1位</small><br><b>{top_display}</b></div>',
            unsafe_allow_html=True,
        )
    with col3:
        myumi_count = sum(1 for horse in horses if "旨味" in str(horse.get("myumi_tag", "")))
        st.markdown(
            f'<div class="metric-card"><small>妙味馬検知</small><br><b>{myumi_count}頭</b></div>',
            unsafe_allow_html=True,
        )

    decision = volatility.get("decision") or race.get("decision_text")
    if decision:
        st.markdown(
            f"<small style='color:#475569;'>💡 {esc(decision)}</small>",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

    render_pace_reference(race)
    st.subheader("📊 出走馬予測ランキング")
    render_ranking(horses)


def render_horse_detail_tab(race):
    st.subheader("🔍 個別馬の詳細分析・要因比較")
    st.markdown(
        "<small style='color:#64748b;'>選択した馬のAI評価スコアの内訳（基準点・加点・減点合計）とシグナルを詳細に確認できます。</small>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    horses = sorted_horses(race)
    if not horses:
        st.warning("出走馬データがありません。")
        return

    horse_options = [
        f"{horse.get('rank', '—')}位: {to_maru_num(horse_number(horse))}番 "
        f"{safe_text(horse.get('name'), '不明')} "
        f"({horse.get('tag') if horse.get('tag') else '一般'})"
        for horse in horses
    ]
    selected_horse_str = st.selectbox("詳細を確認する馬を選択", horse_options, key="detail_horse")
    horse = horses[horse_options.index(selected_horse_str)]

    base_val = horse.get("base_score", 0.0)
    plus_val = horse.get("plus_sum", 0.0)
    minus_val = horse.get("minus_sum", 0.0)
    raw_val = horse.get("raw_score", 0.0)
    pace_adv = horse.get("pace_adv", 0.0)
    track_adv = horse.get("track_adv", 0.0)
    prev_day_adv = horse.get("prev_day_adv", 0.0)
    bias_sum = horse.get("bias_sum", 0.0)
    myumi_display = f"/ 判定: {horse['myumi_tag']}" if horse.get("myumi_tag") else ""
    reasons = horse.get("reasons") or "特筆すべき特記事項なし"
    if isinstance(reasons, list):
        reasons = "<br>".join(esc(reason) for reason in reasons)
    else:
        reasons = esc(reasons)

    st.markdown(
        f"""<div class="horse-detail-box">
<h4 style="margin:0; color:#0f766e;">{to_maru_num(horse_number(horse))}番 {esc(horse.get("name"), "不明")} <span style="font-size:0.9rem; color:#475569;">({esc(horse.get("rank"))}位)</span></h4>
<hr style="margin:8px 0; border:0; border-top:1px solid #e2e8f0;">
<b>🏷️ タグ:</b> {esc(horse.get("tag"), "特になし")}<br>
<b>🏇 騎手 / 脚質:</b> {esc(horse.get("jockey"))} / {esc(horse.get("running_style"))}<br>
<b>💰 単勝オッズ:</b> {esc(horse.get("odds"), "N/A")}倍 {html.escape(myumi_display)}<br><br>
<b>📊 AI総合評価スコアの内訳:</b><br>
<div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:0.85rem; color:#1e293b; margin-top:4px;">
<b>• 基準点（スタートライン）:</b> {float(base_val):+.2f}<br>
<b>• 📈 加点合計（強みの積み上げ）:</b> <span style="color:#047857; font-weight:bold;">{float(plus_val):+.2f}</span><br>
<b>• 📉 減点合計（懸念・リスク）:</b> <span style="color:#b91c1c; font-weight:bold;">{float(minus_val):+.2f}</span><br>
<b>• 🧩 後付けバイアス補正合計:</b> <span style="color:#2563eb; font-weight:bold;">{float(bias_sum):+.2f}</span><br>
<div style="font-size:0.8rem; color:#475569; padding-left:12px; margin-top:2px;">
- ペース展開補正: {float(pace_adv):+.2f}<br>
- 当日馬場バイアス: {float(track_adv):+.2f}<br>
- 前日傾向補正: {float(prev_day_adv):+.2f}
</div>
<hr style="margin:6px 0; border:0; border-top:1px dashed #cbd5e1;">
<b>🎯 最終トータルスコア: {float(raw_val):+.2f}</b>
</div><br>
<b>📈 要因分析・モデル寄与度の詳細:</b><br>
<div style="background:#f8fafc; padding:8px; border-radius:6px; font-size:0.85rem; color:#334155; margin-top:4px;">
{reasons}
</div>
</div>""",
        unsafe_allow_html=True,
    )


json_path, races_list, load_error = load_prediction_file()
st.markdown('<p class="app-title">🏇 AI競馬予測システム</p>', unsafe_allow_html=True)
st.write("学習済みモデルによる高精度レース予測＆インサイト分析アプリ")

if json_path:
    st.caption(f"📁 読込データ：{json_path.name}")
if load_error:
    st.error(load_error)
    st.stop()
if not races_list:
    st.warning("予測JSONにレースがありません。")
    st.stop()

# 一括JSONの各レースに競馬場情報を付加し、ビューア側のフィルターで絞る
for race in races_list:
    race["venue"] = extract_venue(race)

with st.sidebar:
    st.markdown("### ⚙️ レース選択")
    available_venues = sorted({race["venue"] for race in races_list})
    venue_options = ["すべて"] + available_venues
    selected_venue = st.selectbox("競馬場", venue_options, key="venue_filter")
    filtered_races = [
        race for race in races_list
        if selected_venue == "すべて" or race["venue"] == selected_venue
    ]

    if not filtered_races:
        st.warning("選択した競馬場のレースがありません。")
        st.stop()

    race_labels = []
    for index, race in enumerate(filtered_races):
        race_name = safe_text(race.get("name"), "レース名不明")
        detail = str(race.get("details", "")).split("/")[0].strip()
        label = f"{race['venue']}｜{race_name}｜{detail}" if detail else f"{race['venue']}｜{race_name}"
        race_labels.append(f"{index + 1:02d}. {label}")

    selected_label = st.selectbox("対象レース", race_labels, key="target_race")
    selected_race = filtered_races[race_labels.index(selected_label)]
    st.divider()
    st.caption(f"読込レース数：{len(races_list)}")
    st.caption(f"競馬場内レース数：{len(filtered_races)}")
    st.caption("表示専用：予測・学習処理は実行しません。")

# 元アプリの結果画面と同じ情報階層・タブ構成
st.markdown('<p class="app-title">🏇 AI競馬予測結果</p>', unsafe_allow_html=True)
st.markdown("---")
st.success(f"🎯 {safe_text(selected_race.get('name'), 'レース名不明')}")
details = str(selected_race.get("details", "")).replace("\n", " ")
if details:
    st.caption(f"📍 {details}")

tab_list, tab_detail = st.tabs(["📋 予測一覧 ＆ インサイト", "🔍 個別馬・比較分析"])
with tab_list:
    render_prediction_tab(selected_race)
with tab_detail:
    render_horse_detail_tab(selected_race)

st.markdown("<br>", unsafe_allow_html=True)
