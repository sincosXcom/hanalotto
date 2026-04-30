import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import random
from collections import Counter

st.set_page_config(page_title="花图乐透 – HANALOTTO", layout="wide")

# ========== 数据加载 ==========
@st.cache_data
def load_lotto_data():
    csv_path = "data/klotto.csv"
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='cp949')
    except:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')

    col_map = {
        '회차': 'issue', '날짜': 'date',
        '당첨번호1': 'n1', '당첨번호2': 'n2', '당첨번호3': 'n3',
        '당첨번호4': 'n4', '당첨번호5': 'n5', '당첨번호6': 'n6',
        '보너스번호': 'special'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    required = ['issue', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'special']
    for col in required:
        if col not in df.columns:
            st.error(f"CSV 缺少列: {col}")
            st.stop()
    df = df.sort_values('issue', ascending=True).reset_index(drop=True)
    return df

@st.cache_data
def load_card_images():
    images = {}
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    for i in range(1, 46):
        path = os.path.join("images", f"{i}.png")
        if not os.path.exists(path):
            path = os.path.join("images", f"{i}.jpg")
        if not os.path.exists(path):
            img = Image.new('RGB', (80, 110), color=(128,128,128))
        else:
            img = Image.open(path).convert("RGBA")
            img = img.resize((80, 110))
        draw = ImageDraw.Draw(img)
        radius = 16
        x = img.width - radius - 5
        y = img.height - radius - 5
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255))
        text = str(i)
        bbox = draw.textbbox((0,0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((x - text_w//2, y - text_h//2), text, fill=(255,0,0), font=font)
        images[i] = img
    return images

def show_numbers_as_icons(numbers, special_num=None, title=None):
    """显示一组号码的图标+数字，可选标题"""
    if title:
        st.markdown(f"**{title}**")
    cols = st.columns(len(numbers))
    for idx, num in enumerate(numbers):
        with cols[idx]:
            st.image(images[num], width=80)
            if special_num is not None and num == special_num:
                st.markdown(f"<p style='color:#ffaa00; text-align:center; font-weight:bold;'>{num:02d} ★</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align:center;'>{num:02d}</p>", unsafe_allow_html=True)

# ========== 预测函数（基于历史频率） ==========
def predict_numbers(df, num_main=6, num_special=1):
    """基于历史出现频率，返回推荐的 main + special 列表"""
    all_numbers = []
    special_numbers = []
    for _, row in df.iterrows():
        for i in range(1,7):
            all_numbers.append(int(row[f'n{i}']))
        special_numbers.append(int(row['special']))
    
    main_counter = Counter(all_numbers)
    special_counter = Counter(special_numbers)
    
    # 主号码：按频率降序，取前 num_main 个，若并列则随机
    main_candidates = sorted(main_counter.items(), key=lambda x: x[1], reverse=True)
    main_picks = [num for num, _ in main_candidates[:num_main]]
    # 如果不足（理论上不会），则从剩余号码中补充
    if len(main_picks) < num_main:
        remaining = set(range(1,46)) - set(main_picks)
        main_picks.extend(random.sample(remaining, num_main - len(main_picks)))
    
    # 特别号：从除了主号码以外的号码中，按频率选最高，或随机
    special_candidates = [(num, cnt) for num, cnt in special_counter.items() if num not in main_picks]
    if special_candidates:
        special_candidates.sort(key=lambda x: x[1], reverse=True)
        special_pick = special_candidates[0][0]
    else:
        remaining = set(range(1,46)) - set(main_picks)
        special_pick = random.choice(list(remaining))
    
    return main_picks, [special_pick]

# ========== 回调函数 ==========
def on_checkbox_change(num):
    key = f"chk_{num}"
    is_checked = st.session_state.get(key, False)
    
    if is_checked:
        if len(st.session_state.selected_numbers) < 6:
            if num not in st.session_state.selected_numbers:
                st.session_state.selected_numbers.append(num)
        else:
            st.session_state[key] = False
            st.warning("最多只能选6个号码！", icon="⚠️")
    else:
        if num in st.session_state.selected_numbers:
            st.session_state.selected_numbers.remove(num)

# ========== 初始化 ==========
df = load_lotto_data()
images = load_card_images()

if "selected_numbers" not in st.session_state:
    st.session_state.selected_numbers = []
if "current_idx" not in st.session_state:
    st.session_state.current_idx = len(df) - 1
if "prediction" not in st.session_state:
    st.session_state.prediction = None   # 存储预测结果 (main, special)

# ========== 左侧边栏 ==========
st.sidebar.header("📜 HISTORY")
options = [f"{int(row['issue'])}期 ({str(row.get('date',''))[:10]})" for _, row in df.iterrows()]
selected_option = st.sidebar.selectbox("选择期数", options, index=len(df)-1, key="sidebar_select")
selected_idx = options.index(selected_option)
row_sidebar = df.iloc[selected_idx]
main_sidebar = [int(row_sidebar[f'n{i}']) for i in range(1,7)]
special_sidebar = int(row_sidebar['special'])

st.sidebar.markdown("#### 本期开奖号码")
with st.sidebar:
    cols_main = st.columns(6)
    for i, num in enumerate(main_sidebar):
        with cols_main[i]:
            st.image(images[num], width=50)
            st.markdown(f"<p style='text-align:center;'>{num:02d}</p>", unsafe_allow_html=True)
    st.markdown(f"**Special**: {special_sidebar:02d}  ⭐")

# 在侧边栏底部添加预测按钮
st.sidebar.markdown("---")
if st.sidebar.button("🔮 生成预测号码", use_container_width=True):
    main_pred, special_pred = predict_numbers(df)
    st.session_state.prediction = (main_pred, special_pred)
    st.rerun()

# ========== 顶部浏览区 ==========
st.markdown("### 📺 Hanafuda + Korea LOTTO 2026")

col_left, col_mid, col_right = st.columns([1, 8, 1])
with col_left:
    if st.button("◀ 上一期", use_container_width=True):
        if st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
with col_right:
    if st.button("下一期 ▶", use_container_width=True):
        if st.session_state.current_idx < len(df)-1:
            st.session_state.current_idx += 1
            st.rerun()

# 索引条（全部期数，但用户可以通过滑块快速跳转）
all_issues = df['issue'].astype(int).tolist()
current_issue = int(df.iloc[st.session_state.current_idx]['issue'])
slider_issue = st.select_slider(
    "快速跳转到任意期数（共{}期）".format(len(all_issues)),
    options=all_issues,
    value=current_issue,
    key="issue_slider"
)
if slider_issue != current_issue:
    new_idx = df[df['issue'] == slider_issue].index[0]
    st.session_state.current_idx = new_idx
    st.rerun()

# 显示当前期数开奖号码
current_row = df.iloc[st.session_state.current_idx]
issue_num = int(current_row['issue'])
date_str = str(current_row.get('date', ''))[:10]
main_current = [int(current_row[f'n{i}']) for i in range(1,7)]
special_current = int(current_row['special'])

st.markdown(f"**{issue_num}期 ({date_str})**")
show_numbers_as_icons(main_current + [special_current], special_num=special_current)
st.divider()

# ========== 预测结果显示区域（最新一期下方，选号区上方） ==========
if st.session_state.prediction:
    pred_main, pred_special = st.session_state.prediction
    st.markdown("### 🔮 本期预测参考（基于历史频率）")
    show_numbers_as_icons(pred_main + pred_special, special_num=pred_special[0])
    st.caption("预测依据：统计历次开奖中每个号码的出现频率，选取高频主号码 + 出现最多的特别号码（不与主号重复）。仅供娱乐。")
    st.divider()

# ========== 选号区 ==========
st.header("🎨 点击下方复选框选号（最多6个）")
selected = sorted(st.session_state.selected_numbers)
st.markdown(f"**✨ 已选号码：** {selected if selected else '未选'}")
if len(selected) == 6:
    st.success("已选满6个号码，可以保存或继续更换。")

col_save, col_clear = st.columns(2)
with col_save:
    if st.button("💾 保存选号"):
        with open("user_selection.txt", "w", encoding="utf-8") as f:
            f.write(str(selected))
        st.success("保存成功！")
with col_clear:
    if st.button("🗑️ 清空所有"):
        st.session_state.selected_numbers = []
        for num in range(1, 46):
            key = f"chk_{num}"
            if key in st.session_state:
                st.session_state[key] = False
        st.rerun()

# 显示45个复选框
cols_per_row = 9
for i in range(0, 45, cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        num = i + j + 1
        if num > 45:
            break
        with cols[j]:
            st.image(images[num], width=80)
            st.checkbox(
                " ",
                key=f"chk_{num}",
                value=(num in st.session_state.selected_numbers),
                on_change=on_checkbox_change,
                args=(num,),
                label_visibility="collapsed"
            )

st.caption("💡 勾选复选框即可选号，最多6个。已选号码会实时显示在上方。Designed by sincosXcom")
