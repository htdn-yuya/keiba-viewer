from pathlib import Path

import streamlit as st
from bs4 import BeautifulSoup

# スマホ向けレイアウト＆ページ設定
st.set_page_config(
    page_title="AI競馬予測ビューア",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# スマホ向けカスタムCSS（全体のデザイン調整）
st.markdown(
    """
<style>
    .main { background-color: #f8fafc; }
    h1 { color: #0f766e; font-size: 1.5rem !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🏇 AI競馬予測結果ビューア")
st.markdown("PCで生成された最新の予測レポート（HTML）をクラウド上で閲覧します。")
st.divider()

# ルート直下の predict_results.html を指定
default_html_path = Path("predict_results.html")

html_content = None

# 手動アップロード
with st.expander("📁 レポートファイルの切り替え・アップロード"):
    uploaded_file = st.file_uploader(
        "別の予測HTMLファイルをアップロードして表示", type=["html"]
    )
    if uploaded_file is not None:
        html_content = uploaded_file.getvalue().decode("utf-8")
        st.success("アップロードされたHTMLファイルを表示しています。")

# 自動読み込み
if html_content is None:
    if default_html_path.is_file():
        try:
            with open(default_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.caption(f"📂 最新のローカルレポートを表示中 ({default_html_path})")
        except Exception as e:
            st.error(f"❌ HTMLファイルの読み込みに失敗しました: {e}")
    else:
        st.warning(
            "⚠️ 予測HTMLファイル（`predict_results.html`）が見つかりません。\n\n"
            "ファイル名や配置場所を確認してください。"
        )

# HTMLコンテンツが存在する場合、BeautifulSoupでapp_2.py風のデザインに自動スタイリング
if html_content:
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. すべてのテーブルを app_2.py と同じモダンなスタイルに変換
    for table in soup.find_all("table"):
        table["style"] = (
            "width:100%; border-collapse:collapse; font-size:0.88rem; "
            "background:white; border-radius:8px; overflow:hidden; margin-top:8px;"
        )

        # ヘッダー（th）のスタイリング
        for th in table.find_all("th"):
            th["style"] = (
                "padding:10px 8px; text-align:center; white-space:nowrap; "
                "background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;"
            )

        # セル（td）のスタイリング
        for tr in table.find_all("tr"):
            for td in tr.find_all("td"):
                # すでにインラインスタイルがなければ綺麗に整える
                current_style = td.get("style", "")
                td["style"] = (
                    f"padding:10px 8px; border-bottom:1px solid #e2e8f0; "
                    f"white-space:nowrap; {current_style}"
                )

    # 2. テーブル全体を横スクロール可能なdivコンテナで包む
    for table in soup.find_all("table"):
        wrapper = soup.new_tag(
            "div",
            style=(
                "overflow-x: auto; width: 100%; -webkit-overflow-scrolling:"
                " touch; margin-bottom: 1rem;"
            ),
        )
        table.wrap(wrapper)

    # 変換後のHTMLを取得
    html_content = str(soup)

    # Streamlit上でレンダリング
    st.components.v1.html(html_content, height=1400, scrolling=True)
