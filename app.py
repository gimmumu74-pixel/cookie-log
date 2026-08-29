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
try:
    gcp_json_str = st.secrets["GCP_JSON"]
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(gcp_json_str), scope)
    client = gspread.authorize(creds)
    # 전체 워크스페이스를 불러옴
    spreadsheet = client.open('강릉샌드 생산일지')
except Exception as e:
    st.error(f"구글 시트 연결 에러 원인: {e}")
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
    tz = pytz.timezone('Asia/Seoul')
    today_date = datetime.now(tz).strftime("%Y-%m-%d")

    try:
        # 선택한 직원 이름과 똑같은 구글 시트 탭을 찾음
        user_sheet = spreadsheet.worksheet(name)
        # 시간 빼고 날짜, 이름, 구분, 횟수, 쿠키통만 저장!
        user_sheet.append_row([today_date, name, time_type, count, boxes])
        st.success(f"✅ {name}님, 개인 탭에 {today_date} 기록 완료! (현재 횟수: {count})")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"🚨 구글 시트 맨 아래에 '{name}' 탭이 안 보여! 탭 이름을 정확히 만들어줘.")

st.write("---")

# ==========================================
# 3. 실시간 랭킹보드 (오늘 날짜 기준)
# ==========================================
st.subheader("🏆 오늘의 쿠키왕 (실시간 횟수 랭킹)")

# 3명 탭을 다 돌면서 데이터를 하나로 합침
all_data = []
for emp in ["정환", "소정", "가영"]:
    try:
        records = spreadsheet.worksheet(emp).get_all_records()
        all_data.extend(records)
    except:
        pass

df = pd.DataFrame(all_data)

if not df.empty:
    tz = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    # 오늘 날짜만 필터링
    today_df = df[df['날짜'].astype(str) == today_str]
    
    if not today_df.empty:
        # 이름별 최고 횟수 추출 및 정렬
        ranking = today_df.groupby("이름")["횟수"].max().reset_index()
        ranking = ranking.sort_values(by="횟수", ascending=False).reset_index(drop=True)
        ranking.index = ranking.index + 1
        
        st.dataframe(ranking, use_container_width=True)
        
        # 막대그래프(bar_chart) 대신 선 그래프(line_chart)로 띄우기!
        st.line_chart(ranking.set_index("이름")["횟수"])
    else:
        st.info("오늘 입력된 데이터가 없어! 첫 번째 쿠키왕에 도전해 봐!")
else:
    st.info("아직 입력된 데이터가 없어!")
