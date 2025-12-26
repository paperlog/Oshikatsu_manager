import streamlit as st
import pandas as pd
import plotly.express as px
import io
from PIL import Image, ImageDraw, ImageFont

def generate_oshi_image(event_name, total_spent, remaining, member_color, uploaded_file, items_data):
    # キャンバスサイズ (SNS投稿に最適なサイズ)
    width, height = 1200, 630
    # 推しカラーを背景に薄く敷く
    bg_color = member_color + "1A" # 10%程度の透明度
    canvas = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(canvas)
    
    # 背景に色をつける
    draw.rectangle([0, 0, width, height], fill=bg_color)

    # --- フォントの設定 (重要) ---
    try:
        # フォルダに置いたフォントファイルを読み込む
        font_path = "font.ttf" 
        font_title = ImageFont.truetype(font_path, 60)
        font_text = ImageFont.truetype(font_path, 40)
        font_price = ImageFont.truetype(font_path, 50)
    except:
        # フォントがない場合はデフォルト
        font_title = font_text = font_price = ImageFont.load_default()

    # 1. タイトル
    draw.text((50, 40), f"💖 {event_name}", fill=member_color, font=font_title)

    # 2. 推し画像 (左側に配置)
    if uploaded_file is not None:
        user_img = Image.open(uploaded_file).convert("RGBA")
        # 縦横比を維持してリサイズ
        user_img.thumbnail((450, 450))
        canvas.paste(user_img, (50, 130), user_img if user_img.mode == 'RGBA' else None)

    # 3. 集計データ (中央に配置)
    draw.text((550, 150), "合計支出:", fill="#333333", font=font_text)
    draw.text((550, 210), f"{total_spent:,} 円", fill="#333333", font=font_price)
    
    draw.text((550, 320), "予算残り:", fill="#333333", font=font_text)
    draw.text((550, 380), f"{remaining:,} 円", fill=member_color, font=font_price)

    # 4. グラフ (右側に配置)
    # 前の工程で作った Plotly の fig を画像化
    try:
        img_bytes = fig.to_image(format="png", width=500, height=500, scale=2)
        graph_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        graph_img.thumbnail((400, 400))
        canvas.paste(graph_img, (750, 130), graph_img)
    except:
        pass

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
    
    # --- ボタンとダウンロード処理 ---
    if st.sidebar.button("✨ シェア用画像を作成"):
        canvas = generate_oshi_image(event_name, total_spent, remaining, member_color, uploaded_file, items_data)
    
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.sidebar.image(canvas, caption="作成された画像", use_container_width=True)
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





