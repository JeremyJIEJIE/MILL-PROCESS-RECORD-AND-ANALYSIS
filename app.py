import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io
import os # 新增：用于文件路径操作

# --- 添加 Matplotlib 中文字体支持 ---
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS'] # SimHei 是 Windows 常见的中文字体，Arial Unicode MS 跨平台
plt.rcParams['axes.unicode_minus'] = False # 解决负号 '-' 显示为方块的问题
# --- End of Matplotlib config ---

# --- 1. 页面配置与美化 ---
st.set_page_config(
    page_title="选矿数据管理系统",
    page_icon="⛏️", # 可以选择一个相关的 emoji
    layout="wide", # 页面布局，可选 "centered" 或 "wide"
    initial_sidebar_state="expanded" # 侧边栏初始状态
)

# 确保 data.csv 存在且包含列名
# 检查当前运行目录，并在该目录创建 data.csv
data_file_path = "data.csv"
expected_columns = [
    '日期', '原矿吨数', '原矿金品位', '尾液品位', '尾固品位',
    '尾液含金', '尾固含金', '溢流浓度', '溢流细度', '停机时间',
    '尾矿品位', '回收率', '回收金属量'
]

if not os.path.exists(data_file_path):
    # 如果文件不存在，创建一个只包含列名的空 CSV
    initial_df = pd.DataFrame(columns=expected_columns)
    initial_df.to_csv(data_file_path, index=False)
    st.info(f"在 '{os.getcwd()}' 目录下创建了空的 data.csv 文件。")

# 加载数据（缓存处理）
@st.cache_data
def load_data():
    df = pd.read_csv(data_file_path, parse_dates=['日期'])
    # 确保所有预期的列都存在，如果data.csv是空的，pandas可能不会自动创建所有列
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None # 或 pd.NA
    return df

# 保存数据函数
def save_data(df_to_save):
    # 确保保存前所有日期列都是正确的格式
    df_to_save['日期'] = pd.to_datetime(df_to_save['日期'], errors='coerce')
    df_to_save.to_csv(data_file_path, index=False)
    st.session_state.data_updated = True # 设置一个状态变量，用于 reru n 后的消息显示
    st.cache_data.clear()
    st.rerun()

# 派生数据计算 (保持不变，但增加美化提示)
def derive_data(df):
    df = df.copy()
    numeric_cols = ['原矿吨数', '原矿金品位', '尾液含金', '尾固含金', '溢流浓度', '溢流细度', '停机时间'] # 包含所有可能为数字的列
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_calculated = df.dropna(subset=['原矿吨数', '原矿金品位', '尾液含金', '尾固含金'])

    df_calculated['尾矿品位'] = df_calculated['尾液含金'] + df_calculated['尾固含金']
    df_calculated['回收率'] = (df_calculated['原矿金品位'] - df_calculated['尾矿品位']) / df_calculated['原矿金品位']
    df_calculated['回收率'] = df_calculated['回收率'].clip(lower=0, upper=1)
    df_calculated['回收金属量'] = df_calculated['原矿吨数'] * df_calculated['原矿金品位'] * df_calculated['回收率']

    df.update(df_calculated)
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    return df

# --- 主界面菜单 ---
st.sidebar.title("💎 选矿数据管理系统")
st.sidebar.markdown("---") # 侧边栏分隔线
menu = st.sidebar.selectbox("功能选择", ["📝 输入数据", "📊 查看数据", "📈 分析图表"])
st.sidebar.markdown("---")
st.sidebar.info("✨ 欢迎使用！")

# 初始化 session state 用于保存后的消息显示
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False

df = load_data() # 加载现有数据

