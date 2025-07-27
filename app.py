import streamlit as st
import pandas as pd
import os
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.graph_objs as go
import plotly.express as px
import numpy as np

# Matplotlib 中文支持
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="选矿数据管理系统", page_icon="⛏️", layout="wide")

DATA_PATH = "data.xlsx"
COLUMNS = [
    '日期', '原矿吨数', '原矿金品位', '尾液品位', '尾固品位',
    '尾液含金', '尾固含金', '溢流浓度', '溢流细度', '停机时间',
    '尾矿品位', '回收率', '回收金属量'
]
ALIAS = {
    "原矿品位": "原矿金品位", "金品位": "原矿金品位", "品位": "原矿金品位",
    "尾液金": "尾液含金", "尾固金": "尾固含金",
    "浓度": "溢流浓度", "细度": "溢流细度",
    "吨位": "原矿吨数", "金属量": "回收金属量", "日期": "日期"
}

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        pd.DataFrame(columns=COLUMNS).to_excel(DATA_PATH, index=False)
    df = pd.read_excel(DATA_PATH, parse_dates=['日期'])
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df

def save_data(df):
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df.to_excel(DATA_PATH, index=False)
    st.session_state['data_updated'] = True
    st.cache_data.clear()
    st.rerun()

def derive_data(df):
    df = df.copy()
    for col in ['原矿吨数', '原矿金品位', '尾液含金', '尾固含金']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df2 = df.dropna(subset=['原矿吨数', '原矿金品位', '尾液含金', '尾固含金'])
    df2['尾矿品位'] = df2['尾液含金'] + df2['尾固含金']
    df2['回收率'] = ((df2['原矿金品位'] - df2['尾矿品位']) / df2['原矿金品位']).clip(0, 1)
    df2['回收金属量'] = df2['原矿吨数'] * df2['原矿金品位'] * df2['回收率']
    df.update(df2)
    return df

def read_uploaded_file(f):
    try:
        df = pd.read_excel(f)
        df.columns = [ALIAS.get(c.strip(), c.strip()) for c in df.columns]
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[COLUMNS]
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"文件读取失败：{e}")
        return pd.DataFrame()

df = load_data()
if 'data_updated' not in st.session_state:
    st.session_state['data_updated'] = False

menu = st.sidebar.radio(
    "功能选择",
    ["输入数据", "数据表", "分析图表"], index=0
)

if menu == "输入数据":
    st.header("数据录入与导入")
    uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx"])
    if uploaded_file:
        new_df = read_uploaded_file(uploaded_file)
        if not new_df.empty:
            st.dataframe(new_df.head())
            if st.button("合并导入数据"):
                combined = pd.concat([df, new_df], ignore_index=True)
                save_data(derive_data(combined))
                st.success("文件已导入并保存")
        else:
            st.warning("文件内容为空或格式错误")

    st.subheader("手动输入数据")
    with st.form("manual_input"):
        cols = st.columns(3)
        date = cols[0].date_input("日期", datetime.today())
        ore = cols[0].number_input("原矿吨数", min_value=0.0, format="%.2f")
        grade = cols[0].number_input("原矿金品位", min_value=0.0, format="%.4f")
        tail_solu_grade = cols[1].number_input("尾液品位", min_value=0.0, format="%.4f")
        tail_solid_grade = cols[1].number_input("尾固品位", min_value=0.0, format="%.4f")
        tail_solu_au = cols[1].number_input("尾液含金", min_value=0.0, format="%.4f")
        tail_solid_au = cols[2].number_input("尾固含金", min_value=0.0, format="%.4f")
        conc = cols[2].number_input("溢流浓度", min_value=0.0, format="%.2f")
        grind = cols[2].number_input("溢流细度", min_value=0.0, format="%.2f")
        stop = cols[2].number_input("停机时间", min_value=0.0, format="%.0f")
        if st.form_submit_button("保存"):
            row = pd.DataFrame([{
                "日期": pd.to_datetime(date),
                "原矿吨数": ore, "原矿金品位": grade,
                "尾液品位": tail_solu_grade, "尾固品位": tail_solid_grade,
                "尾液含金": tail_solu_au, "尾固含金": tail_solid_au,
                "溢流浓度": conc, "溢流细度": grind, "停机时间": stop,
                "尾矿品位": None, "回收率": None, "回收金属量": None
            }])
            combined = pd.concat([df, row], ignore_index=True)
            save_data(derive_data(combined))
            st.success("已保存")

