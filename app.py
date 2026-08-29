import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="강릉샌드 생산일지", page_icon="🍪")
st.title("🍪 강릉샌드 쿠키 생산일지")

# ==========================================
# 1. 구글 시트 연결
# ==========================================
# 스트림릿 Secrets에서 GCP_JSON 키를 가져옴
try:
    gcp_json_str = st.secrets["GCP_JSON"]
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(gcp_json_str), scope)
    client = gspread.authorize(creds)
    # 🚨 구글 스프레드시트 파일 이름이 '강릉샌드 생산일지'가 맞는지 확인해!
    sheet = client.open('강릉샌드 생산일지').sheet1
except Exception as e:
    st.error("구글 시트 연결에 실패했어. 시크릿 키 설정을 확인해 줘!")
    st.stop()

# ==========================================
# 2. 직원 입력 화면
# ==========================================
st.subheader("📝 횟수 입력하기")

name = st.selectbox("직원 이름", ["정환", "소정", "가영"])
time_type = st.radio("입력 시간", ["오전 (점심 전)", "오후 (퇴근 전)"])

count = st.number_input("기계 횟수", min_value=0, step=1)

if time_type == "오후 (퇴근 전)":
    boxes = st.number_input("총 쿠키 통 수", min_value=0, step=1)
else:
    boxes = 0

if st.button("제출하기"):
    # 버튼 누르는 순간 한국 시간으로 날짜/시간 자동 생성!
    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    today_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # 구글 시트에 데이터 한 줄 쏘기
    sheet.append_row([today_date, current_time, name, time_type, count, boxes])
    st.success(f"✅ {name}님, {today_date} 입력 완료! (현재 횟수: {count})")

st.write("---")

# ==========================================
# 3. 실시간 랭킹보드 (오늘 날짜 기준)
# ==========================================
st.subheader("🏆 오늘의 쿠키왕 (실시간 횟수 랭킹)")

# 시트 전체 데이터 가져오기
records = sheet.get_all_records()
df = pd.DataFrame(records)

if not df.empty:
    # 오늘 날짜에 해당하는 데이터만 필터링
    tz = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    # '날짜' 열이 문자열로 저장되므로, 오늘 날짜와 일치하는 행만 추출
    today_df = df[df['날짜'].astype(str) == today_str]
    
    if not today_df.empty:
        # 이름별 최고 횟수 추출 및 정렬
        ranking = today_df.groupby("이름")["횟수"].max().reset_index()
        ranking = ranking.sort_values(by="횟수", ascending=False).reset_index(drop=True)
        ranking.index = ranking.index + 1
        
        st.dataframe(ranking, use_container_width=True)
        st.bar_chart(ranking.set_index("이름")["횟수"])
    else:
        st.info("오늘 입력된 데이터가 없어! 첫 번째 쿠키왕에 도전해 봐!")
else:
    st.info("아직 입력된 데이터가 없어!")
