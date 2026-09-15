import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="도축 스펙 거래처 자동 배정", layout="wide", page_icon="🐖")

st.title("🐖 돼지 도축 스펙 거래처 자동 배정 시스템")

# ----------------- 기본 거래처 데이터 초기화 -----------------
default_specs = [
    {"업체명": "대용식품", "중량(kg)": "85~90", "등지방(mm)": "18~21", "등급": "1,1+", "거세": 6, "암": 4},
    {"업체명": "민강", "중량(kg)": "85~97", "등지방(mm)": "21~25", "등급": "1,1+", "거세": 5, "암": 5},
    {"업체명": "예소야", "중량(kg)": "85~97", "등지방(mm)": "22~25", "등급": "1,1+", "거세": 6, "암": 4},
    {"업체명": "승민", "중량(kg)": "84~88", "등지방(mm)": "20", "등급": "1,1+", "거세": 0, "암": 10},
    {"업체명": "자운", "중량(kg)": "85~95", "등지방(mm)": "22~25", "등급": "1,1+", "거세": 0, "암": 10},
    {"업체명": "제이이", "중량(kg)": "88~97", "등지방(mm)": "25~27", "등급": "1,1+", "거세": 5, "암": 5},
    {"업체명": "돼랑이", "중량(kg)": "85~90", "등지방(mm)": "25~26", "등급": "1,1+", "거세": 5, "암": 5},
    {"업체명": "명성", "중량(kg)": "87~97", "등지방(mm)": "20~22", "등급": "1,1+", "거세": 8, "암": 2},
    {"업체명": "염주골", "중량(kg)": "98~109", "등지방(mm)": "20~27", "등급": "2", "거세": 5, "암": 5},
    {"업체명": "흥부축산", "중량(kg)": "75~86", "등지방(mm)": "18~22", "등급": "1,1+,2", "거세": 6, "암": 4},
    {"업체명": "미소", "중량(kg)": "80~97", "등지방(mm)": "17~25", "등급": "1,1+", "거세": 6, "암": 4},
    {"업체명": "프라임미트", "중량(kg)": "80~103", "등지방(mm)": "20~34", "등급": "1,1+,2", "거세": 7, "암": 3},
]

if 'spec_df' not in st.session_state:
    st.session_state.spec_df = pd.DataFrame(default_specs)

# ----------------- 탭(카테고리) 구성 -----------------
tab1, tab2 = st.tabs(["🚀 자동 배정 실행", "⚙️ 거래처 스펙 관리"])

# ----------------- 탭 1: 자동 배정 -----------------
with tab1:
    st.sidebar.header("📁 파일 업로드")
    uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])

    if uploaded_grade:
        try:
            df_g = pd.read_excel(uploaded_grade, header=3)
            pigs = pd.DataFrame({
                '도체번호': df_g.iloc[:, 4],
                '성별': df_g.iloc[:, 7],
                '중량': pd.to_numeric(df_g.iloc[:, 8], errors='coerce'),
                '등지방': pd.to_numeric(df_g.iloc[:, 9], errors='coerce'),
                '등급': df_g.iloc[:, 22]
            }).dropna(subset=['중량']).copy()

            pigs.reset_index(drop=True, inplace=True)
            pigs.index = pigs.index + 1

            # 저장된 스펙 파싱
            specs = []
            for idx, row in st.session_state.spec_df.iterrows():
                name = str(row['업체명'])
                weight_str = str(row['중량(kg)'])
                fat_str = str(row['등지방(mm)'])
                grade_str = str(row['등급'])

                w_min, w_max = (map(float, weight_str.split('~')) if '~' in weight_str 
                                else (float(weight_str), float(weight_str)) if weight_str!='nan' else (0, 999))
                f_min, f_max = (map(float, fat_str.split('~')) if '~' in fat_str 
                                else (float(fat_str), float(fat_str)) if fat_str!='nan' else (0, 999))
                grades = [g.strip() for g in grade_str.split(',')] if grade_str != 'nan' else []

                c_cnt = int(row['거세']) if pd.notna(row['거세']) else 0
                f_cnt = int(row['암']) if pd.notna(row['암']) else 0

                specs.append({
                    '업체명': name, 'w_min': w_min, 'w_max': w_max,
                    'f_min': f_min, 'f_max': f_max, 'grades': grades,
                    '거세수량': c_cnt, '암수량': f_cnt
                })

            pigs['배정거래처'] = '미배정'
            for spec in specs:
                company = spec['업체명']
                for sex, req_cnt in [('거세', spec['거세수량']), ('암', spec['암수량'])]:
                    if req_cnt <= 0:
                        continue
                    cond = (
                        (pigs['배정거래처'] == '미배정') &
                        (pigs['성별'] == sex) &
                        (pigs['중량'] >= spec['w_min']) & (pigs['중량'] <= spec['w_max']) &
                        (pigs['등지방'] >= spec['f_min']) & (pigs['등지방'] <= spec['f_max'])
                    )
                    if spec['grades']:
                        cond &= (pigs['등급'].isin(spec['grades']))
                    matched = pigs[cond].head(req_cnt)
                    pigs.loc[matched.index, '배정거래처'] = company

            # 사이드바 요약 표
            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 거래처별 배정 요약")
            summary = pigs[pigs['배정거래처'] != '미배정'].groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
            st.sidebar.dataframe(summary, use_container_width=True, height=500)

            # 상단 메인 지표
            total_pigs = len(pigs)
            assigned_pigs = len(pigs[pigs['배정거래처'] != '미배정'])
            unassigned_pigs = len(pigs[pigs['배정거래처'] == '미배정'])

            c1, c2, c3 = st.columns(3)
            c1.metric("총 도축 수량", f"{total_pigs} 두")
            c2.metric("거래처 배정 완료", f"{assigned_pigs} 두")
            c3.metric("미배정 수량", f"{unassigned_pigs} 두")

            st.markdown("---")
            
            col_main, col_empty = st.columns([3, 1])
            with col_main:
                st.subheader("📋 전체 개체별 세부 배정 내역")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    pigs.to_excel(writer, sheet_name='배정내역')
                    summary.to_excel(writer, sheet_name='요약')
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 배정 결과 엑셀 다운로드",
                    data=processed_data,
                    file_name="돼지_도축_자동배정결과.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.dataframe(pigs, height=900, use_container_width=True)

        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
    else:
        st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]만 올려주시면 바로 배정됩니다.")

# ----------------- 탭 2: 거래처 스펙 관리 -----------------
with tab2:
    st.subheader("⚙️ 등록된 거래처 스펙 수정 및 추가")
    st.write("표 안의 셀을 클릭하여 직접 숫자를 수정하거나, 아래에서 항목을 추가/삭제할 수 있습니다.")

    # 표 직접 수정 기능
    edited_df = st.data_editor(
        st.session_state.spec_df,
        num_rows="dynamic",
        use_container_width=True,
        key="spec_editor"
    )

    if st.button("💾 스펙 변경사항 저장"):
        st.session_state.spec_df = edited_df
        st.success("거래처 스펙 변경 사항이 저장되었습니다!")