# --- 界面 1：输入数据 ---
if menu == "📝 输入数据":
    st.header("✨ 数据录入与导入")
    st.markdown("在这里您可以手动输入单条数据，或从文件批量导入数据。")

    # ----- 文件上传部分 -----
    st.subheader("📁 方式一：从文件导入数据")
    uploaded_file = st.file_uploader("请上传 CSV 或 Excel 文件 (包含 '日期' 列和所有预期列)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                new_data_from_file = pd.read_csv(uploaded_file, parse_dates=['日期'])
            elif uploaded_file.name.endswith('.xlsx'):
                new_data_from_file = pd.read_excel(uploaded_file, parse_dates=['日期'])
            else:
                st.error("❌ 不支持的文件格式。请上传 CSV 或 Excel 文件。")
                new_data_from_file = pd.DataFrame()

            if not new_data_from_file.empty:
                st.success(f"✅ 文件 '{uploaded_file.name}' 上传成功！预览数据：")
                st.dataframe(new_data_from_file.head())

                if st.button("➕ 将导入数据添加到现有数据并保存"):
                    # 确保导入数据的列与现有数据的列匹配
                    # 添加缺失的列，并确保顺序一致
                    for col in expected_columns:
                        if col not in new_data_from_file.columns:
                            new_data_from_file[col] = None # 添加缺失列

                    # 确保列的顺序一致
                    new_data_from_file = new_data_from_file[expected_columns]

                    combined_df = pd.concat([df, new_data_from_file], ignore_index=True)
                    combined_df = derive_data(combined_df) # 重新计算派生数据
                    save_data(combined_df) # 使用统一的保存函数
                    st.success("🎉 数据已成功从文件导入并保存！")
            else:
                st.warning("⚠️ 上传的文件为空或无法解析。")

        except Exception as e:
            st.error(f"发生错误：{e}")
            st.info("💡 提示：请确保文件格式正确且包含 '日期' 列，并且列名与预期一致。")

    st.markdown("---")

    # ----- 手动输入部分 -----
    st.subheader("✍️ 方式二：手动输入单条数据")
    with st.form("data_entry_form"):
        col1, col2, col3 = st.columns(3) # 使用列布局
        with col1:
            date = st.date_input("🗓️ 日期", datetime.today())
            ore = st.number_input("⛰️ 原矿吨数", min_value=0.0, format="%.2f", key="ore_input")
            grade = st.number_input("🧪 原矿金品位 (g/t)", min_value=0.0, format="%.4f", key="grade_input")
        with col2:
            tailing_solu_grade = st.number_input("💧 尾液品位 (g/t)", min_value=0.0, format="%.4f", key="tsg_input")
            tailing_solid_grade = st.number_input("🧱 尾固品位 (g/t)", min_value=0.0, format="%.4f", key="tssg_input")
            tailing_solu_weight = st.number_input("💧 尾液含金 (g)", min_value=0.0, format="%.4f", help="通常指尾液中的金含量", key="tsw_input")
        with col3:
            tailing_solid_weight = st.number_input("🧱 尾固含金 (g)", min_value=0.0, format="%.4f", help="通常指尾固中的金含量", key="tshw_input")
            cof_concentration = st.number_input("💧 溢流浓度 (%)", min_value=0.0, max_value=100.0, format="%.2f", key="cc_input")
            cof_grinding = st.number_input("📏 溢流细度 (%)", min_value=0.0, max_value=100.0, format="%.2f", key="cg_input")
            shutdown_time = st.number_input("⏳ 停机时间 (min)", min_value=0.0, format="%.0f", key="st_input")

        submitted = st.form_submit_button("💾 保存新数据")
        if submitted:
            # 检查是否有必填项为空
            if not all([ore, grade, tailing_solu_grade, tailing_solid_grade, tailing_solu_weight, tailing_solid_weight, cof_concentration, cof_grinding, shutdown_time]):
                st.warning("⚠️ 请填写所有数据项！")
            else:
                new_row = pd.DataFrame([{
                    "日期": pd.to_datetime(date),
                    "原矿吨数": ore,
                    "原矿金品位": grade,
                    "尾液品位": tailing_solu_grade,
                    "尾固品位": tailing_solid_grade,
                    "尾液含金": tailing_solu_weight,
                    "尾固含金": tailing_solid_weight,
                    "溢流浓度": cof_concentration,
                    "溢流细度": cof_grinding,
                    "停机时间": shutdown_time,
                    "尾矿品位": None, # 这些会在derive_data中计算
                    "回收率": None,
                    "回收金属量": None
                }])
                combined_df = pd.concat([df, new_row], ignore_index=True)
                combined_df = derive_data(combined_df)
                save_data(combined_df)
                st.success("✅ 单条数据已保存！")

    # 显示保存成功消息（在 reru n 后）
    if st.session_state.data_updated:
        st.success("数据已更新！")
        st.session_state.data_updated = False # 用完后重置状态

# --- 界面 2：查看数据 ---
elif menu == "📊 查看数据":
    st.header("🔍 所有选矿数据")
    st.markdown("您可以浏览、编辑或删除数据。")

    df = derive_data(df) # 确保查看时也计算派生数据

    if not df.empty:
        # ---- 数据编辑与删除 ----
        st.subheader("数据管理")
        edited_df = st.data_editor(
            df,
            key="data_editor",
            num_rows="dynamic", # 允许用户添加新行
            hide_index=True,
            column_config={
                "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
                # 可以为其他列添加配置，例如数字格式化等
            }
        )

        # 检查是否有行被删除或修改
        if not edited_df.equals(df):
            # 将编辑后的数据保存
            save_data(edited_df)
            st.success("数据已更新！") # 重新加载后会显示此消息

        # 删除选定行按钮
        # Streamlit 1.25+ 支持 st.dataframe 的 selection_mode
        # 为了兼容性，这里使用一个更直接的删除方法，通过索引来删除
        st.markdown("---")
        st.subheader("删除数据行")
        st.info("💡 请在上方表格中选择要删除的行，然后点击删除按钮。")
        rows_to_delete_indices = st.session_state.data_editor["added_rows"] # 用于动态行，这里可能需要手动选择
        # 更标准的删除方式是让用户选择行
        # st.dataframe (或 st.data_editor) 返回的 Dataframe 会有一个 selection 属性
        # 但 data_editor 的行为更复杂，它返回的是一个可编辑的 DataFrame。
        # 最简单的方法是让用户在 data_editor 中删除行（通过 num_rows="dynamic" 提供的叉号图标），
        # 或者提供一个单独的删除机制。
        # 考虑到 data_editor 的 "num_rows='dynamic'" 已经允许用户删除行，这里可以简化。

        # 如果需要提供一个单独的“删除选中行”按钮，并且用户选择的是原始的 st.dataframe:
        # selected_indices = st.dataframe(df, selection_mode="multi-row").selection.index
        # if st.button("删除选定行") and selected_indices:
        #     df_filtered = df.drop(selected_indices).reset_index(drop=True)
        #     save_data(df_filtered)
        #     st.success(f"已删除 {len(selected_indices)} 行数据。")
        #     st.rerun()

    else:
        st.info("📈 暂无数据可显示。请前往'输入数据'页面添加数据。")

# --- 界面 3：分析图表 ---
elif menu == "📈 分析图表":
    st.header("📊 指标趋势分析")
    st.markdown("选择一个或多个指标来查看它们的历史趋势。")

    df = derive_data(df)

    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df.dropna(subset=['日期']).sort_values(by='日期')

        if not df.empty:
            min_date = df['日期'].min().date()
            max_date = df['日期'].max().date()

            col_date_start, col_date_end = st.columns(2)
            with col_date_start:
                start = st.date_input("🗓️ 开始日期", min_date, min_value=min_date, max_value=max_date)
            with col_date_end:
                end = st.date_input("🗓️ 结束日期", max_date, min_value=min_date, max_value=max_date)

            selected_df = df[(df['日期'] >= pd.to_datetime(start)) & (df['日期'] <= pd.to_datetime(end))]

            if not selected_df.empty:
                available_metrics = [
                    "原矿吨数", "原矿金品位", "尾液品位", "尾固品位", "尾液含金", "尾固含金",
                    "溢流浓度", "溢流细度", "停机时间", "尾矿品位", "回收率", "回收金属量"
                ]
                selected_metrics = st.multiselect("📈 选择一个或多个指标", available_metrics, default=["原矿吨数", "回收率"])

                if selected_metrics:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    for metric in selected_metrics:
                        ax.plot(selected_df['日期'], selected_df[metric], marker='o', linestyle='-', label=metric)

                    # --- 改进点：动态图表标题和更明确的Y轴标签 ---
                    if len(selected_metrics) == 1:
                        # 单个指标时，标题更具体
                        ax.set_title(f"{selected_metrics[0]} 趋势图", fontsize=16)
                        # Y轴标签直接使用指标名称
                        ax.set_ylabel(selected_metrics[0], fontsize=12)
                    else:
                        # 多个指标时，使用通用标题，Y轴标签说明是“值”
                        ax.set_title("📈 选定指标趋势对比图", fontsize=16)
                        ax.set_ylabel("数值", fontsize=12) # 或者可以根据常见单位做映射，这里先用通用“数值”

                    ax.set_xlabel("日期", fontsize=12) # X轴标签保持不变

                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend(loc='best', fontsize=10)
                    plt.xticks(rotation=45, ha='right', fontsize=10)
                    plt.yticks(fontsize=10)
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning("请至少选择一个指标进行分析。")
            else:
                st.warning("所选日期范围内无数据。请调整日期范围或添加数据。")
        else:
            st.warning("暂无有效日期数据用于分析。请先录入数据。")
    else:
        st.info("📊 暂无数据可分析。请前往'输入数据'页面添加数据。")