elif menu == "数据表":
    st.header("数据表管理")

    # 1. 在侧边栏设置小数位数
    decimal_places = st.sidebar.number_input("数值小数位数", min_value=0, max_value=6, value=3, step=1)

    # 2. 生成显示用DataFrame
    df_show = df.copy()
    df_show['日期'] = pd.to_datetime(df_show['日期'], errors='coerce').dt.strftime('%Y-%m-%d')

    for c in df_show.columns:
        if c != '日期':
            # 动态保留小数位
            df_show[c] = np.round(pd.to_numeric(df_show[c], errors='coerce'), decimal_places)

    # 3. 构建AgGrid参数，自动列宽
    gb = GridOptionsBuilder.from_dataframe(df_show)
    gb.configure_default_column(
        editable=True,
        resizable=True,
        autoWidth=True,  # 自动宽度
        cellStyle={'textAlign': 'center'},
    )
    gb.configure_column("日期", width=360)
    for col in df_show.columns:
        gb.configure_column(col, filter=False, menuTabs=[])

    gridOptions = gb.build()

    # 4. 渲染表格
    AgGrid(
        df_show,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,  # 自动列宽
        allow_unsafe_jscode=True,
        theme='alpine'
    )

    # 5. 添加公式列表单
    st.markdown("### 添加公式列")
    with st.form("add_formula", clear_on_submit=True):
        col1, col2 = st.columns([1,2])
        new_col = col1.text_input("新列名")
        formula = col2.text_input("公式（如：原矿吨数 * 原矿金品位 * 回收率）")
        if st.form_submit_button("添加") and new_col and formula:
            try:
                df[new_col] = df.eval(formula)
                save_data(df)
                st.success(f"已添加新列 {new_col}")
                st.rerun()
            except Exception as e:
                st.error(f"公式有误：{e}")

elif menu == "分析图表":
    st.header("指标趋势分析")
    dfp = df.copy()  # 这里是关键，确保dfp变量存在
    dfp['日期'] = pd.to_datetime(dfp['日期'], errors='coerce')
    dfp = dfp.dropna(subset=['日期'])
    metrics = [col for col in dfp.columns if col != '日期']  # <-- 在这里定义
    dfp = df.copy()
    dfp['日期'] = pd.to_datetime(dfp['日期'], errors='coerce')
    dfp = dfp.dropna(subset=['日期'])
    metrics = [col for col in dfp.columns if col != '日期']

    if dfp['日期'].notna().any():
        min_date = dfp['日期'].min().date()
        max_date = dfp['日期'].max().date()
    else:
        today = datetime.today().date()
        min_date = max_date = today
    left, right = st.columns([1, 3])
    with left:
        start = st.date_input("开始日期", min_value=min_date, max_value=max_date, value=min_date)
        end = st.date_input("结束日期", min_value=min_date, max_value=max_date, value=max_date)
        left_metrics = st.multiselect("左轴指标（虚线）", metrics, default=["回收率"])
        right_metrics = st.multiselect("右轴指标（实线）", metrics, default=["原矿吨数"])
        left_zero = st.checkbox("左轴从0开始", value=False)
        right_zero = st.checkbox("右轴从0开始", value=False)
    with right:
        dfsel = dfp[(dfp['日期'] >= pd.to_datetime(start)) & (dfp['日期'] <= pd.to_datetime(end))]
        if not dfsel.empty and (left_metrics or right_metrics):
            fig = go.Figure()
            color_list = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
            for idx, m in enumerate(left_metrics):
                fig.add_trace(go.Scatter(
                    x=dfsel['日期'], y=dfsel[m], mode='lines+markers',
                    name=f"左-{m}", yaxis='y1',
                    line=dict(dash='dash', color=color_list[idx % len(color_list)]),
                    marker=dict(symbol='circle'),
                    hovertemplate = f"日期: %{{x|%Y-%m-%d}}<br>{m}: %{{y:.4f}}<extra></extra>",
                ))
            for idx, m in enumerate(right_metrics):
                fig.add_trace(go.Scatter(
                    x=dfsel['日期'], y=dfsel[m], mode='lines+markers',
                    name=f"右-{m}", yaxis='y2',
                    line=dict(color=color_list[(idx + 5) % len(color_list)]),
                    marker=dict(symbol='x'),
                    hovertemplate = f"日期: %{{x|%Y-%m-%d}}<br>{m}: %{{y:.4f}}<extra></extra>",
                ))
            fig.update_layout(
                xaxis=dict(title='日期'),
                yaxis=dict(title='左轴', zeroline=left_zero, rangemode='tozero' if left_zero else 'normal'),
                yaxis2=dict(title='右轴', overlaying='y', side='right', zeroline=right_zero, rangemode='tozero' if right_zero else 'normal'),
                legend=dict(x=0.01, y=0.99), hovermode='x unified', margin=dict(l=20, r=20, t=20, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("请选择有效的日期范围和指标")
