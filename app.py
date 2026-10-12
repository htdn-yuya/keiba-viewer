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

# スマホ向けカスタムCSS（横スクロールテーブルを見やすく調整）
st.markdown(
    """
<style>
    .main { background-color: #f8fafc; }
    h1 { color: #0f766e; font-size: 1.5rem !important; }
    details { background: #f1f5f9; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; margin: 4px 0; }
    summary { font-weight: bold; cursor: pointer; color: #0f766e; }
    .stars { color: #d97706; white-space: nowrap; letter-spacing: 1px; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🏇 AI競馬予測結果ビューア")
st.divider()

# JSONデータのパス設定
json_path = Path("predict_results_2.json")
if not json_path.is_file():
    json_path = Path("predict_results.json")

loaded_data = None

if json_path.is_file():
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
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
    race_labels = [
        f"R{r.get('id', i + 1)}: {r.get('name', 'レース')} ({r.get('details', '').split('/')[0].strip()})"
        for i, r in enumerate(races_list)
    ]

    selected_label = st.selectbox("🎯 表示するレースを選択", race_labels)
    selected_index = race_labels.index(selected_label)
    prepared_result = races_list[selected_index]

# 選択されたレースのデータを描画
if prepared_result:
    st.markdown(f"### 🎯 {prepared_result.get('name', 'レース名不明')}")
    st.caption(f"📍 {prepared_result.get('details', '').replace(chr(10), ' ')}")

    # 混戦度カード
    vol = prepared_result.get("volatility", {})
    if vol:
        st.info(f"**混戦度判定: {vol.get('label', '')}**\n\n{vol.get('reason', '')}")

    st.subheader("📊 出走馬予測ランキング")

    # 脚質・オッズ・妙味をすべて網羅したテーブルレイアウト
    table_html = '<div style="overflow-x: auto;"><table style="width:100%; border-collapse:collapse; font-size:0.82rem; background:white; border-radius:8px; overflow:hidden; margin-top:8px;">'
    table_html += '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
    table_html += (
        '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">順位</th>'
    )
    table_html += (
        '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">タグ</th>'
    )
    table_html += (
        '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">馬番</th>'
    )
    table_html += (
        '<th style="padding:10px 4px; text-align:left; white-space:nowrap;">馬名</th>'
    )
    table_html += (
        '<th style="padding:10px 4px; text-align:left; white-space:nowrap;">騎手</th>'
    )
    table_html += (
        '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">脚質</th>'
    )
    table_html += '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">オッズ</th>'
    table_html += (
        '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">妙味</th>'
    )
    table_html += '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">軸馬度</th>'
    table_html += '<th style="padding:10px 4px; text-align:center; white-space:nowrap;">穴馬度</th>'
    table_html += "</tr></thead><tbody>"

    for h in prepared_result.get("horses", []):
        rank_str = f"{h.get('rank', '-')}"
        tag_str = h.get("tag", "") if h.get("tag") else "-"
        num = h.get("num", "-")
        name = h.get("name", "不明")
        jockey = h.get("jockey", "不明")
        running_style = h.get("running_style", "-")
        odds = h.get("odds", "-")
        myumi_tag = h.get("myumi_tag", "") if h.get("myumi_tag") else "-"
        axis_stars = h.get("axis_stars", "")
        hole_stars = h.get("hole_stars", "")

        badge_html = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.7rem;">{num}</span>'

        table_html += '<tr style="border-bottom:1px solid #e2e8f0;">'
        table_html += f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f172a; white-space:nowrap;">{rank_str}位</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;"><span style="display:inline-block; padding:2px 4px; border-radius:999px; font-size:0.65rem; font-weight:bold; background:#f1f5f9; color:#0f766e; border:1px solid #cbd5e1;">{tag_str}</span></td>'
        table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{badge_html}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:left; color:#475569; white-space:nowrap;">{jockey}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center; color:#334155; white-space:nowrap;">{running_style}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center; color:#334155; white-space:nowrap;">{odds}倍</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center; color:#b45309; font-size:0.75rem; white-space:nowrap;">{myumi_tag}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center;" class="stars">{axis_stars}</td>'
        table_html += f'<td style="padding:8px 4px; text-align:center;" class="stars">{hole_stars}</td>'
        table_html += "</tr>"

    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

    # 🔍 各馬の詳細コメント（トグル）
    with st.expander("🔍 各馬の詳細コメント・評価理由を見る"):
        for h in prepared_result.get("horses", []):
            st.markdown(
                f"**{h.get('num', '')}番 {h.get('name', '')}** ({h.get('tag', '-')}) - 脚質: {h.get('running_style', '-')} / 単勝: {h.get('odds', '-')}倍"
            )
            st.markdown(f"- コメント: {h.get('score_comment', '')}")
            if h.get("reasons"):
                st.markdown(f"- 要因: {h.get('reasons', '')}")
            st.divider()

    # 🎟️ 自動買い目セクション
    if prepared_result.get("recommend_tickets"):
        st.subheader("🎟️ AIおすすめ自動買い目")
        for t in prepared_result["recommend_tickets"]:
            st.markdown(
                f"""
            <div style="background:white; border:1px solid #cbd5e1; border-left:4px solid #0f766e; padding:10px; border-radius:6px; margin-bottom:8px;">
                <b>{t.get("type", "")}</b> <span style="background:#0f766e; color:white; padding:2px 6px; border-radius:10px; font-size:0.75rem;">{t.get("points", "")}点</span><br>
                • 軸: {t.get("axis", "")}<br>
                • 相手: {t.get("opponents", "")}<br>
                <small style="color:#64748b;">💡 {t.get("note", "")}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

    if vol.get("approach"):
        st.markdown(f"**買い目アプローチ:** {vol['approach']}")
