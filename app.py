import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st

# スマホ向けレイアウト＆ページ設定
st.set_page_config(
    page_title="AI競馬予測システム",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# スマホ向けカスタムCSS & テーブル・バッジスタイル
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

RACECOURSES = [
    "札幌",
    "函館",
    "福島",
    "新潟",
    "東京",
    "中山",
    "中京",
    "京都",
    "阪神",
    "小倉",
]


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
    candidates = sorted(Path(".").glob("predict_results_*.json"), reverse=True) + [
        Path("predict_results.json"),
        Path("latest_prediction.json"),
    ]
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


def render_ranking(horses):
    if not horses:
        st.warning("出走馬データがありません。")
        return

    table_html = (
        '<div class="mobile-table-wrap"><table class="mobile-table">'
        "<thead><tr>"
        '<th>順位</th><th>タグ</th><th>馬番</th><th style="text-align:left">馬名</th>'
        '<th style="text-align:left">騎手</th><th>脚質</th><th>単勝</th>'
        "<th>妙味判定</th><th>軸度</th><th>穴度</th>"
        "</tr></thead><tbody>"
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
            "<tr>"
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
            "</tr>"
        )
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.caption("スマホでは表を左右にスワイプして確認できます。")


def render_prediction_tab(races_list):
    available_venues = sorted({race["venue"] for race in races_list})
    venue_col, race_col = st.columns([1, 2])
    with venue_col:
        selected_venue = st.selectbox(
            "競馬場",
            ["すべて"] + available_venues,
            key="table_venue_filter",
        )
    filtered_races = [
        race
        for race in races_list
        if selected_venue == "すべて" or race["venue"] == selected_venue
    ]
    if not filtered_races:
        st.warning("選択した競馬場のレースがありません。")
        return None
    race_labels = []
    for index, item in enumerate(filtered_races):
        race_name = safe_text(item.get("name"), "レース名不明")
        detail = str(item.get("details", "")).split("/")[0].strip()
        label = (
            f"{item['venue']}｜{race_name}｜{detail}"
            if detail
            else f"{item['venue']}｜{race_name}"
        )
        race_labels.append(f"{index + 1:02d}. {label}")
    with race_col:
        selected_label = st.selectbox(
            "対象レース",
            race_labels,
            key="table_target_race",
        )
    race = filtered_races[race_labels.index(selected_label)]
    st.caption(f"表示対象：{len(filtered_races)}レース / 全{len(races_list)}レース")
    horses = sorted_horses(race)
    volatility = race.get("volatility") or {}
    top_horse = horses[0] if horses else None
    top_odds = top_horse.get("odds", "N/A") if top_horse else "N/A"

    st.markdown("### 🧾 レースサマリ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="metric-card"><small>レース性質</small><br><b>{esc(volatility.get("label"), "未判定")}</b></div>',
            unsafe_allow_html=True,
        )
    with col2:
        top_display = (
            f"{esc(horse_number(top_horse))}番 ({esc(top_odds)}倍)"
            if top_horse
            else "—"
        )
        st.markdown(
            f'<div class="metric-card"><small>本命予測1位</small><br><b>{top_display}</b></div>',
            unsafe_allow_html=True,
        )
    with col3:
        myumi_count = sum(
            1 for horse in horses if "旨味" in str(horse.get("myumi_tag", ""))
        )
        st.markdown(
            f'<div class="metric-card"><small>妙味馬検知</small><br><b>{myumi_count}頭</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 出走馬予測ランキング")
    render_ranking(horses)
    return race


def render_race_development_tab(race):
    pace = race.get("pace_forecast") or {}
    st.markdown("### 🏁 レース展開")
    if pace:

        def stars(value):
            if value is None or pd.isna(value):
                return "—"
            try:
                score = max(0, min(5, int(round(float(value) * 5))))
                return "★" * score if score else "—"
            except (TypeError, ValueError):
                return "—"

        pc1, pc2, pc3 = st.columns(3)
        for col, icon, label, value in [
            (pc1, "⏱️", "想定ペース", pace.get("pace", "判定材料不足")),
            (pc2, "⚔️", "先行争い", pace.get("competition_risk", "不明")),
            (
                pc3,
                "🚩",
                "前方候補",
                f"{len(pace.get('front_runner_candidates', []))}頭",
            ),
        ]:
            with col:
                with st.container(border=True):
                    st.markdown(
                        f'<div style="font-size:0.78rem; line-height:1.2; color:#475569; '
                        f'font-weight:600; white-space:nowrap;">{icon} {label}</div>'
                        f'<div style="font-size:1.02rem; line-height:1.25; font-weight:700; '
                        f'overflow-wrap:anywhere; word-break:keep-all; margin-top:4px;">{value}</div>',
                        unsafe_allow_html=True,
                    )

        candidates = pace.get("front_runner_candidates", [])
        st.markdown("#### 🚀 前に行きそうな馬")
        if candidates:
            for candidate in candidates:
                if isinstance(candidate, dict):
                    mark = to_maru_num(candidate.get("number", "?"))
                    outside = (
                        " ↗ 外枠から前へ"
                        if candidate.get("outside_draw_effort")
                        else ""
                    )
                    st.markdown(
                        f"{mark} **{safe_text(candidate.get('name'), '馬名不明')}**"
                        f" 前方圧力 **{number_value(candidate.get('pressure'), 0):.2f}**{outside}"
                    )
        else:
            st.write("前に行きそうな馬は、近走データから絞り込めませんでした。")

        st.markdown("#### 🐎 出走馬の脚質傾向")
        st.caption("脚質傾向＝位置取りパターン／脚質適性＝その位置取りでの好走実績。")

        horses_list = sorted_horses(race)
        style_by_number = {
            str(horse.get("num", "")).strip(): horse.get(
                "running_style", "判定材料不足"
            )
            for horse in horses_list
        }
        profiles = pace.get("style_profiles", [])
        if profiles:
            style_html = '<div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; overflow:hidden;">'
            style_html += '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
            for heading in (
                "馬番",
                "馬名",
                "脚質傾向",
                "脚質適性",
                "序盤前方傾向",
                "4角前方傾向",
                "位置取り変化",
                "近走",
            ):
                align = "left" if heading == "馬名" else "center"
                style_html += f'<th style="padding:10px 6px; text-align:{align}; white-space:nowrap;">{heading}</th>'
            style_html += "</tr></thead><tbody>"

            for profile in profiles:
                if not isinstance(profile, dict):
                    continue
                number = str(profile.get("horse_number", "?")).strip()
                name = profile.get("horse_name", "馬名不明")
                running_style = style_by_number.get(
                    number,
                    profile.get("running_style") or "判定材料不足",
                )
                early = stars(profile.get("early_front_rate"))
                late = stars(profile.get("late_front_rate"))
                versatile = stars(profile.get("versatility"))
                starts = profile.get("starts", 0)

                horse_badge = f'<span class="horse-number">{number}</span>'
                style_badge = f'<span class="style-badge">{running_style}</span>'
                aptitude = profile.get("aptitude_label", "判定材料不足")
                evaluated = int(profile.get("evaluated_starts", 0) or 0)
                good = int(profile.get("good_finish_starts", 0) or 0)
                aptitude_text = (
                    f"{aptitude}（好走{good}/{evaluated}）" if evaluated else aptitude
                )
                aptitude_badge = (
                    f'<span style="display:inline-block; padding:2px 5px; border-radius:4px; '
                    f'font-size:0.7rem; background:#f1f5f9; color:#334155;">'
                    f"{aptitude_text}</span>"
                )
                star_style = 'style="text-align:center; color:#d97706; white-space:nowrap; font-size:0.75rem; letter-spacing:0.02em;"'

                style_html += '<tr style="border-bottom:1px solid #e2e8f0;">'
                style_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{horse_badge}</td>'
                style_html += f'<td style="padding:8px 4px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
                style_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{style_badge}</td>'
                style_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{aptitude_badge}</td>'
                style_html += f"<td {star_style}>{early}</td>"
                style_html += f"<td {star_style}>{late}</td>"
                style_html += f"<td {star_style}>{versatile}</td>"
                style_html += f'<td style="padding:8px 4px; text-align:center; color:#475569; white-space:nowrap;">{starts}走</td>'
                style_html += "</tr>"

            style_html += "</tbody></table></div>"
            st.markdown(style_html, unsafe_allow_html=True)
        else:
            st.info("詳細な脚質プロファイルデータがありません。")
    else:
        st.info("このレースのペース展開データはJSONに含まれていません。")


def render_horse_detail_tab(race):
    st.subheader("🐎 馬詳細・スコア内訳")
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
        f"{horse.get('rank', '—')}位: {horse_number(horse)}番 {safe_text(horse.get('name'), '不明')} ({horse.get('tag') if horse.get('tag') else '一般'})"
        for horse in horses
    ]
    selected_horse_str = st.selectbox(
        "詳細を確認する馬を選択", horse_options, key="detail_horse"
    )

    if selected_horse_str:
        selected_idx = horse_options.index(selected_horse_str)
        h = horses[selected_idx]

        base_val = number_value(h.get("base_score"), 0.0)
        plus_val = number_value(h.get("plus_sum"), 0.0)
        minus_val = number_value(h.get("minus_sum"), 0.0)
        raw_val = number_value(h.get("raw_score"), 0.0)
        pace_adv = number_value(h.get("pace_adv"), 0.0)
        track_adv = number_value(h.get("track_adv"), 0.0)
        prev_day_adv = number_value(h.get("prev_day_adv"), 0.0)
        bias_sum = number_value(h.get("bias_sum"), 0.0)
        myumi_display = f"/ 判定: {h['myumi_tag']}" if h.get("myumi_tag") else ""

        # reasons がリストの場合や文字列の場合でそのままHTML構造を生かすように処理
        reasons_raw = h.get("reasons", "特筆すべき特記事項なし")
        if isinstance(reasons_raw, list):
            reasons_html = "<br>".join(reasons_raw)
        else:
            reasons_html = str(reasons_raw)

        st.markdown(
            f"""<div class="horse-detail-box">
<h4 style="margin:0; color:#0f766e;">{horse_number(h)}番 {esc(h.get("name"), "不明")} <span style="font-size:0.9rem; color:#475569;">({esc(h.get("rank"))}位)</span></h4>
<hr style="margin:8px 0; border:0; border-top:1px solid #e2e8f0;">
<b>🏷️ タグ:</b> {esc(h.get("tag"), "特になし")}<br>
<b>🏇 騎手 / 脚質:</b> {esc(h.get("jockey"))} / {esc(h.get("running_style"))}<br>
<b>💰 単勝オッズ:</b> {esc(h.get("odds"), "N/A")}倍 {esc(myumi_display)}<br><br>
<b>📊 AI総合評価スコアの内訳:</b><br>
<div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:0.85rem; color:#1e293b; margin-top:4px;">
<b>• 基準点（スタートライン）:</b> {base_val:+.2f}<br>
<b>• 📈 加点合計（強みの積み上げ）:</b> <span style="color:#047857; font-weight:bold;">{plus_val:+.2f}</span><br>
<b>• 📉 減点合計（懸念・リスク）:</b> <span style="color:#b91c1c; font-weight:bold;">{minus_val:+.2f}</span><br>
<b>• 🧩 後付けバイアス補正合計:</b> <span style="color:#2563eb; font-weight:bold;">{bias_sum:+.2f}</span><br>
<div style="font-size:0.8rem; color:#475569; padding-left:12px; margin-top:2px;">
- ペース展開補正: {pace_adv:+.2f}<br>
- 当日馬場バイアス: {track_adv:+.2f}<br>
- 前日傾向補正: {prev_day_adv:+.2f}
</div>
<hr style="margin:6px 0; border:0; border-top:1px dashed #cbd5e1;">
<b>🎯 最終トータルスコア: {raw_val:+.2f}</b>
</div><br>
<b>📈 要因分析・モデル寄与度の詳細:</b><br>
<div style="background:#f8fafc; padding:8px; border-radius:6px; font-size:0.85rem; color:#334155; margin-top:4px;">
{reasons_html}
</div>
</div>""",
            unsafe_allow_html=True,
        )


# メイン処理
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

# 各レースに競馬場情報を付加
for race in races_list:
    race["venue"] = extract_venue(race)

st.markdown("---")

# タブ切り替え（「📋 AI予測一覧」 / 「🏁 レース展開」 / 「🐎 馬詳細」）
tab_list, tab_pace, tab_detail = st.tabs(
    ["📋 AI予測一覧", "🏁 レース展開", "🐎 馬詳細"]
)

with tab_list:
    selected_race = render_prediction_tab(races_list)

with tab_pace:
    if selected_race is not None:
        st.success(f"🎯 {safe_text(selected_race.get('name'), 'レース名不明')}")
        details = str(selected_race.get("details", "")).replace("\n", " ")
        if details:
            st.caption(f"📍 {details}")
        render_race_development_tab(selected_race)
    else:
        st.info("AI予測一覧で競馬場と対象レースを選択してください。")

with tab_detail:
    if selected_race is not None:
        st.success(f"🎯 {safe_text(selected_race.get('name'), 'レース名不明')}")
        render_horse_detail_tab(selected_race)
    else:
        st.info("AI予測一覧で競馬場と対象レースを選択してください。")
