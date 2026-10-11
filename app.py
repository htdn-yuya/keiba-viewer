from pathlib import Path

import streamlit as st

# スマホ向けレイアウト＆ページ設定
st.set_page_config(
    page_title="AI競馬予測ビューア",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# スマホ向けカスタムCSS（余白や見やすさの調整）
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

# レポートHTMLの保存先パス（reports/predict_results.html）
default_html_path = Path("predict_results.html")

html_content = None

# サイドバーまたは画面上部で、自動読み込みか手動アップロードかを選択
with st.expander("📁 レポートファイルの切り替え・アップロード"):
    uploaded_file = st.file_uploader(
        "別の予測HTMLファイルをアップロードして表示", type=["html"]
    )
    if uploaded_file is not None:
        html_content = uploaded_file.getvalue().decode("utf-8")
        st.success("アップロードされたHTMLファイルを表示しています。")

# アップロードがない場合はデフォルトのパスから読み込む
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
            "⚠️ 予測HTMLファイル（`reports/predict_results.html`）が見つかりません"
            "。\n\n"
            "PC側で予測を実行してHTMLを生成し、GitHubにプッシュしてください。"
        )

# HTMLコンテンツが存在する場合、Streamlit上でレンダリング
if html_content:
    # スマホでも見やすいよう十分な高さを確保したiframeでHTMLを描画
    st.components.v1.html(html_content, height=1400, scrolling=True)
