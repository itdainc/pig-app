import streamlit as st
import pandas as pd
import io
from datetime import datetime

# ----------------- 외부 및 분리 모듈 불러오기 -----------------
try:
    from auth import check_password
except ImportError:
    def check_password(): return True

try:
    from company_conditions import (
        get_company_conditions_df,
        get_company_conditions_excel_bytes,
        run_100pct_strict_allocation
    )
except ImportError:
    def get_company_conditions_df(): return pd.DataFrame()
    def get_company_conditions_excel_bytes(): return b''
    def run_100pct_strict_allocation(df): 
        df['배정거래처'] = '미분류'
        return df, pd.DataFrame(), pd.DataFrame()

# ----------------- 엑셀 위치 지정 로더 (7행부터 데이터 시작, I=8, J=9, L~U=11~20, W=22) -----------------
def load_excel_by_coords(file):
    file.seek(0)
    df = pd.read_excel(file, skiprows=6, header=None)
    
    df['w_num'] = pd.to_numeric(df.iloc[:, 8], errors='coerce')
    df['f_num'] = pd.to_numeric(df.iloc[:, 9], errors='coerce')
    df['grade_str'] = df.iloc[:, 22].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    
    def check_no_defect(row_slice):
        for val in row_slice:
            if pd.notna(val):
                s = str(val).strip()
                if s and s.lower() not in ['nan', 'none']:
                    return False
        return True

    df['no_defect'] = df.iloc[:, 11:21].apply(check_no_defect, axis=1)
    df['배정거래처'] = '미분류'
    
    w_col_name = "I열(중량)"
    f_col_name = "J열(등지방)"
    
    return df, w_col_name, f_col_name

