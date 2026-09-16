import pandas as pd

def run_first_allocation(file, target_df, allocate_func=None):
    """
    1차 배정(스펙일치) 연산을 수행하는 별도 분리 모듈
    """
    if file is None:
        return None, None, None

    file.seek(0)
    
    # 외부 allocate_pigs_data 함수가 전달되었을 경우 실행
    if allocate_func:
        pigs, specs_dict = allocate_func(file, target_df)
    else:
        # 모듈이 없을 경우 기본 빈 데이터프레임 반환
        return pd.DataFrame(), {}, pd.DataFrame()

    # 요약 표 생성 (목표두수 vs 1차 예상 배정두수 vs 달성률)
    target_curr = target_df.copy()
    allocated_counts = pigs.groupby('배정거래처').size().reset_index(name='예상 배정두수')
    
    summary_alloc = pd.merge(target_curr, allocated_counts, left_on='거래처명', right_on='배정거래처', how='left')
    summary_alloc['예상 배정두수'] = summary_alloc['예상 배정두수'].fillna(0).astype(int)
    summary_alloc['목표두수'] = pd.to_numeric(summary_alloc['목표두수'], errors='coerce').fillna(0).astype(int)
    
    summary_alloc['달성률'] = summary_alloc.apply(
        lambda r: f"{(r['예상 배정두수']/r['목표두수']*100):.1f}%" if r['목표두수'] > 0 else "-", axis=1
    )
    
    display_summary = summary_alloc[['거래처명', '목표두수', '예상 배정두수', '달성률']]
    
    return pigs, specs_dict, display_summary
