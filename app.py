import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
        user_sheet = spreadsheet.worksheet(name)
        user_sheet.append_row([today_date, name, time_type, count, boxes])
        st.success(f"✅ {name}님, 개인 탭에 {today_date} 기록 완료! (현재 횟수: {count})")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"🚨 구글 시트 맨 아래에 '{name}' 탭이 없어. 탭 이름을 다시 확인해 줘.")

st.write("---")

# ==========================================
# 3. 주간 생산량 (최근 7일 기준)
# ==========================================
st.subheader("🏆 주간 생산량 (최근 7일)")

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
    today = datetime.now(tz)
    week_ago = today - timedelta(days=6)
    
    today_str = today.strftime("%Y-%m-%d")
    week_ago_str = week_ago.strftime("%Y-%m-%d")
    
    week_df = df[(df['날짜'] >= week_ago_str) & (df['날짜'] <= today_str)]
    
    if not week_df.empty:
        # 오후 기록이 하루 총 횟수이므로, 날짜별로 가장 큰 숫자(max)를 하루 실적으로 계산
        daily_max = week_df.groupby(['날짜', '이름'])['횟수'].max().reset_index()
        
        # 7일 치 합산 계산
        weekly_total = daily_max.groupby('이름')['횟수'].sum().reset_index()
        weekly_total = weekly_total.sort_values(by="횟수", ascending=False).reset_index(drop=True)
        weekly_total.index = weekly_total.index + 1
        
        st.markdown("**👑 이번 주 총 누적 횟수**")
        st.dataframe(weekly_total, use_container_width=True)
        
        # X축을 일(Day) 단위 텍스트로 짧게 변경
        daily_max['일자'] = pd.to_datetime(daily_max['날짜']).dt.strftime('%d일')
        
        current_month = today.month
        st.markdown(f"**📈 {current_month}월 일별 횟수 변화**")
        
        chart_data = daily_max.pivot(index='일자', columns='이름', values='횟수').fillna(0)
        st.line_chart(chart_data)
        
    else:
        st.info("최근 7일 동안 입력된 데이터가 없어!")
else:
    st.info("아직 입력된 데이터가 없어!")