# 로그인 검증
if check_password():

    st.set_page_config(page_title="주식회사 잇다 / 자동 배정 및 농가 분석 시스템", layout="wide", page_icon="🐖")

    if 'main_menu' not in st.session_state:
        st.session_state.main_menu = "배정"

    # 📌 메인 메뉴 (2개 고정)
    st.sidebar.title("📌 메인 메뉴")

    if st.sidebar.button("🏢 1. 거래처 자동 배정 시스템", type="primary" if st.session_state.main_menu == "배정" else "secondary", use_container_width=True):
        st.session_state.main_menu = "배정"
        st.rerun()

    if st.sidebar.button("📊 2. 농가 분석", type="primary" if st.session_state.main_menu == "농가분석" else "secondary", use_container_width=True):
        st.session_state.main_menu = "농가분석"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("📁 파일 업로드")
    uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])

    if st.sidebar.button("🔒 로그아웃", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

    def get_centered_column_config(df):
        config = {}
        for col in df.columns:
            if col in ["우선순위", "목표두수"]:
                config[col] = st.column_config.Column(col, alignment="center", width="small")
            elif col == "비고":
                config[col] = st.column_config.Column(col, alignment="center", width="large")
            elif col in ["출하농가", "이력번호"]:
                config[col] = st.column_config.Column(col, alignment="center", width="medium")
            else:
                config[col] = st.column_config.Column(col, alignment="center")
        return config

    # ==============================================================================
    # [메뉴 1] 거래처 자동 배정 시스템
    # ==============================================================================
    if st.session_state.main_menu == "배정":
        st.title("🐖 주식회사 잇다 / 거래처 자동 배정 시스템")

        # 3개 탭 구성
        tab1, tab2, tab3 = st.tabs([
            "🚀 자동 배정 실행", 
            "🏢 거래처별 배정 상세", 
            "🚚 잇다 배정"
        ])

        # ----------------- 탭 1: 자동 배정 실행 -----------------
        with tab1:
            st.subheader("🚀 자동 배정 연산 및 분석")
            
            # -------------------------------------------------------------------------
            # 1. 등급판정 결과 분석 표
            # -------------------------------------------------------------------------
            st.markdown("### 📊 1. 등급판정 결과 데이터 규격 분석")
            
            if uploaded_grade:
                try:
                    df_raw, w_col_name, f_col_name = load_excel_by_coords(uploaded_grade)
                    df_valid = df_raw.dropna(subset=['w_num', 'f_num'])
                    
                    # 1차 배정 백그라운드 연산 (다른 탭 연동용)
                    pigs, unallocated_df, _ = run_100pct_strict_allocation(df_valid)
                    st.session_state['allocated_pigs'] = pigs
                    
                    cond1 = (
                        (df_valid['w_num'] >= 85) & (df_valid['w_num'] <= 97) & 
                        (df_valid['f_num'] >= 18) & (df_valid['f_num'] <= 27) & 
                        (df_valid['grade_str'].isin(['1', '1+'])) &
                        (df_valid['no_defect'])
                    )
                    df_cond1 = df_valid[cond1]
                    df_rem1 = df_valid[~cond1]
                    
                    cond2 = (df_rem1['w_num'] >= 97) | (df_rem1['f_num'] >= 27)
                    df_cond2 = df_rem1[cond2]
                    df_rem2 = df_rem1[~cond2]
                    
                    cond3 = (df_rem2['w_num'] < 85) | (df_rem2['f_num'] < 18)
                    df_cond3 = df_rem2[cond3]
                    df_cond4 = df_rem2[~cond3]
                    
                    tot_cnt = len(df_valid)
                    c1_cnt = len(df_cond1)
                    c2_cnt = len(df_cond2)
                    c3_cnt = len(df_cond3)
                    c4_cnt = len(df_cond4)
                    
                    analysis_table = pd.DataFrame({
                        "구분": [
                            "1. 마장동 스펙 규격", 
                            "2. 두꺼운 지육 (마장동 제외)", 
                            "3. 얇은/소형 지육 (잔여 물량)",
                            "4. 그외"
                        ],
                        "분류 상세 조건": [
                            r"중량 85 \~ 97kg, 등지방 18 \~ 27mm, 등급 1 / 1+, 하자없음",
                            r"중량 97kg 이상 이거나 등지방 27mm 이상",
                            r"중량 85kg 미만 이거나 등지방 18mm 미만",
                            r"1 \~ 3번 조건 미포함"
                        ],
                        "배정가능 두수": [f"{c1_cnt:,} 두", f"{c2_cnt:,} 두", f"{c3_cnt:,} 두", f"{c4_cnt:,} 두"],
                        "비율 (%)": [
                            f"{(c1_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c2_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c3_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%",
                            f"{(c4_cnt/tot_cnt*100):.1f}%" if tot_cnt > 0 else "0%"
                        ]
                    })
                    
                    st.table(analysis_table)
                    st.info(f"💡 **총 입고두수:** {tot_cnt:,}두 (마장동 스펙 지육: {c1_cnt:,}두 / 두꺼운 지육: {c2_cnt:,}두 / 얇은·소형: {c3_cnt:,}두 / 그외: {c4_cnt:,}두)")
                except Exception as e:
                    st.error(f"등급판정 파일 분석 중 오류 발생: {e}")
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드하시면 규격별 수량 분석표가 표시됩니다.")

        # ----------------- 탭 2: 거래처별 배정 상세 -----------------
        with tab2:
            st.subheader("🏢 거래처별 개별 배정 내역 및 명단")
            if 'allocated_pigs' in st.session_state and '배정거래처' in st.session_state['allocated_pigs'].columns:
                pigs_all = st.session_state['allocated_pigs']
                all_assigned = [c for c in pigs_all['배정거래처'].unique() if "미분류" not in c]
                
                if all_assigned:
                    selected_company = st.selectbox("👉 조회할 거래처를 선택하세요:", sorted(all_assigned))
                    st.markdown(f"### **[{selected_company}] 배정 명단**")
                    comp_df = pigs_all[pigs_all['배정거래처'] == selected_company].copy()
                    st.dataframe(comp_df, use_container_width=True)
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

        # ----------------- 탭 3: 잇다 배정 -----------------
        with tab3:
            st.subheader("🚚 잇다 배정 내역")
            if 'allocated_pigs' in st.session_state and '배정거래처' in st.session_state['allocated_pigs'].columns:
                pigs_all = st.session_state['allocated_pigs']
                st.dataframe(pigs_all[pigs_all['배정거래처'] == '미분류'], use_container_width=True)
            else:
                st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")

    # ==============================================================================
    # [메뉴 2] 농가 분석
    # ==============================================================================
    elif st.session_state.main_menu == "농가분석":
        st.title("📊 농가별 출하 및 스펙 분석")
        st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]을 업로드해 주세요.")
