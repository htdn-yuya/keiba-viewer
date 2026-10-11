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

# スマホ向けカスタムCSS
st.markdown(
    """
<style>
    .main { background-color: #f8fafc; }
    h1 { color: #0f766e; font-size: 1.5rem !important; }
    details { background: #f1f5f9; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; margin: 4px 0; }
    summary { font-weight: bold; cursor: pointer; color: #0f766e; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🏇 AI競馬予測結果ビューア")
st.markdown("PCで生成された最新の予測レポートをクラウド上で閲覧します。")
st.divider()

# JSONデータのパス
json_path = Path("predict_results.json")
prepared_result = None

# 手動アップロード（JSON対応）
with st.expander("📁 予測データファイル（JSON）のアップロード"):
    uploaded_file = st.file_uploader(
        "別の予測データファイルをアップロード", type=["json"]
    )
    if uploaded_file is not None:
        try:
            prepared_result = json.load(uploaded_file)
            st.success("アップロードされた予測データを表示しています。")
        except Exception as e:
            st.error(f"❌ JSONの読み込みに失敗しました: {e}")

# 自動読み込み
if prepared_result is None:
    if json_path.is_file():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                prepared_result = json.load(f)
            st.caption(f"📂 最新の予測データを表示中 ({json_path})")
        except Exception as e:
            st.error(f"❌ 予測データの読み込みに失敗しました: {e}")
    else:
        st.warning(
            "⚠️ 予測データファイル（`predict_results.json`）が見つかりません。\n\n"
            "PC側で予測を実行し、JSONを生成してGitHubにプッシュしてください。"
        )

# データを基にUIを描画（app_2.py と同じ構成）
if prepared_result:
    st.success(f"🎯 {prepared_result['name']}")
    st.caption(f"📍 {prepared_result['details']}")

    # 混戦度カード
    vol = prepared_result["volatility"]
    st.info(f"**混戦度判定: {vol['label']}**\n\n{vol['reason']}")

    st.subheader("📊 出走馬予測ランキング（主要項目）")

    # 表の項目を絞り込んだスッキリしたHTMLテーブル
    table_html = '<div style="overflow-x: auto;"><table style="width:100%; border-collapse:collapse; font-size:0.88rem; background:white; border-radius:8px; overflow:hidden; margin-top:8px;">'
    table_html += '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
    table_html += (
        '<th style="padding:10px 8px; text-align:center; white-space:nowrap;">順位</th>'
    )
    table_html += (
        '<th style="padding:10px 8px; text-align:center; white-space:nowrap;">タグ</th>'
    )
    table_html += (
        '<th style="padding:10px 8px; text-align:center; white-space:nowrap;">馬番</th>'
    )
    table_html += (
        '<th style="padding:10px 8px; text-align:left; white-space:nowrap;">馬名</th>'
    )
    table_html += (
        '<th style="padding:10px 8px; text-align:left; white-space:nowrap;">騎手</th>'
    )
    table_html += (
        '<th style="padding:10px 8px; text-align:right; white-space:nowrap;">勝率</th>'
    )
    table_html += '<th style="padding:10px 8px; text-align:right; white-space:nowrap;">軸スコア</th>'
    table_html += "</tr></thead><tbody>"

    for h in prepared_result["horses"]:
        rank_str = f"{h['rank']}位"
        tag_str = h["tag"] if h["tag"] else "-"
        num = h["num"]
        name = h["name"]
        jockey = h.get("jockey", "不明")
        win_str = f"{h['win_score']:.1f}%"
        axis_str = f"{h['axis_score']:.1f}%"

        badge_html = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.78rem;">{num}</span>'

        table_html += '<tr style="border-bottom:1px solid #e2e8f0;">'
        table_html += f'<td style="padding:10px 8px; text-align:center; font-weight:bold; color:#0f172a; white-space:nowrap;">{rank_str}</td>'
        table_html += f'<td style="padding:10px 8px; text-align:center; white-space:nowrap;"><span style="display:inline-block; padding:2px 6px; border-radius:999px; font-size:0.75rem; font-weight:bold; background:#f1f5f9; color:#0f766e; border:1px solid #cbd5e1;">{tag_str}</span></td>'
        table_html += f'<td style="padding:10px 8px; text-align:center; white-space:nowrap;">{badge_html}</td>'
        table_html += f'<td style="padding:10px 8px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
        table_html += f'<td style="padding:10px 8px; text-align:left; color:#475569; white-space:nowrap;">{jockey}</td>'
        table_html += f'<td style="padding:10px 8px; text-align:right; font-variant-numeric: tabular-nums; font-weight:500; white-space:nowrap;">{win_str}</td>'
        table_html += f'<td style="padding:10px 8px; text-align:right; font-variant-numeric: tabular-nums; font-weight:500; white-space:nowrap;">{axis_str}</td>'
        table_html += "</tr>"

    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

    # 🔍 各馬の詳細コメント・評価理由（トグル形式による補完）
    with st.expander("🔍 各馬の詳細コメント・評価理由を見る"):
        for h in prepared_result["horses"]:
            st.markdown(
                f"**{h['num']}番 {h['name']}** ({h['tag']}) - AI順位: {h['rank']}位"
            )
            st.markdown(f"- コメント: {h['score_comment']}")
            if h.get("reasons"):
                st.markdown(f"- 要因: {h['reasons']}")
            st.divider()

    # 🎟️ 自動買い目セクション
    if prepared_result.get("recommend_tickets"):
        st.subheader("🎟️ AIおすすめ自動買い目")
        for t in prepared_result["recommend_tickets"]:
            st.markdown(
                f"""
            <div style="background:white; border:1px solid #cbd5e1; border-left:4px solid #0f766e; padding:10px; border-radius:6px; margin-bottom:8px;">
                <b>{t["type"]}</b> <span style="background:#0f766e; color:white; padding:2px 6px; border-radius:10px; font-size:0.75rem;">{t["points"]}点</span><br>
                • 軸: {t["axis"]}<br>
                • 相手: {t["opponents"]}<br>
                <small style="color:#64748b;">💡 {t["note"]}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown(f"**買い目アプローチ:** {vol['approach']}")
