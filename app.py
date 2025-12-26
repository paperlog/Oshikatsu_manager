import streamlit as st
import pandas as pd
import plotly.express as px
import io
from PIL import Image, ImageDraw, ImageFont

def generate_oshi_image(event_name, total_spent, remaining, member_color, uploaded_file, items_data, fig):
    # 1. キャンバス作成 (1200x630)
    width, height = 1200, 630
    # 背景は白、縁取りに推しカラーを使用する清潔感のあるデザイン
    canvas = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    # 外枠（推しカラーの細い線）
    draw.rectangle([0, 0, width-1, height-1], outline=member_color, width=15)

    # 2. フォント設定 (ファイル名は正確に指定) 
    font_path = "font.ttf" 
    try:
        font_title = ImageFont.truetype(font_path, 55)
        font_label = ImageFont.truetype(font_path, 30)
        font_value = ImageFont.truetype(font_path, 45)
    except:
        font_title = font_label = font_value = ImageFont.load_default()

    # --- 要素の配置 ---
    # A. タイトル
    draw.text((60, 40), f"💖 {event_name}", fill=member_color, font=font_title)

    # B. 推し画像 (左側)
    if uploaded_file is not None:
        user_img = Image.open(uploaded_file).convert("RGBA")
        user_img.thumbnail((400, 400))
        canvas.paste(user_img, (60, 130), user_img if user_img.mode == 'RGBA' else None)

    # C. 支出明細 (中央)
    draw.text((500, 130), "【 支出明細 】", fill="#333333", font=font_label)
    y_offset = 180
    # 最大6項目まで表示（画像からはみ出さないよう調整）
    for index, row in items_data.head(6).iterrows():
        item_text = f"・{row['項目']}"
        price_text = f"{row['金額']:,}円"
        draw.text((500, y_offset), item_text, fill="#555555", font=font_label)
        draw.text((750, y_offset), price_text, fill="#555555", font=font_label)
        y_offset += 45
    
    # 合計と残り
    draw.text((500, 460), f"支出合計: {total_spent:,}円", fill="#333333", font=font_value)
    draw.text((500, 520), f"予算残り: {remaining:,}円", fill=member_color, font=font_value)

    # D. グラフ (右側)
    try:
        # グラフを画像化。scaleを上げて画質を確保
        img_bytes = fig.to_image(format="png", width=400, height=400, scale=2)
        graph_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        canvas.paste(graph_img, (820, 150), graph_img)
    except:
        st.error("グラフの画像化に失敗しました。kaleidoがインストールされているか確認してください。")

    return canvas

st.set_page_config(page_title="推し活マネージャー", layout="wide")

# --- 1. データの初期化 (計算エラーを防ぐために最初に定義) ---
if 'budget_df' not in st.session_state:
    st.session_state.budget_df = pd.DataFrame([
        {"項目": "チケット代", "金額": 12000},
        {"項目": "交通費", "金額": 5000},
        {"項目": "グッズ代", "金額": 10000},
    ])

# --- 2. サイドバー設定 ---
st.sidebar.header("カスタマイズ")
uploaded_file = st.sidebar.file_uploader("推しの写真をアップロード", type=["jpg", "jpeg", "png"])
member_color = st.sidebar.color_picker("推しカラーを選択", "#A9EEFF")
event_name = st.sidebar.text_input("イベント名", "推しのライブ")
total_budget = st.sidebar.number_input("全体の予算 (円)", value=50000, step=1000)

# --- 3. CSS設定 (画像とグラフのサイズを固定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {member_color}08; }}
    h1, h2, h3 {{ color: {member_color} !important; }}
    /* 画像の縦幅を固定して1画面に収める */
    .main-img img {{
        max-height: 400px;
        object-fit: contain;
        border: 3px solid {member_color};
        border-radius: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title(f"{event_name}")

# タブの作成
tab1, tab2 = st.tabs(["予算管理", "スケジュール"])

with tab1:
    # --- 💡 ここがポイント：表示の前にまずデータを確定させる ---
    # ユーザーが編集できる表を先に配置（隠し要素にせず、中央に置くための準備）
    
    # 三分割レイアウトの開始
    col_img, col_table, col_graph = st.columns([1, 1.5, 1.3])

    with col_img:
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
        else:
            st.info("サイドバーから画像をアップロード")

    with col_table:
        st.write("### 支出入力")
        # 編集されたデータを items_data として取得
        items_data = st.data_editor(
            st.session_state.budget_df,
            num_rows="dynamic",
            use_container_width=True,
            key="budget_editor_final"
        )
        
        # 計算
        total_spent = items_data["金額"].sum()
        remaining = total_budget - total_spent
        
        # 数字を表示
        m1, m2 = st.columns(2)
        m1.metric("合計支出", f"{total_spent:,}円")
        m2.metric("予算残り", f"{remaining:,}円", delta=remaining)

    with col_graph:
        st.write("### 割合分析")
        fig = px.pie(
            items_data, values='金額', names='項目', 
            color_discrete_sequence=[member_color, "#f0f2f6", "#cccccc", "#999999"]
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',  
            font_color=member_color,
            legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=0, b=0, l=0, r=0), 
            height=250 
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("✨ シェア用画像を作成"):
        # 関数に fig (グラフ) を渡し忘れないように修正
        report_img = generate_oshi_image(
            event_name, total_spent, remaining, member_color, uploaded_file, items_data, fig
        )
    
        # プレビューとダウンロード
        buf = io.BytesIO()
        report_img.save(buf, format="PNG")
        st.sidebar.image(report_img, caption="完成イメージ", use_container_width=True)
        st.sidebar.download_button(
            label="📥 画像を保存する",
            data=buf.getvalue(),
            file_name=f"{event_name}_report.png",
            mime="image/png"
        )

with tab2:
    st.write("▼ スケジュール入力")
    # スケジュール用のエディタも同様に配置
    st.data_editor(pd.DataFrame([
            {"時間": "12:00", "予定": "会場到着・物販並び"},
            {"時間": "18:00", "予定": "開演！"},
            {"時間": "20:00", "予定": "閉演！"},
        ]),
        num_rows="dynamic",
        use_container_width=True,
        key="schedule_editor"

    )









