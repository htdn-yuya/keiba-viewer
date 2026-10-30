import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# 元の keiba_pipeline/app.py と同じスマホ前提の画面設定
st.set_page_config(
    page_title="AI競馬予測システム",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background-color: #f8fafc; }
    .block-container { max-width: 760px; padding: 1rem .85rem 2rem; }
    .app-title { font-size: 1.5rem !important; font-weight: 800; color: #0f172a; }
    .metric-card {
        background: #fff; border: 1px solid #cbd5e1; padding: 12px;
        border-radius: 8px; text-align: center; margin: 5px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,.05);
    }
    .horse-detail-box {
        background: #fff; border: 1px solid #cbd5e1; padding: 14px;
        border-radius: 8px; margin-bottom: 10px; overflow-wrap: anywhere;
    }
    .mobile-table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .mobile-table {
        border-collapse: collapse; min-width: 820px; width: 100%;
        font-size: .82rem; background: white; border-radius: 8px;
    }
    .mobile-table th {
        background: #f1f5f9; color: #334155; border-bottom: 2px solid #cbd5e1;
        padding: 10px 7px; white-space: nowrap;
    }
    .mobile-table td { border-bottom: 1px solid #e2e8f0; padding: 9px 7px; white-space: nowrap; }
    .mobile-table tr:last-child td { border-bottom: 0; }
    .horse-num {
        display:inline-flex; align-items:center; justify-content:center;
        width:23px; height:23px; border-radius:50%; background:#0f766e;
        color:white; font-weight:800; font-size:.72rem;
    }
    .style-badge {
        display:inline-block; padding:2px 5px; border-radius:4px;
        font-size:.7rem; background:#e2e8f0; color:#1e293b; font-weight:700;
    }
    .pace-card {
        background:#fff; border:1px solid #cbd5e1; border-radius:8px;
        padding:12px; margin:6px 0;
    }
    div.stButton > button { width:100%; border-radius:8px; font-weight:700; }
    @media (max-width: 600px) {
        .block-container { padding: .7rem .65rem 1.5rem; }
        h1 { font-size: 1.45rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] { padding: 9px 8px; font-size: .82rem; }
    }
</style>
""",
    unsafe_allow_html=True,
)


def text_value(value, default="—"):
    if value is None or value == "":
        return default
    return str(value)


def safe_html(value, default="—"):
    return html.escape(text_value(value, default))


def number_value(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def horse_num(horse):
    return horse.get("num", horse.get("horse_number", horse.get("number", "—")))


def maru_num(value):
    try:
        n = int(value)
        if 1 <= n <= 20:
            return chr(0x2460 + n - 1)
    except (TypeError, ValueError):
        pass
    return text_value(value)


def sorted_horses(race):
    horses = race.get("horses") or []
    return sorted(
        [h for h in horses if isinstance(h, dict)],
        key=lambda h: number_value(h.get("rank"), 999),
    )


def race_venue(race):
    details = str(race.get("details", ""))
    name = str(race.get("name", ""))
    for venue in ("札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"):
        if venue in details or venue in name:
            return venue
    return text_value(race.get("venue"), "競馬場不明")


def load_races():
    # 既存ビューアの読み込み優先順位を維持
    candidates = (
        sorted(Path(".").glob("predict_results_*.json"), reverse=True)
        + [Path("predict_results.json"), Path("latest_prediction.json")]
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data = data.get("races", data.get("predictions", [data]))
            if isinstance(data, list):
                races = [r for r in data if isinstance(r, dict)]
                if races:
                    return path, races, None
            return path, [], "JSON内にレース一覧がありません。"
        except (OSError, json.JSONDecodeError) as exc:
            return path, [], f"JSONの読み込みに失敗しました: {exc}"
    return None, [], "予測JSONが見つかりません。"


def render_horse_table(horses):
    if not horses:
        st.warning("出走馬データがありません。")
        return
    rows = []
    for h in horses:
        myumi = str(h.get("myumi_tag", ""))
        if "旨味" in myumi:
            myumi_badge = '<span style="color:#d97706;font-weight:bold;">🔥 旨味大</span>'
        elif "トリガミ" in myumi:
            myumi_badge = '<span style="color:#dc2626;font-weight:bold;">⚠️ 注意</span>'
        else:
            myumi_badge = "—"
        tag = safe_html(h.get("tag"), "-")
        num = safe_html(horse_num(h))
        name = safe_html(h.get("name"), "不明")
        jockey = safe_html(h.get("jockey"), "不明")
        style = safe_html(h.get("running_style"), "不明")
        odds = safe_html(h.get("odds", h.get("win")), "—")
        axis = safe_html(h.get("axis_stars"), "—")
        hole = safe_html(h.get("hole_stars"), "—")
        rank = safe_html(h.get("rank"))
        rows.append(
            f"<tr><td style='text-align:center;font-weight:bold'>{rank}位</td>"
            f"<td style='text-align:center'>{tag}</td>"
            f"<td style='text-align:center'><span class='horse-num'>{num}</span></td>"
            f"<td style='font-weight:bold'>{name}</td><td>{jockey}</td>"
            f"<td style='text-align:center'><span class='style-badge'>{style}</span></td>"
            f"<td style='text-align:center;font-weight:bold;color:#0f766e'>{odds}倍</td>"
            f"<td style='text-align:center'>{myumi_badge}</td>"
            f"<td style='text-align:center;color:#d97706'>{axis}</td>"
            f"<td style='text-align:center;color:#d97706'>{hole}</td></tr>"
        )
    st.markdown(
        '<div class="mobile-table-wrap"><table class="mobile-table">'
        '<thead><tr><th>順位</th><th>タグ</th><th>馬番</th><th>馬名</th>'
        '<th>騎手</th><th>脚質</th><th>単勝</th><th>妙味判定</th>'
        '<th>軸度</th><th>穴度</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.caption("表は左右にスワイプして全項目を確認できます。")


def render_pace_forecast(race):
    pace = race.get("pace_forecast")
    if not isinstance(pace, dict):
        return
    with st.expander("🏁 ペース・レース展開予測", expanded=False):
        st.caption("参考情報です。元アプリと同様、AIランキング・評価スコアとは独立して表示します。")
        pace_fields = [
            ("想定ペース", pace.get("pace")),
            ("先行争い", pace.get("competition_risk")),
            ("データ品質", pace.get("data_quality")),
        ]
        for label, value in pace_fields:
            st.markdown(f"**{label}：** {safe_html(value)}")
        coverage = pace.get("data_coverage")
        if coverage is not None:
            st.markdown(f"**データ利用率：** {number_value(coverage, 0):.0%}")
        candidates = pace.get("front_runner_candidates") or []
        if candidates:
            st.markdown("**🚩 前方候補**")
            for c in candidates:
                if not isinstance(c, dict):
                    continue
                st.write(
                    f"・{maru_num(c.get('number', '—'))}番 {text_value(c.get('name'))}"
                    f" / 圧力：{text_value(c.get('pressure'))}"
                )
        for reason in pace.get("reasons") or []:
            st.write(f"・{reason}")
        if pace.get("scope_note"):
            st.caption(str(pace["scope_note"]))


def render_prediction_tab(race):
    horses = sorted_horses(race)
    volatility = race.get("volatility") or {}
    top = horses[0] if horses else {}
    top_odds = text_value(top.get("odds", top.get("win"))) if top else "—"
    myumi_count = sum("旨味" in str(h.get("myumi_tag", "")) for h in horses)

    st.markdown("### 🧠 レースインサイト")
    # 元画面の3指標カードを、スマホで読みやすい縦並びにする
    metrics = [
        ("レース性質", text_value(volatility.get("label"), "未判定")),
        ("本命予測1位", f"{maru_num(horse_num(top))}番 ({top_odds}倍)" if top else "—"),
        ("妙味馬検知", f"{myumi_count}頭"),
    ]
    for label, value in metrics:
        st.markdown(
            f'<div class="metric-card"><small>{html.escape(label)}</small><br>'
            f'<b>{html.escape(value)}</b></div>',
            unsafe_allow_html=True,
        )
    if volatility.get("decision"):
        st.markdown(
            f"<small style='color:#475569;'>💡 {safe_html(volatility.get('decision'))}</small>",
            unsafe_allow_html=True,
        )

    render_pace_forecast(race)
    st.subheader("📊 出走馬予測ランキング")
    render_horse_table(horses)


def render_horse_detail_tab(race):
    horses = sorted_horses(race)
    st.subheader("🔍 個別馬の詳細分析・要因比較")
    st.markdown(
        "<small style='color:#64748b;'>選択した馬のAI評価スコアの内訳（基準点・加点・減点合計）とシグナルを詳細に確認できます。</small>",
        unsafe_allow_html=True,
    )
    if not horses:
        st.warning("出走馬データがありません。")
        return

    labels = [
        f"{h.get('rank', '—')}位: {maru_num(horse_num(h))}番 {h.get('name', '不明')} "
        f"({h.get('tag') or '一般'})"
        for h in horses
    ]
    selected = st.selectbox("詳細を確認する馬を選択", labels, key="detail_horse")
    h = horses[labels.index(selected)]

    base = number_value(h.get("base_score"))
    plus = number_value(h.get("plus_sum"))
    minus = number_value(h.get("minus_sum"))
    raw = number_value(h.get("raw_score"))
    bias = number_value(h.get("bias_sum"))
    pace = number_value(h.get("pace_adv"))
    track = number_value(h.get("track_adv"))
    prev = number_value(h.get("prev_day_adv"))
    odds = text_value(h.get("odds", h.get("win")))
    myumi = f" / 判定: {h.get('myumi_tag')}" if h.get("myumi_tag") else ""

    st.markdown(
        f"""<div class="horse-detail-box">
<h4 style="margin:0;color:#0f766e;">{maru_num(horse_num(h))}番 {safe_html(h.get('name'), '不明')} <span style="font-size:.9rem;color:#475569;">({safe_html(h.get('rank'))}位)</span></h4>
<hr style="margin:8px 0;border:0;border-top:1px solid #e2e8f0;">
<b>🏷️ タグ:</b> {safe_html(h.get('tag'), '特になし')}<br>
<b>🏇 騎手 / 脚質:</b> {safe_html(h.get('jockey'))} / {safe_html(h.get('running_style'))}<br>
<b>💰 単勝オッズ:</b> {html.escape(odds)}倍 {html.escape(myumi)}<br><br>
<b>📊 AI総合評価スコアの内訳:</b><br>
<div style="background:#f1f5f9;padding:10px;border-radius:6px;font-size:.85rem;color:#1e293b;margin-top:4px;">
<b>• 基準点（スタートライン）:</b> {base:+.2f}<br>
<b>• 📈 加点合計（強みの積み上げ）:</b> <span style="color:#047857;font-weight:bold;">{plus:+.2f}</span><br>
<b>• 📉 減点合計（懸念・リスク）:</b> <span style="color:#b91c1c;font-weight:bold;">{minus:+.2f}</span><br>
<b>• 🧩 後付けバイアス補正合計:</b> <span style="color:#2563eb;font-weight:bold;">{bias:+.2f}</span><br>
<div style="font-size:.8rem;color:#475569;padding-left:12px;margin-top:2px;">
- ペース展開補正: {pace:+.2f}<br>
- 当日馬場バイアス: {track:+.2f}<br>
- 前日傾向補正: {prev:+.2f}
</div>
<hr style="margin:6px 0;border:0;border-top:1px dashed #cbd5e1;">
<b>🎯 最終トータルスコア: {raw:+.2f}</b>
</div><br>
<b>📈 要因分析・モデル寄与度の詳細:</b><br>
<div style="background:#f8fafc;padding:8px;border-radius:6px;font-size:.85rem;color:#334155;margin-top:4px;">
{h.get('reasons') or safe_html(h.get('score_comment'), '特筆すべき特記事項なし')}
</div></div>""",
        unsafe_allow_html=True,
    )


json_path, races, load_error = load_races()
st.markdown('<p class="app-title">🏇 AI競馬予測システム</p>', unsafe_allow_html=True)
st.write("学習済みモデルによるレース予測＆インサイト分析")
if json_path:
    st.caption(f"📁 読込データ：{json_path.name}")

if load_error:
    st.error(load_error)
    st.stop()
if not races:
    st.warning("予測JSONにレースがありません。")
    st.stop()

# 元アプリのレース切替操作を、保存済み複数レースJSON向けに置き換え
race_labels = [
    f"{race_venue(r)}｜{text_value(r.get('name'), 'レース名不明')}｜{str(r.get('details', '')).splitlines()[0]}"
    for r in races
]
selected_label = st.selectbox("🔄 レース番号・対象レースを切替", race_labels, key="race_select")
race = races[race_labels.index(selected_label)]

st.success(f"🎯 {text_value(race.get('name'), 'レース名不明')}")
details = str(race.get("details", "")).replace("\n", " ").strip()
if details:
    st.caption(f"📍 {details[:240]}")

tab_list, tab_detail = st.tabs(["📋 予測一覧 ＆ インサイト", "🔍 個別馬・比較分析"])
with tab_list:
    render_prediction_tab(race)
with tab_detail:
    render_horse_detail_tab(race)

st.caption("表示専用ビューア：予測・学習処理は実行せず、保存済みJSONのみを表示します。")
