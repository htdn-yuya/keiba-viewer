import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
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

    vol = prepared_result.get("volatility", {})
    horses_list = prepared_result.get("horses", [])
    top_horse = horses_list[0] if horses_list else None
    top_odds = top_horse.get("odds", "N/A") if top_horse else "N/A"

    # ==========================================
    # 📑 タブ切り替え
    # ==========================================
    tab_list, tab_detail, tab_anim = st.tabs(
        [
            "📋 予測一覧 ＆ インサイト",
            "🔍 個別馬・要因可視化",
            "🎬 トラックレースアニメーション",
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
            num_val = top_horse.get("num", "-") if top_horse else "-"
            st.markdown(
                f'<div class="metric-card"><small>本命予測1位</small><br><b>{to_maru_num(num_val)} {top_odds}倍</b></div>',
                unsafe_allow_html=True,
            )
        with col3:
            myumi_count = sum(
                1 for h in horses_list if "旨味" in h.get("myumi_tag", "")
            )
            st.markdown(
                f'<div class="metric-card"><small>妙味馬検知</small><br><b>{myumi_count}頭</b></div>',
                unsafe_allow_html=True,
            )

        if vol.get("decision"):
            st.markdown(
                f"<small style='color:#475569;'>💡 {vol['decision']}</small>",
                unsafe_allow_html=True,
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
            num = h.get("num", "-")
            name = h.get("name", "不明")
            jockey = h.get("jockey", "不明")
            running_style = h.get("running_style", "-")
            odds = h.get("odds", "-")
            myumi_tag = h.get("myumi_tag", "") if h.get("myumi_tag") else "-"
            axis_stars = h.get("axis_stars", "")
            hole_stars = h.get("hole_stars", "")

            badge_html = f'<span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:#0f766e; color:white; font-weight:bold; font-size:0.75rem;">{to_maru_num(num)}</span>'
            style_badge = f'<span style="display:inline-block; padding:2px 4px; border-radius:4px; font-size:0.7rem; background:#e2e8f0; color:#1e293b; font-weight:bold;">{running_style}</span>'

            myumi_badge = "-"
            if "旨味" in myumi_tag:
                myumi_badge = '<span style="color:#d97706; font-weight:bold; font-size:0.7rem;">🔥 旨味大</span>'
            elif "トリガミ" in myumi_tag:
                myumi_badge = '<span style="color:#dc2626; font-weight:bold; font-size:0.7rem;">⚠️ 注意</span>'

            table_html += '<tr style="border-bottom:1px solid #e2e8f0;">'
            table_html += f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f172a; white-space:nowrap;">{rank_str}位</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;"><span style="display:inline-block; padding:2px 4px; border-radius:999px; font-size:0.65rem; font-weight:bold; background:#f1f5f9; color:#0f766e; border:1px solid #cbd5e1;">{tag_str}</span></td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{badge_html}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:left; font-weight:bold; color:#0f172a; white-space:nowrap;">{name}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:left; color:#475569; white-space:nowrap;">{jockey}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{style_badge}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; font-weight:bold; color:#0f766e; white-space:nowrap;">{odds}倍</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; white-space:nowrap;">{myumi_badge}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; color:#d97706; white-space:nowrap; font-size:0.75rem;">{axis_stars}</td>'
            table_html += f'<td style="padding:8px 4px; text-align:center; color:#d97706; white-space:nowrap; font-size:0.75rem;">{hole_stars}</td>'
            table_html += "</tr>"

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

    # --- TAB 2: 個別馬・要因可視化 ---
    with tab_detail:
        st.subheader("🔍 個別馬の詳細分析・要因比較")
        st.markdown(
            "<small style='color:#64748b;'>選択した馬のAI評価スコアの内訳とシグナルを確認できます。</small>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        horse_options = [
            f"{h.get('rank', '-')}位: {to_maru_num(h.get('num', '-'))}番 {h.get('name', '不明')} ({h.get('tag') if h.get('tag') else '一般'})"
            for h in horses_list
        ]
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

            st.markdown(
                f"""<div class="horse-detail-box">
<h4 style="margin:0; color:#0f766e;">{to_maru_num(h.get("num", "-"))}番 {h.get("name", "不明")} <span style="font-size:0.9rem; color:#475569;">({h.get("rank", "-")}位)</span></h4>
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
{h.get("reasons") if h.get("reasons") else "特筆すべき特記事項なし"}
</div>
</div>""",
                unsafe_allow_html=True,
            )

    # --- TAB 3: 🎬 トラックレースアニメーション ---
    with tab_anim:
        st.subheader("🎬 トラックレース展開アニメーション")
        st.markdown(
            "<small style='color:#475569;'>競馬場のオーバルコース（楕円トラック）に沿って、スタートからゴールまでの各馬のポジション入れ替わりをスマホでスッキリ再現します。</small>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if horses_list:
            total_h = len(horses_list)
            phases = [
                "1. スタート",
                "2. 第1コーナー",
                "3. 第2コーナー",
                "4. 向こう正面",
                "5. 第3コーナー",
                "6. 第4コーナー",
                "7. 直線",
                "8. ゴール",
            ]

            anim_data = []
            import random

            # トラック上の位置パラメータ s (0.0 ~ 1.0) をフェーズごとに算出
            phase_progress = {
                "1. スタート": 0.0,
                "2. 第1コーナー": 0.12,
                "3. 第2コーナー": 0.25,
                "4. 向こう正面": 0.45,
                "5. 第3コーナー": 0.65,
                "6. 第4コーナー": 0.82,
                "7. 直線": 0.93,
                "8. ゴール": 1.0,
            }

            for h in horses_list:
                num = h.get("num", 1)
                name = h.get("name", "不明")
                style = h.get("running_style", "差し")
                final_rank = h.get("rank", 1)
                burst = h.get("burst_score", 0.5)
                maru_num = to_maru_num(num)

                # 脚質に応じたスタート時のベース順位
                if style == "逃げ":
                    base_start = random.randint(1, max(2, int(total_h * 0.2)))
                elif style == "先行":
                    base_start = random.randint(2, max(4, int(total_h * 0.4)))
                elif style == "差し":
                    base_start = random.randint(int(total_h * 0.4), int(total_h * 0.7))
                else:
                    base_start = random.randint(int(total_h * 0.7), total_h)

                base_start = max(1, min(total_h, base_start))

                for step_idx, phase in enumerate(phases):
                    p_val = phase_progress[phase]

                    # 進行に応じた順位の推移
                    if step_idx == 0:
                        curr_rank = base_start
                    elif step_idx in [1, 2]:
                        curr_rank = (
                            base_start
                            if style in ("逃げ", "先行")
                            else int(total_h * 0.7)
                        )
                    elif step_idx in [3, 4, 5]:
                        progress_ratio = step_idx / len(phases)
                        target_blend = (
                            base_start * (1 - progress_ratio)
                            + final_rank * progress_ratio
                        )
                        burst_boost = -int((burst - 0.5) * 3)
                        curr_rank = int(
                            max(1, min(total_h, target_blend + burst_boost))
                        )
                    elif step_idx == 6:
                        curr_rank = int(round(base_start * 0.15 + final_rank * 0.85))
                    else:
                        curr_rank = final_rank

                    curr_rank = max(1, min(total_h, curr_rank))

                    # 楕円トラック上の座標 (x, y) 計算 (反時計回り)
                    # 順位が上の馬ほど前へ (sを少し進める)
                    effective_s = p_val - (curr_rank - 1) * (0.03 / max(1, total_h - 1))
                    effective_s = effective_s % 1.0

                    t = 2 * np.pi * effective_s - np.pi / 2
                    Rx, Ry = 4.0, 2.0  # コースの横幅・縦幅

                    # イン・外のラチ調整
                    lane_offset = 0.25 * ((num % 3) - 1)
                    x = Rx * np.cos(t) + lane_offset * np.sin(t)
                    y = Ry * np.sin(t) - lane_offset * np.cos(t)

                    anim_data.append(
                        {
                            "Phase": phase,
                            "StepOrder": step_idx,
                            "HorseLabel": f"{maru_num} {name}",
                            "x": x,
                            "y": y,
                            "Style": style,
                            "Rank": curr_rank,
                        }
                    )

            df_anim = pd.DataFrame(anim_data)

            # トラック背景用の軌道を描画するためのデータ作成
            t_line = np.linspace(0, 2 * np.pi, 100)
            track_x = 4.0 * np.cos(t_line)
            track_y = 2.0 * np.sin(t_line)
            df_track = pd.DataFrame({"x": track_x, "y": track_y})

            # Plotlyでアニメーション散布図作成
            fig = px.scatter(
                df_anim,
                x="x",
                y="y",
                color="Style",
                text="HorseLabel",
                animation_frame="Phase",
                animation_group="HorseLabel",
                range_x=[-5.5, 5.5],
                range_y=[-3.0, 3.0],
                height=400,  # スマホで見やすいコンパクトな高さ
            )

            # トラックの内ラチ（コース線）を追加
            fig.add_scatter(
                x=df_track["x"],
                y=df_track["y"],
                mode="lines",
                line=dict(color="#047857", width=2, dash="dash"),
                showlegend=False,
                hoverinfo="skip",
            )

            fig.update_traces(textposition="top center", marker=dict(size=16))
            fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    visible=False,
                    scaleanchor="x",
                    scaleratio=1,
                ),
                plot_bgcolor="#ecfdf5",  # 芝生風の薄い緑色背景
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=30, b=10),
                transition=dict(duration=700),
            )

            st.plotly_chart(fig, use_container_width=True)
            st.info(
                "💡 **使い方:** グラフの下にある **▶️（再生ボタン）** を押すと、芝生トラックの上を馬番（①②…）のドットがコーナーに沿って駆け抜けます！"
            )
        else:
            st.warning("出走馬データが見つかりません。")
