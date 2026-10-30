import json
from pathlib import Path

import streamlit as st

# スマホ向けレイアウト＆ページ設定
st.set_page_config(
    page_title="AI競馬予測ビューア",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# スマホ向けカスタムCSS（デザイン統一・レスポンシブ調整）
st.markdown(
    """
<style>
    .main { background-color: #f8fafc; }
    h1 { color: #0f766e; font-size: 1.5rem !important; }
    .metric-card { background: white; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .horse-detail-box { background: white; border: 1px solid #cbd5e1; padding: 14px; border-radius: 8px; margin-bottom: 10px; }
    .stars { color: #d97706; white-space: nowrap; letter-spacing: 1px; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🏇 AI競馬予測結果ビューア")
st.divider()


# 丸数字変換ヘルパー
def to_maru_num(n):
    try:
        n_int = int(n)
        if 1 <= n_int <= 20:
            return chr(0x2460 + n_int - 1)
    except:
        pass
    return str(n)


# 開催競馬場を抽出するヘルパー
RACECOURSES = [
    "東京",
    "中山",
    "京都",
    "阪神",
    "中京",
    "小倉",
    "福島",
    "新潟",
    "札幌",
    "函館",
]


def extract_venue(details_text):
    for rc in RACECOURSES:
        if rc in details_text:
            return rc
    return "その他"


# JSONデータのパス設定（latest_prediction.json または predict_results系を自動探索）
json_files = ["latest_prediction.json"] + sorted(
    [str(p) for p in Path(".").glob("predict_results_*.json")], reverse=True
)
json_path = None
for f in json_files:
    if Path(f).is_file():
        json_path = Path(f)
        break

if not json_path:
    json_path = Path("predict_results.json")

loaded_data = None

if json_path and json_path.is_file():
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        st.sidebar.caption(f"📁 読込ファイル: {json_path.name}")
    except Exception as e:
        st.error(f"❌ 予測データの読み込みに失敗しました: {e}")
else:
    st.warning("⚠️ 予測データファイルが見つかりません。")

# レースリストの構築
races_list = []
if isinstance(loaded_data, list):
    races_list = loaded_data
elif isinstance(loaded_data, dict):
    races_list = [loaded_data]

prepared_result = None

if races_list:
    try:
        # 各レースに競馬場情報を付与
        for r in races_list:
            r["venue"] = extract_venue(r.get("details", ""))

        # 競馬場ごとにレース番号（1R, 2R...）を採番するためのカウンタ
        venue_counters = {}
        for r in races_list:
            v = r.get("venue", "その他")
            venue_counters[v] = venue_counters.get(v, 0) + 1
            r["venue_race_num"] = venue_counters[v]

        # 利用可能な競馬場リストの作成
        available_venues = sorted(
            list(set(r.get("venue", "その他") for r in races_list))
        )
        venue_options = ["すべて"] + available_venues

        # 🏟️ 開催競馬場フィルター
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            selected_venue = st.selectbox("🏟️ 開催競馬場", venue_options)

        # 競馬場による絞り込み
        if selected_venue != "すべて":
            filtered_races = [r for r in races_list if r.get("venue") == selected_venue]
        else:
            filtered_races = races_list

        if not filtered_races:
            st.warning("選択された条件に一致するレースがありません。")
        else:
            race_labels = []
            for r in filtered_races:
                v_name = r.get("venue", "その他")
                v_num = r.get("venue_race_num", 1)
                r_name = r.get("name", "レース")
                details = r.get("details", "")
                sub_info = details.split("/")[0].strip() if details else ""
                # 表示例: [東京] 東京1R: 2歳未勝利 (09:40発走...)
                race_labels.append(
                    f"[{v_name}] {v_name}{v_num}R: {r_name} ({sub_info})"
                )

            with col_f2:
                selected_label = st.selectbox("🎯 表示するレースを選択", race_labels)

            selected_index = race_labels.index(selected_label)
            prepared_result = filtered_races[selected_index]

    except Exception as e:
        st.error(f"❌ フィルター・レース選択の構築中にエラーが発生しました: {e}")

# 選択されたレースのデータを描画
if prepared_result:
    st.markdown(f"### 🎯 {prepared_result.get('name', 'レース名不明')}")
    details_text = prepared_result.get("details", "")
    if details_text:
        st.caption(f"📍 {details_text.replace(chr(10), ' ')}")

    vol = prepared_result.get("volatility", {})
    horses_list = prepared_result.get("horses", [])

    # 勝率またはAI順位順にソート（安全のため）
    horses_list = sorted(
        horses_list,
        key=lambda x: (
            x.get("rank", 99) if isinstance(x.get("rank"), (int, float)) else 99
        ),
    )

    top_horse = horses_list[0] if horses_list else None
    top_odds = top_horse.get("odds", "N/A") if top_horse else "N/A"

    # ==========================================
    # 📑 シンプルな2タブ構成
    # ==========================================
    tab_list, tab_detail = st.tabs(
        [
            "📋 予測一覧 ＆ インサイト",
            "🔍 個別馬・要因詳細分析",
        ]
    )

    # --- TAB 1: 予測一覧 ＆ インサイト ---
    with tab_list:
        st.markdown("### 🧠 レースインサイト")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div class="metric-card"><small>レース性質</small><br><b>{vol.get("label", "混戦")}</b></div>',
                unsafe_allow_html=True,
            )
        with col2:
            num_val = (
                top_horse.get("horse_number", top_horse.get("num", "-"))
                if top_horse
                else "-"
            )
            st.markdown(
                f'<div class="metric-card"><small>本命予測1位</small><br><b>{to_maru_num(num_val)} ({top_odds}倍)</b></div>',
                unsafe_allow_html=True,
            )
        with col3:
            myumi_count = sum(
                1 for h in horses_list if "旨味" in str(h.get("myumi_tag", ""))
            )
            st.markdown(
                f'<div class="metric-card"><small>妙味馬検知</small><br><b>{myumi_count}頭</b></div>',
                unsafe_allow_html=True,
            )

        decision_msg = vol.get("decision") or prepared_result.get("decision_text")
        if decision_msg:
            st.markdown(
                f"<small style='color:#475569;'>💡 {decision_msg}</small>",
                unsafe_allow_html=True,
            )

        # --- 独立したレースペース予測（AIランキング・スコアとは別表示） ---
        st.markdown("### 🏁 レース展開・ペース予測")
        pace_forecast = prepared_result.get("pace_forecast")
        if isinstance(pace_forecast, dict):
            pace_value = pace_forecast.get("pace", "判定保留")
            contest_value = pace_forecast.get("competition_risk", "判定保留")
            coverage_value = pace_forecast.get("data_coverage")
            quality_value = pace_forecast.get("data_quality", "不明")
            coverage_label = (
                f"{float(coverage_value):.0%}"
                if isinstance(coverage_value, (int, float))
                else "不明"
            )

            pace_col1, pace_col2, pace_col3 = st.columns(3)
            pace_col1.metric("想定ペース", pace_value)
            pace_col2.metric("先行争い", contest_value)
            pace_col3.metric("位置取りデータ利用率", coverage_label)
            st.caption(
                f"データ品質：{quality_value}。この展開予測は参考情報であり、"
                "既存のAIランキング・各馬スコアには加算していません。"
            )

            candidates = pace_forecast.get("front_runner_candidates") or []
            if candidates:
                st.markdown("**前方候補馬**")
                candidate_rows = [
                    {
                        "馬番": item.get("number", "-"),
                        "馬名": item.get("name", "不明"),
                        "前方圧力": item.get("pressure", "-"),
                        "根拠": "・".join(item.get("evidence") or []),
                        "外枠負荷": "あり" if item.get("outside_draw_effort") else "なし",
                    }
                    for item in candidates
                ]
                st.dataframe(candidate_rows, hide_index=True, use_container_width=True)
            else:
                st.caption("前方候補として抽出された馬はいません。")

            pace_reasons = pace_forecast.get("reasons") or []
            if pace_reasons:
                with st.expander("ペース判定の根拠・注意点"):
                    for reason in pace_reasons:
                        st.write(f"・{reason}")
                    scope_note = pace_forecast.get("scope_note")
                    if scope_note:
                        st.caption(scope_note)
        else:
            st.info(
                "このJSONにはペース予測データが含まれていません。"
                "予測生成側の最新版で一括レース予測を再実行し、"
                "出力されたJSONをこのビューアに配置してください。"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("📊 出走馬予測ランキング")

        table_html = '<div style="overflow-x: auto;"><table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; overflow:hidden; margin-top:8px;">'
        table_html += '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">順位</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">タグ</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">馬番</th>'
        table_html += '<th style="padding:10px 6px; text-align:left; white-space:nowrap;">馬名</th>'
        table_html += '<th style="padding:10px 6px; text-align:left; white-space:nowrap;">騎手</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">脚質</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">単勝</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">妙味判定</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">軸度</th>'
        table_html += '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">穴度</th>'
        table_html += "</tr></thead><tbody>"

        for h in horses_list:
            rank_str = f"{h.get('rank', '-')}"
            tag_str = h.get("tag", "") if h.get("tag") else "-"
            num = h.get("horse_number", h.get("num", "-"))
            name = h.get("name", "不明")
            jockey = h.get("jockey", "不明")
            running_style = h.get("running_style", "-")
            odds = h.get("odds", "-")
            myumi_tag = h.get("myumi_tag", "") if h.get("myumi_tag") else "-"
            axis_stars = h.get("axis_stars", "★★★")
            hole_stars = h.get("hole_stars", "★★")

            badge_html = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.75rem;">{to_maru_num(num)}</span>'
            style_badge = f'<span style="display:inline-block; padding:2px 4px; border-radius:4px; font-size:0.7rem; background:#e2e8f0; color:#1e293b; font-weight:bold;">{running_style}</span>'

            table_html += '<tr style="border-bottom:1px solid #e2e8f0;">'
            table_html += f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f172a; white-space:nowrap;">{rank_str}位</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;"><span style="display:inline-block; padding:2px 4px; border-radius:999px; font-size:0.65rem; font-weight:bold; background:#f1f5f9; color:#0f766e; border:1px solid #cbd5e1;">{tag_str}</span></td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{badge_html}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:left; color:#475569; white-space:nowrap;">{jockey}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; color:#334155; white-space:nowrap;">{style_badge}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; color:#334155; white-space:nowrap;">{odds}倍</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; color:#b45309; font-size:0.75rem; white-space:nowrap;">{myumi_tag}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center;" class="stars">{axis_stars}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center;" class="stars">{hole_stars}</td>'
            table_html += "</tr>"

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

    # --- TAB 2: 個別馬・要因詳細分析 ---
    with tab_detail:
        st.subheader("🔍 個別馬の詳細分析・要因比較")
        st.markdown(
            "<small style='color:#64748b;'>選択した馬のAI評価スコアの内訳や特記シグナルを確認できます。</small>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        horse_options = []
        for h in horses_list:
            r_num = h.get("horse_number", h.get("num", "-"))
            r_tag = h.get("tag") if h.get("tag") else "一般"
            horse_options.append(
                f"{h.get('rank', '-')}位: {to_maru_num(r_num)}番 {h.get('name', '不明')} ({r_tag})"
            )

        selected_horse_str = st.selectbox("詳細を確認する馬を選択", horse_options)

        if selected_horse_str:
            selected_idx = horse_options.index(selected_horse_str)
            h = horses_list[selected_idx]

            base_val = h.get("base_score", 0.0)
            plus_val = h.get("plus_sum", 0.0)
            minus_val = h.get("minus_sum", 0.0)
            raw_val = h.get("raw_score", 0.0)
            pace_adv = h.get("pace_adv", 0.0)
            track_adv = h.get("track_adv", 0.0)
            prev_day_adv = h.get("prev_day_adv", 0.0)
            bias_sum = h.get("bias_sum", 0.0)
            myumi_display = (
                f"/ 判定: {h.get('myumi_tag')}" if h.get("myumi_tag") else ""
            )

            num_val = h.get("horse_number", h.get("num", "-"))
            reasons_html = (
                h.get("reasons") or h.get("score_comment") or "特筆すべき特記事項なし"
            )

            st.markdown(
                f"""<div class="horse-detail-box">
<h4 style="margin:0; color:#0f766e;">{to_maru_num(num_val)}番 {h.get("name", "不明")} <span style="font-size:0.9rem; color:#475569;">({h.get("rank", "-")}位)</span></h4>
<hr style="margin:8px 0; border:0; border-top:1px solid #e2e8f0;">
<b>🏷️ タグ:</b> {h.get("tag") if h.get("tag") else "特になし"}<br>
<b>🏇 騎手 / 脚質:</b> {h.get("jockey", "不明")} / {h.get("running_style", "-")}<br>
<b>💰 単勝オッズ:</b> {h.get("odds", "N/A")}倍 {myumi_display}<br><br>
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
else:
    st.warning("出走馬データが見つかりません。")
