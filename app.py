import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="강릉샌드 생산일지", page_icon="🍪")
st.title("🍪 강릉샌드 쿠키 생산일지")

# 임시 저장소 (나중에 구글 시트 코드(gspread)로 바꿔치기 하면 됨!)
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=["시간", "이름", "구분", "횟수", "쿠키통"])

# ==========================================
# 1. 직원 입력 화면
# ==========================================
st.subheader("📝 횟수 입력하기")

name = st.selectbox("직원 이름", ["정환", "소정", "가영"])
time_type = st.radio("입력 시간", ["오전 (점심 전)", "오후 (퇴근 전)"])

count = st.number_input("기계 횟수", min_value=0, step=1)

# 오후(퇴근 전)를 선택했을 때만 쿠키 통 수 입력칸이 짠! 하고 나타남
if time_type == "오후 (퇴근 전)":
    boxes = st.number_input("총 쿠키 통 수", min_value=0, step=1)
else:
    boxes = 0  # 오전에는 0으로 자동 처리

if st.button("제출하기"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 새 데이터 추가
    new_data = pd.DataFrame([{"시간": now, "이름": name, "구분": time_type, "횟수": count, "쿠키통": boxes}])
    st.session_state.logs = pd.concat([st.session_state.logs, new_data], ignore_index=True)
    
    st.success(f"✅ {name}님, 입력 완료! (현재 횟수: {count})")

st.write("---")

# ==========================================
# 2. 동기부여 팍팍! 실시간 랭킹보드
# ==========================================
st.subheader("🏆 오늘의 쿠키왕 (실시간 횟수 랭킹)")

if not st.session_state.logs.empty:
    # 이름별로 가장 높은 횟수(최종 횟수)를 찾아내서 순위 매기기
    ranking = st.session_state.logs.groupby("이름")["횟수"].max().reset_index()
    ranking = ranking.sort_values(by="횟수", ascending=False).reset_index(drop=True)
    ranking.index = ranking.index + 1  # 순위를 1등부터 시작하게 맞춤
    
    # 1. 깔끔한 표로 보여주기
    st.dataframe(ranking, use_container_width=True)
    
    # 2. 한눈에 들어오는 막대그래프 띄우기
    st.bar_chart(ranking.set_index("이름")["횟수"])
else:
    st.info("아직 오늘 입력된 데이터가 없어! 첫 번째 쿠키왕에 도전해 봐!")
