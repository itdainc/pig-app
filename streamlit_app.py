import streamlit as st
import pandas as pd

st.set_page_config(page_title="도축 스펙 거래처 자동 배정", layout="wide", page_icon="🐖")

st.title("🐖 돼지 도축 스펙 거래처 자동 배정 시스템")
st.markdown("도축 등급판정 파일과 거래처 스팩 파일을 업로드하면 최적의 거래처를 자동으로 배정합니다.")

st.sidebar.header("📁 파일 업로드")
uploaded_grade = st.sidebar.file_uploader("1. 등급판정 결과 파일 (.xls/.xlsx)", type=["xls", "xlsx"])
uploaded_spec = st.sidebar.file_uploader("2. 거래처 스팩 파일 (.xlsx)", type=["xlsx"])

if uploaded_grade and uploaded_spec:
    try:
        df_g = pd.read_excel(uploaded_grade, header=3)
        pigs = pd.DataFrame({
            '도체번호': df_g.iloc[:, 4],
            '성별': df_g.iloc[:, 7],
            '중량': pd.to_numeric(df_g.iloc[:, 8], errors='coerce'),
            '등지방': pd.to_numeric(df_g.iloc[:, 9], errors='coerce'),
            '등급': df_g.iloc[:, 22]
        }).dropna(subset=['중량']).copy()

        df_s = pd.read_excel(uploaded_spec).dropna(subset=['Unnamed: 0'])
        specs = []
        for idx, row in df_s.iterrows():
            name = row['Unnamed: 0']
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

        total_pigs = len(pigs)
        assigned_pigs = len(pigs[pigs['배정거래처'] != '미배정'])
        unassigned_pigs = len(pigs[pigs['배정거래처'] == '미배정'])

        c1, c2, c3 = st.columns(3)
        c1.metric("총 도축 수량", f"{total_pigs} 두")
        c2.metric("거래처 배정 완료", f"{assigned_pigs} 두")
        c3.metric("미배정 수량", f"{unassigned_pigs} 두")

        st.subheader("📊 거래처별 배정 현황 요약")
        summary = pigs[pigs['배정거래처'] != '미배정'].groupby(['배정거래처', '성별']).size().unstack(fill_value=0)
        st.dataframe(summary, use_container_width=True)

        st.subheader("📋 전체 개체별 세부 배정 내역")
        st.dataframe(pigs, use_container_width=True)

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 [1. 등급판정 파일]과 [2. 거래처 스팩 파일]을 업로드해주세요.")
