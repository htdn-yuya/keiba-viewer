import html
import json
import re
from pathlib import Path

import streamlit as st

# ==========================================
# 1. スマホ向けレイアウト＆ページ設定
# ==========================================
st.set_page_config(
    page_title="AI競馬予測システム",
    page_icon="🏇",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# スマホ向けカスタムCSS（ベースコードのデザインを継承）
st.markdown(
    """
<style>
  .main { background-color: #f8fafc; }
  .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #0f766e; color: white; padding: 10px; }
  .stButton>button:hover { background-color: #115e59; color: white; }
  .app-title { font-size: 1.5rem !important; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #0f172a; margin-bottom: 0.5rem; }
  .metric-card { background: white; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
  .horse-detail-box { background: white; border: 1px solid #cbd5e1; padding: 14px; border-radius: 8px; margin-bottom: 10px; }
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. 評価判定ユーティリティ関数（ベースコード準拠）
# ==========================================
def get_base_rank(score: float) -> str:
    """地力評価 (base_score) の 5 段階判定"""
    if score >= 0.05:
        return "S"
    elif score >= 0.00:
        return "A"
    elif score >= -0.10:
        return "B"
    elif score >= -0.20:
        return "C"
    else:
        return "D"


def get_cond_rank(score: float) -> str:
    """条件適性 (plus_sum + minus_sum) の 5 段階判定"""
    if score >= 0.80:
        return "S"
    elif score >= 0.30:
        return "A"
    elif score >= -0.20:
        return "B"
    elif score >= -0.60:
        return "C"
    else:
        return "D"


def format_rank_emoji(rank_str: str, score: float) -> str:
    """SABCDランクを絵文字付きHTML形式に装飾"""
    emoji_map = {
        "S": '<span style="color:#047857; font-weight:bold;">👑 S</span>',
        "A": '<span style="color:#059669; font-weight:bold;">🟢 A</span>',
        "B": '<span style="color:#d97706; font-weight:bold;">🟡 B</span>',
        "C": '<span style="color:#ea580c; font-weight:bold;">🟠 C</span>',
        "D": '<span style="color:#dc2626; font-weight:bold;">🔴 D</span>',
    }
    formatted = emoji_map.get(rank_str, rank_str)
    return f"{formatted} <small style='color:#64748b;'>({score:+.2f})</small>"


def assign_evaluations(horses_list):
    """地力・条件スコアとモデル指標に基づいてメイン評価バッジを判定する。"""
    for idx, h in enumerate(horses_list, start=1):
        rank = h.get("rank", idx)
        base_val = float(h.get("base_score", 0.0) or 0.0)
        plus_val = float(h.get("plus_sum", 0.0) or 0.0)
        minus_val = float(h.get("minus_sum", 0.0) or 0.0)
        cond_val = plus_val + minus_val

        try:
            burst_val = float(h.get("burst_score", 0.0) or 0.0)
        except (ValueError, TypeError):
            burst_val = 0.0
        try:
            weak_risk_raw = h.get("weak_risk_score")
            weak_risk_val = (
                1.0
                if weak_risk_raw is None or weak_risk_raw == ""
                else float(weak_risk_raw)
            )
        except (ValueError, TypeError):
            weak_risk_val = 1.0

        b_rank = get_base_rank(base_val)
        c_rank = get_cond_rank(cond_val)

        h["base_rank"] = b_rank
        h["cond_rank"] = c_rank
        h["base_display"] = format_rank_emoji(b_rank, base_val)
        h["cond_display"] = format_rank_emoji(c_rank, cond_val)

        # JSON側に既存のタグがあれば優先、なければ新ロジックから判定
        badge = h.get("main_badge") or h.get("tag")
        if not badge or badge == "—":
            badge = "—"

            total_val = base_val + cond_val

            # 1. 鉄板軸：予測1位かつトータルスコアが最上位帯
            if rank == 1 and total_val > 0.56:
                badge = "🎯 鉄板軸"
            # 2. 本命軸：上位（4位以内）でトータルスコアがプラス
            elif rank < 4 and total_val > 0.28:
                badge = "👑 本命軸"
            # 3. 相手軸：上位（4位以内）でトータルスコアがプラス
            elif rank < 4 and total_val > 0.0:
                badge = "🛡️ 相手軸"
            # 4. バースト穴：中位以下でバースト力が高い、またはリスクが低い
            elif rank >= 4 and (burst_val >= 0.10 or weak_risk_val <= 0.35):
                badge = "🚀 バースト穴"
            # 5. 地力穴：中位以下で地力スコアがS/A相当
            elif rank >= 4 and base_val >= 0.00:
                badge = "💎 地力穴"

        h["main_badge"] = badge
    return horses_list


# ==========================================
# 3. JSONデータ読み込み＆競馬場・レース番号の抽出
# ==========================================
TRACK_CODE_MAP = {
    "01": "札幌",
    "02": "函館",
    "03": "福島",
    "04": "新潟",
    "05": "東京",
    "06": "中山",
    "07": "中京",
    "08": "京都",
    "09": "阪神",
    "10": "小倉",
}
TRACK_NAMES = list(TRACK_CODE_MAP.values())


def extract_track_name(race: dict) -> str:
    """レースデータから競馬場名を自動抽出"""
    for key in ["track", "track_name", "place", "venue"]:
        if race.get(key):
            for t in TRACK_NAMES:
                if t in str(race[key]):
                    return t
            return str(race[key])

    race_id = str(race.get("race_id", "") or race.get("id", ""))
    if len(race_id) >= 6 and race_id[:6].isdigit():
        t_code = race_id[4:6]
        if t_code in TRACK_CODE_MAP:
            return TRACK_CODE_MAP[t_code]

    details = str(race.get("details", ""))
    for t in TRACK_NAMES:
        if t in details:
            return t

    return "その他"


def extract_race_num(race: dict, fallback_idx: int) -> int:
    """レースデータからレース番号（1〜12）を自動抽出"""
    for key in ["race_num", "race_no", "r", "num"]:
        val = race.get(key)
        if val is not None:
            m = re.search(r"\d+", str(val))
            if m:
                return int(m.group(0))

    race_id = str(race.get("race_id", "") or race.get("id", ""))
    if len(race_id) == 12 and race_id.isdigit():
        return int(race_id[10:12])

    text = f"{race.get('name', '')} {race.get('details', '')}"
    m = re.search(r"(\d{1,2})\s*(?:R|レース)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    return fallback_idx


def extract_start_time(race: dict) -> str:
    """ソート用に発走時刻（例: 10:00）を抽出"""
    details = str(race.get("details", ""))
    m = re.search(r"(\d{1,2}:\d{2})発走", details)
    return m.group(1).zfill(5) if m else "99:99"


def format_clean_details(raw_details: str) -> str:
    """改行や連続スラッシュ・空白を整理して綺麗な『 / 』区切りに整形"""
    parts = [
        re.sub(r"\s+", " ", p).strip() for p in re.split(r"[\n/／]+", str(raw_details))
    ]
    return " / ".join([p for p in parts if p])


@st.cache_data
def load_prediction_data():
    candidates = [
        Path("latest_prediction.json"),
        Path("predict_results.json"),
    ]
    for path in candidates:
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("races", [data])
            except Exception:
                continue
    return []


# ==========================================
# 4. メインUI描画関数（各レースのコンテンツ）
# ==========================================
def render_race_content(race: dict, unique_key: str):
    """選択された1レース分の予測一覧・展開・馬詳細を描画"""
    r_num = race.get("_race_num", "")
    r_name = race.get("name", "レース名未設定")
    r_details = format_clean_details(race.get("details", ""))

    st.success(f"🎯 {r_num}R：{r_name}")
    st.caption(f"📍 {r_details}")

    # 下段タブ切り替え（「📋 AI予測一覧」 / 「🏁 レース展開」 / 「🐎 馬詳細」）
    tab_list, tab_pace, tab_detail = st.tabs(
        ["📋 AI予測一覧", "🏁 レース展開", "🐎 馬詳細"]
    )

    raw_horses = [dict(h) for h in race.get("horses", [])]
    horses_list = assign_evaluations(raw_horses)
    horses_list.sort(key=lambda x: x.get("rank", 99))

    # --- TAB 1: AI予測一覧 ---
    with tab_list:
        st.subheader("📊 出走馬予測ランキング")

        table_html = (
            '<div style="overflow-x: auto;">'
            '<table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; overflow:hidden;">'
            '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">順位</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">メイン評価</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">馬番</th>'
            '<th style="padding:10px 6px; text-align:left; white-space:nowrap;">馬名</th>'
            '<th style="padding:10px 6px; text-align:left; white-space:nowrap;">騎手</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">脚質</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">単勝</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">地力評価</th>'
            '<th style="padding:10px 6px; text-align:center; white-space:nowrap;">条件適性</th>'
            "</tr></thead><tbody>"
        )

        for h in horses_list:
            rank_str = f"{h.get('rank', '—')}位"
            main_badge = h.get("main_badge", "—")
            num = h.get("num", "—")
            name = html.escape(str(h.get("name", "—")))
            jockey = html.escape(str(h.get("jockey", "不明")))
            running_style = html.escape(str(h.get("running_style", "不明")))
            odds = h.get("odds", "N/A")
            base_display = h.get("base_display", "—")
            cond_display = h.get("cond_display", "—")

            num_badge = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.7rem;">{num}</span>'
            style_badge = f'<span style="display:inline-block; padding:2px 4px; border-radius:4px; font-size:0.7rem; background:#e2e8f0; color:#1e293b; font-weight:bold;">{running_style}</span>'

            if main_badge != "—":
                badge_html = f'<span style="display:inline-block; padding:2px 6px; border-radius:999px; font-size:0.72rem; font-weight:bold; background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0;">{main_badge}</span>'
            else:
                badge_html = '<span style="color:#94a3b8; font-size:0.8rem;">—</span>'

            table_html += (
                '<tr style="border-bottom:1px solid #e2e8f0;">'
                f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f172a; white-space:nowrap;">{rank_str}</td>'
                f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{badge_html}</td>'
                f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{num_badge}</td>'
                f'<td style="padding:8px 4px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
                f'<td style="padding:8px 4px; text-align:left; color:#475569; white-space:nowrap;">{jockey}</td>'
                f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{style_badge}</td>'
                f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f766e; white-space:nowrap;">{odds}倍</td>'
                f'<td style="padding:8px 4px; text-align:center; white-space:nowrap; font-size:0.8rem;">{base_display}</td>'
                f'<td style="padding:8px 4px; text-align:center; white-space:nowrap; font-size:0.8rem;">{cond_display}</td>'
                "</tr>"
            )

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

    # --- TAB 2: レース展開 ---
    with tab_pace:
        pace = race.get("pace_forecast") or {}
        st.subheader("🏁 レース展開 ＆ ペース予測")

        if pace:
            p1, p2, p3 = st.columns(3)
            with p1:
                st.markdown(
                    f'<div class="metric-card"><small>⏱️ 想定ペース</small><br><b>{pace.get("pace", "不明")}</b></div>',
                    unsafe_allow_html=True,
                )
            with p2:
                st.markdown(
                    f'<div class="metric-card"><small>⚔️ 先行争い激度</small><br><b>{pace.get("competition_risk", "不明")}</b></div>',
                    unsafe_allow_html=True,
                )
            with p3:
                st.markdown(
                    f'<div class="metric-card"><small>🚩 前方展開候補</small><br><b>{pace.get("candidate_count", 0)}頭</b></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            candidates = pace.get("front_runner_candidates", [])
            if candidates:
                st.markdown("##### 🚀 展開を引っ張る注目馬")
                cand_html = '<div style="background:white; border:1px solid #cbd5e1; border-radius:8px; padding:12px; margin-bottom:16px;">'
                for c in candidates:
                    num_val = c.get("number", "?")
                    num_badge = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.7rem; margin-right:4px;">{num_val}</span>'
                    outside_str = (
                        " ↗️ 外枠から攻勢" if c.get("outside_draw_effort") else ""
                    )
                    cand_html += f'<div style="margin-bottom:6px;">{num_badge} <b>{html.escape(str(c.get("name", "")))}</b> <small style="color:#475569;">(⚡ 圧力: {c.get("pressure", 0):.2f})</small>{outside_str}</div>'
                cand_html += "</div>"
                st.markdown(cand_html, unsafe_allow_html=True)

            profiles = pace.get("style_profiles", [])
            if profiles:
                st.markdown("##### 🐎 出走馬の位置取り・脚質傾向")
                p_html = (
                    '<div style="overflow-x:auto;">'
                    '<table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; overflow:hidden;">'
                    '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
                    '<th style="padding:8px; text-align:center; white-space:nowrap;">🐴 馬番</th>'
                    '<th style="padding:8px; text-align:left; white-space:nowrap;">馬名</th>'
                    '<th style="padding:8px; text-align:center; white-space:nowrap;">🏃 脚質傾向</th>'
                    '<th style="padding:8px; text-align:center; white-space:nowrap;">🎯 好走位置適性</th>'
                    '<th style="padding:8px; text-align:center; white-space:nowrap;">📊 近走</th>'
                    "</tr></thead><tbody>"
                )

                for prof in profiles:
                    num_str = str(prof.get("horse_number", "?"))
                    name_str = html.escape(str(prof.get("horse_name", "不明")))
                    style_str = html.escape(str(prof.get("running_style", "不明")))
                    apt_str = html.escape(str(prof.get("aptitude_label", "判定なし")))
                    starts_val = prof.get("starts", 0)

                    num_badge = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.7rem;">{num_str}</span>'
                    style_badge = f'<span style="display:inline-block; padding:2px 6px; border-radius:4px; font-size:0.72rem; background:#e2e8f0; color:#1e293b; font-weight:bold;">{style_str}</span>'

                    p_html += (
                        '<tr style="border-bottom:1px solid #e2e8f0;">'
                        f'<td style="padding:8px; text-align:center; white-space:nowrap;">{num_badge}</td>'
                        f'<td style="padding:8px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name_str}</td>'
                        f'<td style="padding:8px; text-align:center; white-space:nowrap;">{style_badge}</td>'
                        f'<td style="padding:8px; text-align:center; color:#475569; white-space:nowrap;">{apt_str}</td>'
                        f'<td style="padding:8px; text-align:center; color:#64748b; white-space:nowrap;">{starts_val}走</td>'
                        "</tr>"
                    )

                p_html += "</tbody></table></div>"
                st.markdown(p_html, unsafe_allow_html=True)
        else:
            st.markdown("##### 🐎 出走馬の位置取り・脚質傾向")
            p_html = (
                '<div style="overflow-x:auto;">'
                '<table style="width:100%; border-collapse:collapse; font-size:0.85rem; background:white; border-radius:8px; overflow:hidden;">'
                '<thead><tr style="background:#f1f5f9; color:#334155; border-bottom:2px solid #cbd5e1;">'
                '<th style="padding:8px; text-align:center; white-space:nowrap;">🐴 馬番</th>'
                '<th style="padding:8px; text-align:left; white-space:nowrap;">馬名</th>'
                '<th style="padding:8px; text-align:left; white-space:nowrap;">騎手</th>'
                '<th style="padding:8px; text-align:center; white-space:nowrap;">🏃 脚質傾向</th>'
                "</tr></thead><tbody>"
            )
            for h in sorted(horses_list, key=lambda x: x.get("num", 99)):
                num_str = str(h.get("num", "?"))
                name_str = html.escape(str(h.get("name", "不明")))
                jockey_str = html.escape(str(h.get("jockey", "不明")))
                style_str = html.escape(str(h.get("running_style", "判定材料不足")))

                num_badge = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.7rem;">{num_str}</span>'
                style_badge = f'<span style="display:inline-block; padding:2px 6px; border-radius:4px; font-size:0.72rem; background:#e2e8f0; color:#1e293b; font-weight:bold;">{style_str}</span>'

                p_html += (
                    '<tr style="border-bottom:1px solid #e2e8f0;">'
                    f'<td style="padding:8px; text-align:center; white-space:nowrap;">{num_badge}</td>'
                    f'<td style="padding:8px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name_str}</td>'
                    f'<td style="padding:8px; text-align:left; color:#475569; white-space:nowrap;">{jockey_str}</td>'
                    f'<td style="padding:8px; text-align:center; white-space:nowrap;">{style_badge}</td>'
                    "</tr>"
                )
            p_html += "</tbody></table></div>"
            st.markdown(p_html, unsafe_allow_html=True)

    # --- TAB 3: 個別馬分析 ---
    with tab_detail:
        st.subheader("馬ごとのAI評価・詳細")
        st.markdown(
            "<small style='color:#64748b;'>選択した馬のAI評価スコアの内訳（地力・条件適性）とシグナルを詳細に確認できます。</small>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        horse_options = [
            f"{h.get('rank', '—')}位: {h.get('num', '—')}番 {h.get('name', '—')} ({h.get('main_badge', '一般')})"
            for h in horses_list
        ]
        selected_horse_str = st.selectbox(
            "詳細を確認する馬を選択",
            horse_options,
            key=f"horse_select_{unique_key}",
        )

        if selected_horse_str:
            selected_idx = horse_options.index(selected_horse_str)
            h = horses_list[selected_idx]

            base_val = float(h.get("base_score", 0.0) or 0.0)
            plus_val = float(h.get("plus_sum", 0.0) or 0.0)
            minus_val = float(h.get("minus_sum", 0.0) or 0.0)
            cond_val = plus_val + minus_val
            total_val = base_val + cond_val

            b_rank = get_base_rank(base_val)
            c_rank = get_cond_rank(cond_val)
            base_display = format_rank_emoji(b_rank, base_val)
            cond_display = format_rank_emoji(c_rank, cond_val)
            main_badge = h.get("main_badge", "—")

            signals = h.get("one_change_signals", [])
            if signals:
                signals_badges = " ".join(
                    [
                        f'<span style="display:inline-block; padding:3px 8px; border-radius:6px; font-size:0.78rem; font-weight:bold; background:#e0f2fe; color:#0369a1; border:1px solid #bae6fd; margin:2px;">{html.escape(str(sig))}</span>'
                        for sig in signals
                    ]
                )
            else:
                signals_badges = (
                    '<span style="color:#94a3b8; font-size:0.85rem;">なし</span>'
                )

            reasons_text = h.get("reasons") or "特筆すべき特記事項なし"

            detail_html = (
                '<div class="horse-detail-box">'
                f'<h4 style="margin:0; color:#0f766e;">{h.get("num", "—")}番 {html.escape(str(h.get("name", "—")))} <span style="font-size:0.9rem; color:#475569;">({h.get("rank", "—")}位)</span></h4>'
                '<hr style="margin:8px 0; border:0; border-top:1px solid #e2e8f0;">'
                f"<b>🏷️ メイン評価:</b> {main_badge}<br>"
                f"<b>🏇 騎手 / 脚質:</b> {html.escape(str(h.get('jockey', '不明')))} / {html.escape(str(h.get('running_style', '不明')))}<br>"
                f"<b>💰 単勝オッズ:</b> {h.get('odds', 'N/A')}倍<br><br>"
                "<b>🏷️ 特筆シグナル (検知タグ):</b><br>"
                f'<div style="margin-top:4px; margin-bottom:10px;">{signals_badges}</div>'
                "<b>📊 AI総合評価スコアの内訳:</b><br>"
                '<div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:0.85rem; color:#1e293b; margin-top:4px;">'
                f"<b>• 地力評価 (基準点):</b> {base_display}<br>"
                f'<b>• 📈 加点合計 (強みの積み上げ):</b> <span style="color:#047857; font-weight:bold;">{plus_val:+.2f}</span><br>'
                f'<b>• 📉 減点合計 (懸念・リスク):</b> <span style="color:#b91c1c; font-weight:bold;">{minus_val:+.2f}</span><br>'
                f"<b>• 条件適性合計:</b> {cond_display}<br>"
                '<hr style="margin:6px 0; border:0; border-top:1px dashed #cbd5e1;">'
                f"<b>🎯 最終トータルスコア: {total_val:+.2f}</b>"
                "</div><br>"
                "<b>📈 要因分析・モデル寄与度の詳細:</b><br>"
                '<div style="background:#f8fafc; padding:8px; border-radius:6px; font-size:0.85rem; color:#334155; margin-top:4px;">'
                f"{reasons_text}"
                "</div>"
                "</div>"
            )
            st.markdown(detail_html, unsafe_allow_html=True)


# ==========================================
# 5. メイン処理（競馬場選択 ＆ 1R〜上段タブ表示）
# ==========================================
st.markdown('<p class="app-title">🏇 AI競馬予測システム</p>', unsafe_allow_html=True)

races = load_prediction_data()

if not races:
    st.warning(
        "`latest_prediction.json` または `predict_results.json` が見つかりません。ファイルを配置してください。"
    )
    st.stop()

# 競馬場ごとにレースをグループ化
track_groups = {}
for r in races:
    t_name = extract_track_name(r)
    track_groups.setdefault(t_name, []).append(r)

# JRA標準の競馬場順（札幌〜小倉）に並び替え
available_tracks = sorted(
    track_groups.keys(),
    key=lambda t: TRACK_NAMES.index(t) if t in TRACK_NAMES else 99,
)

# 1. 競馬場フィルター
selected_track = st.selectbox("🏟️ 競馬場を選択", available_tracks)
filtered_races = track_groups[selected_track]

# 発走時刻順・レース番号順でソートし、1R〜12Rの番号を確定
for idx, r in enumerate(filtered_races, start=1):
    r["_start_time"] = extract_start_time(r)
    r["_raw_num"] = extract_race_num(r, 99)

filtered_races.sort(key=lambda r: (r["_raw_num"], r["_start_time"]))

for idx, r in enumerate(filtered_races, start=1):
    r["_race_num"] = r["_raw_num"] if r["_raw_num"] != 99 else idx

# 2. 上段タブ（1R〜）の生成と描画
race_tab_labels = [f"{r['_race_num']}R" for r in filtered_races]
race_tabs = st.tabs(race_tab_labels)

for tab, race_data in zip(race_tabs, filtered_races):
    with tab:
        unique_key = f"{selected_track}_{race_data['_race_num']}R"
        render_race_content(race_data, unique_key)
