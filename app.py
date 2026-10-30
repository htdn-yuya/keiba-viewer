import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="AI競馬予測ビューア",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.stApp { background: #f7f9fc; }
.block-container { padding-top: 1.4rem; max-width: 1500px; }
[data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #dce3ea;
    padding: 12px 14px; border-radius: 12px;
}
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; }
.pace-note { color: #526174; font-size: .9rem; }
.horse-number {
    display:inline-flex; width:30px; height:30px; border-radius:50%;
    align-items:center; justify-content:center; background:#0f766e;
    color:white; font-weight:700; margin-right:8px;
}
.small-muted { color:#64748b; font-size:.82rem; }
</style>
""",
    unsafe_allow_html=True,
)

RACECOURSES = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]


def safe_text(value, default="—"):
    if value is None or value == "":
        return default
    return str(value)


def number_value(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def horse_number(horse):
    return horse.get("horse_number", horse.get("num", horse.get("number", "-")))


def to_maru_num(value):
    try:
        n = int(value)
        if 1 <= n <= 20:
            return chr(0x2460 + n - 1)
    except (TypeError, ValueError):
        pass
    return safe_text(value)


def extract_venue(race):
    details = str(race.get("details", ""))
    name = str(race.get("name", ""))
    for venue in RACECOURSES:
        if venue in details or venue in name:
            return venue
    return "その他"


def race_date(race):
    for key in ("prediction_date", "date", "開催日", "race_date"):
        if race.get(key):
            return str(race[key])[:10]
    return ""


def load_prediction_file():
    # 日付付きの最新ファイルを優先し、次に標準出力、最後に互換ファイルを読む。
    candidates = (
        sorted(Path(".").glob("predict_results_*.json"), reverse=True)
        + [Path("predict_results.json"), Path("latest_prediction.json")]
    )
    for path in candidates:
        if path.is_file():
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


def sorted_horses(race):
    horses = race.get("horses") or []
    return sorted(
        [h for h in horses if isinstance(h, dict)],
        key=lambda h: number_value(h.get("rank")) if number_value(h.get("rank")) is not None else 999,
    )


def display_stars(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, (int, float)):
        count = max(0, min(5, int(round(value))))
        return "★" * count + "☆" * (5 - count)
    return str(value)


def metric_alias(horse, aliases):
    for key in aliases:
        if key in horse and horse[key] not in (None, ""):
            return horse[key]
    return None


def render_race_header(race):
    st.title(f"🏇 {safe_text(race.get('name'), 'レース名不明')}")
    details = str(race.get("details", "")).replace("\n", " ")
    if details:
        st.caption(f"📍 {details}")


def render_prediction_list(race, races):
    st.subheader("🧠 レースサマリ")
    horses = sorted_horses(race)
    volatility = race.get("volatility") or {}
    top = horses[0] if horses else {}
    top_num = horse_number(top) if top else "—"
    myumi_count = sum("旨味" in str(h.get("myumi_tag", "")) for h in horses)
    cols = st.columns(4)
    cols[0].metric("レース性質", safe_text(volatility.get("label"), "未判定"))
    cols[1].metric("AI本命", f"{to_maru_num(top_num)}番" if top else "—")
    cols[2].metric("妙味検知", f"{myumi_count}頭")
    cols[3].metric("出走頭数", f"{len(horses)}頭")
    decision = volatility.get("decision") or race.get("decision_text")
    if decision:
        st.info(str(decision))

    st.subheader("📋 開催レース一覧")
    overview = []
    for item in races:
        item_horses = sorted_horses(item)
        best = item_horses[0] if item_horses else {}
        overview.append({
            "競馬場": item.get("venue", extract_venue(item)),
            "レース": safe_text(item.get("name"), "レース名不明"),
            "本命": f"{to_maru_num(horse_number(best))} {safe_text(best.get('name'))}" if best else "—",
            "単勝": safe_text(best.get("odds")) if best else "—",
            "頭数": len(item_horses),
            "レース性質": safe_text((item.get("volatility") or {}).get("label"), "未判定"),
        })
    st.dataframe(pd.DataFrame(overview), hide_index=True, use_container_width=True)

    st.subheader("🏆 出走馬AIランキング")
    if not horses:
        st.warning("出走馬データがありません。")
        return
    rows = []
    for h in horses:
        rows.append({
            "順位": safe_text(h.get("rank")),
            "馬番": to_maru_num(horse_number(h)),
            "馬名": safe_text(h.get("name"), "不明"),
            "タグ": safe_text(h.get("tag")),
            "騎手": safe_text(h.get("jockey")),
            "脚質": safe_text(h.get("running_style")),
            "単勝": safe_text(h.get("odds")),
            "妙味": safe_text(h.get("myumi_tag")),
            "軸度": display_stars(h.get("axis_stars")),
            "穴度": display_stars(h.get("hole_stars")),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_pace_view(race):
    st.subheader("🏁 レース展開・ペース予測")
    pace = race.get("pace_forecast")
    if not isinstance(pace, dict):
        st.info("このレースにはペース予測データがありません。")
        return

    pace_cols = st.columns(4)
    coverage = number_value(pace.get("data_coverage"))
    coverage_label = f"{coverage:.0%}" if coverage is not None else "不明"
    pace_cols[0].metric("想定ペース", safe_text(pace.get("pace"), "判定保留"))
    pace_cols[1].metric("先行争い", safe_text(pace.get("competition_risk"), "判定保留"))
    pace_cols[2].metric("データ利用率", coverage_label)
    pace_cols[3].metric("データ品質", safe_text(pace.get("data_quality"), "不明"))
    st.caption("ペース予測は参考情報として独立表示しています。AIランキング・各馬スコアには加算していません。")

    candidates = pace.get("front_runner_candidates") or []
    st.markdown("#### 🚩 前方候補・先行争い")
    if candidates:
        cols = st.columns(min(4, len(candidates)))
        for index, candidate in enumerate(candidates):
            with cols[index % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"**{to_maru_num(candidate.get('number', '-'))}番 {safe_text(candidate.get('name'), '不明')}**")
                    st.metric("前方圧力", safe_text(candidate.get("pressure")))
                    evidence = candidate.get("evidence") or []
                    if evidence:
                        st.caption(" / ".join(str(x) for x in evidence))
                    if candidate.get("outside_draw_effort"):
                        st.caption("外枠負荷あり")
    else:
        st.caption("前方候補として抽出された馬はいません。")

    horses = sorted_horses(race)
    st.markdown("#### 🧭 脚質・位置取り一覧")
    profile_rows = []
    for h in horses:
        early = metric_alias(h, ("early_position_stars", "early_front_stars", "序盤前方", "early_position"))
        corner = metric_alias(h, ("corner4_front_stars", "corner4_position_stars", "4角前方", "corner4_position"))
        flexibility = metric_alias(h, ("style_flexibility_stars", "flexibility_stars", "自在性", "style_flexibility"))
        profile_rows.append({
            "馬番": to_maru_num(horse_number(h)),
            "馬名": safe_text(h.get("name"), "不明"),
            "脚質": safe_text(h.get("running_style")),
            "序盤前方": display_stars(early),
            "4角前方": display_stars(corner),
            "自在性": display_stars(flexibility),
        })
    if profile_rows:
        st.dataframe(pd.DataFrame(profile_rows), hide_index=True, use_container_width=True)
        if all(row["序盤前方"] == row["4角前方"] == row["自在性"] == "—" for row in profile_rows):
            st.caption("位置取り評価の詳細項目は、このJSONには含まれていません。")
    reasons = pace.get("reasons") or []
    if reasons or pace.get("scope_note"):
        with st.expander("判定根拠・注意点"):
            for reason in reasons:
                st.write(f"・{reason}")
            if pace.get("scope_note"):
                st.caption(str(pace["scope_note"]))


def render_horse_detail(race):
    st.subheader("🐎 個別馬・比較分析")
    horses = sorted_horses(race)
    if not horses:
        st.warning("出走馬データがありません。")
        return

    labels = [
        f"{safe_text(h.get('rank'))}位：{to_maru_num(horse_number(h))}番 {safe_text(h.get('name'), '不明')}"
        for h in horses
    ]
    selected = st.selectbox("詳細を確認する馬", labels, key="horse_detail_select")
    horse = horses[labels.index(selected)]
    cols = st.columns(4)
    cols[0].metric("AI順位", f"{safe_text(horse.get('rank'))}位")
    cols[1].metric("単勝オッズ", f"{safe_text(horse.get('odds'))}倍")
    cols[2].metric("軸度", display_stars(horse.get("axis_stars")))
    cols[3].metric("穴度", display_stars(horse.get("hole_stars")))

    st.markdown(f"### {to_maru_num(horse_number(horse))}番 {safe_text(horse.get('name'), '不明')}")
    st.caption(f"{safe_text(horse.get('jockey'))} / {safe_text(horse.get('running_style'))} / {safe_text(horse.get('tag'))}")

    score_fields = [
        ("基準点", "base_score"),
        ("加点合計", "plus_sum"),
        ("減点合計", "minus_sum"),
        ("バイアス補正", "bias_sum"),
        ("最終スコア", "raw_score"),
    ]
    score_data = []
    for label, key in score_fields:
        value = number_value(horse.get(key))
        if value is not None:
            score_data.append({"項目": label, "スコア": value})
    if score_data:
        st.markdown("#### 📊 AI評価スコア内訳")
        st.bar_chart(pd.DataFrame(score_data).set_index("項目"))
        st.dataframe(pd.DataFrame(score_data), hide_index=True, use_container_width=True)
    else:
        st.caption("この馬のスコア内訳はJSONに含まれていません。")

    adjustment_fields = [
        ("ペース展開補正", "pace_adv"),
        ("当日馬場バイアス", "track_adv"),
        ("前日傾向補正", "prev_day_adv"),
    ]
    adjustment_rows = [
        {"補正項目": label, "値": number_value(horse.get(key))}
        for label, key in adjustment_fields
        if number_value(horse.get(key)) is not None
    ]
    if adjustment_rows:
        st.markdown("#### 🧩 補正項目")
        st.dataframe(pd.DataFrame(adjustment_rows), hide_index=True, use_container_width=True)

    reasons = horse.get("reasons") or horse.get("score_comment")
    st.markdown("#### 📈 評価要因・モデル寄与")
    if isinstance(reasons, list):
        for reason in reasons:
            st.write(f"・{reason}")
    elif reasons:
        st.write(str(reasons))
    else:
        st.caption("特筆すべき要因データはありません。")


json_path, races_list, load_error = load_prediction_file()
st.title("🏇 AI競馬予測ビューア")
if json_path:
    st.sidebar.caption(f"📁 読込ファイル: {json_path.name}")
if load_error:
    st.error(load_error)
    st.stop()

if not races_list:
    st.warning("予測JSONにレースがありません。")
    st.stop()

for race in races_list:
    race["venue"] = extract_venue(race)

available_venues = sorted({race["venue"] for race in races_list})
selected_venue = st.sidebar.selectbox("🏟️ 開催競馬場", ["すべて"] + available_venues)
venue_races = [race for race in races_list if selected_venue == "すべて" or race["venue"] == selected_venue]

race_labels = []
for index, race in enumerate(venue_races):
    race_name = safe_text(race.get("name"), "レース名不明")
    detail = str(race.get("details", "")).split("/")[0].strip()
    race_labels.append(f"{race['venue']}｜{race_name}｜{detail}" if detail else f"{race['venue']}｜{race_name}")

selected_label = st.sidebar.selectbox("🎯 対象レース", race_labels)
selected_race = venue_races[race_labels.index(selected_label)]
render_race_header(selected_race)

screen = st.radio(
    "表示画面",
    ["📋 AI予測一覧", "🏁 レース展開", "🐎 馬詳細"],
    horizontal=True,
    key="viewer_screen",
)
st.divider()

if screen == "📋 AI予測一覧":
    render_prediction_list(selected_race, races_list)
elif screen == "🏁 レース展開":
    render_pace_view(selected_race)
else:
    render_horse_detail(selected_race)

with st.sidebar:
    st.divider()
    st.caption(f"読み込みレース数：{len(races_list)}")
    st.caption("表示専用ビューア：予測・学習処理は実行しません。")
