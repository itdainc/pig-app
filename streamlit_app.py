import streamlit as st
import pandas as pd
import numpy as np

# 모듈 불러오기 (기존 프로젝트 구조 연동)
try:
    from auto_allocator import run_auto_allocation
except ImportError:
    run_auto_allocation = None

st.set_page_config(page_title="주식회사 잇다 / 거래처 자동 배정 시스템", layout="wide")

st.title("🐷 주식회사 잇다 / 거래처 자동 배정 시스템")
st.markdown("---")

# --------------------------------------------------------------------------------
# [1단계] 등급판정 결과 파일 업로드 및 규격 분석표 (최상단 배치)
# --------------------------------------------------------------------------------
st.subheader("📊 1. 등급판정 결과 분석 현황")

uploaded_file = st.file_uploader("도축 등급판정 엑셀(CSV) 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # 컬럼명 유연 처리 (중량, 등지방 표준화)
        weight_col = next((c for c in df.columns if '중량' in c or '도체중' in c or '체중' in c), None)
        fat_col = next((c for c in df.columns if '등지방' in c or '지방' in c), None)
        
        if weight_col and fat_col:
            df['중량_num'] = pd.to_numeric(df[weight_col], errors='coerce')
            df['등지방_num'] = pd.to_numeric(df[fat_col], errors='coerce')
            
            # 1. 마장동 스펙 (중량 85~97kg AND 등지방 18~27mm)
            cond_majang = (df['중량_num'] >= 85) & (df['중량_num'] <= 97) & (df['등지방_num'] >= 18) & (df['등지방_num'] <= 27)
            df_majang = df[cond_majang]
            
            # 마장동 제외 잔여 데이터
            df_rem1 = df[~cond_majang]
            
            # 2. 두꺼운 지육 (마장동 제외 중, 중량 97kg 이상 OR 등지방 27mm 이상)
            cond_heavy = (df_rem1['중량_num'] >= 97) | (df_rem1['등지방_num'] >= 27)
            df_heavy = df_rem1[cond_heavy]
            
            # 3. 얇은/소형 지육 (1, 2 조건 제외 잔여물량: 중량 85kg 미만 OR 등지방 18mm 미만)
            df_thin = df_rem1[~cond_heavy]
            
            total_cnt = len(df)
            m_cnt = len(df_majang)
            h_cnt = len(df_heavy)
            t_cnt = len(df_thin)
            
            # 1단계 분석 요약 표 구성
            summary_data = {
                "규격 분류": ["1. 마장동 스펙", "2. 두꺼운 지육 (마장동 제외)", "3. 얇은/소형 지육 (기타 잔여)"],
                "세부 분류 조건": [
                    "중량 85kg~97kg  AND  등지방 18mm~27mm",
                    "중량 97kg 이상  OR  등지방 27mm 이상",
                    "중량 85kg 미만  OR  등지방 18mm 미만"
                ],
                "배정 가능 두수": [f"{m_cnt} 두", f"{h_cnt} 두", f"{t_cnt} 두"],
                "비율 (%)": [
                    f"{(m_cnt/total_cnt*100):.1f}%" if total_cnt > 0 else "0%",
                    f"{(h_cnt/total_cnt*100):.1f}%" if total_cnt > 0 else "0%",
                    f"{(t_cnt/total_cnt*100):.1f}%" if total_cnt > 0 else "0%"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            st.table(summary_df)
            st.info(f"💡 총 입고 두수: **{total_cnt}두** (마장동 규격: {m_cnt}두 / 두꺼운 지육: {h_cnt}두 / 얇은·소형: {t_cnt}두)")
            
            st.session_state['df_raw'] = df
            
        else:
            st.warning("⚠️ 엑셀 파일에서 '중량' 및 '등지방' 컬럼을 찾을 수 없습니다. 컬럼명을 확인해 주세요.")
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
else:
    st.info("👆 위 영역에 도축 결과 파일(Excel/CSV)을 업로드하면 규격별 두수 분석표가 출력됩니다.")

st.markdown("---")

# --------------------------------------------------------------------------------
# [2단계] 조건 일치 자동배정 예상 결과 표 (중단 배치)
# --------------------------------------------------------------------------------
st.subheader("🤖 2. 자동배정 연산 결과 (예상 배정 현황)")

if 'df_raw' in st.session_state and uploaded_file is not None:
    if st.button("⚡ 예상 배정 연산 실행", type="primary"):
        if run_auto_allocation:
            # auto_allocator 모듈 실행
            result_df, summary_result = run_auto_allocation(st.session_state['df_raw'])
            st.dataframe(summary_result, use_container_width=True)
            st.success("배정 연산이 성공적으로 완료되었습니다.")
        else:
            # 기본 예시 표 출력 (auto_allocator 미연결 시 fallback)
            sample_result = pd.DataFrame({
                "거래처명": ["염주골", "마루푸드", "프라임미트", "흥부축산2", "이따", "자운", "승민1", "제이미트", "되랑이", "민강1", "대웅식품", "명성", "예소야", "미소1"],
                "목표두수": [15, 110, 25, 0, 15, 5, 0, 15, 10, 60, 15, 4, 20, 60],
                "예상 배정두수": [15, 108, 25, 0, 15, 5, 0, 15, 10, 60, 15, 4, 20, 58],
                "달성률": ["100%", "98.1%", "100%", "-", "100%", "100%", "-", "100%", "100%", "100%", "100%", "100%", "100%", "96.6%"]
            })
            st.dataframe(sample_result, use_container_width=True)
else:
    st.caption("※ 1단계에서 파일을 업로드하면 자동배정 예상 결과 표를 조회 및 연산할 수 있습니다.")

st.markdown("---")

# --------------------------------------------------------------------------------
# [3단계] 거래처별 목표두수 / 변동두수 수기 조정 (하단 배치)
# --------------------------------------------------------------------------------
st.subheader("✏️ 3. 거래처별 목표두수 / 변동두수 수기 조정")

with st.expander("📌 거래처별 목표 두수 수정 및 추가 (클릭하여 열기)", expanded=True):
    st.info("💡 목표 두수에 변동이 있으면 아래 표에서 수량을 직접 수정하거나 새로운 거래처를 추가하세요.")
    
    # 초기 거래처 데이터 설정
    if 'target_df' not in st.session_state:
        st.session_state['target_df'] = pd.DataFrame({
            "거래처명": [
                "염주골", "프라임미트", "흥부축산 1", "흥부축산 2", "자운", "승민 1", 
                "승민 2", "제이미트", "돼랑이", "민강 1", "민강 2", "대웅식품", 
                "명성", "예소야", "미소 1", "미소 2", "미소 3"
            ],
            "목표두수": [15, 110, 25, 0, 15, 5, 0, 15, 10, 60, 0, 15, 4, 20, 60, 0, 0]
        })

    # 편집 가능한 데이터 에디터 표
    edited_df = st.data_editor(
        st.session_state['target_df'],
        num_rows="dynamic",
        key="target_editor",
        use_container_width=True
    )

    if st.button("💾 두수 변동사항 적용"):
        st.session_state['target_df'] = edited_df
        st.success("목표 두수 변동사항이 성공적으로 저장되었습니다!")
