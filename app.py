from flask import Flask, jsonify, request, render_template
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask_cors import CORS
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        # AJAX 요청 데이터 받기
        data = request.json
        booking_number = data.get("booking_number", "").strip()
        if not booking_number:
            return jsonify({"error": "예약번호를 입력하세요."}), 400

        # Selenium Chrome Driver 설정 (최적화 적용)
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # 지연 시간 추가
        time.sleep(random.uniform(1.5, 2.5))

        driver.get("https://partner.booking.naver.com/bizes/685947/booking-list-view")
        wait = WebDriverWait(driver, 10)

        # 예약조회 버튼 클릭
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#app > div > div.BaseLayout__container__zPiGd.full-layout > div.Contents__root__KKNX7 > div > div.BookingFilter__root__S9XG7 > div.BookingFilter__search-input__3x1-d > form > div")
            )
        ).click()

        # 예약번호조회 버튼 클릭
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#app > div > div.BaseLayout__container__zPiGd.full-layout > div.Contents__root__KKNX7 > div > div.BookingFilter__root__S9XG7 > div.BookingFilter__search-input__3x1-d > form > div > div > a:nth-child(3)")
            )
        ).click()

        # 입력 및 검색
        input_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#app > div > div.BaseLayout__container__zPiGd.full-layout > div.Contents__root__KKNX7 > div > div.BookingFilter__root__S9XG7 > div.BookingFilter__search-input__3x1-d > form > input")
            )
        )
        input_element.clear()
        input_element.send_keys(booking_number)

        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#app > div > div.BaseLayout__container__zPiGd.full-layout > div.Contents__root__KKNX7 > div > div.BookingFilter__root__S9XG7 > div.BookingFilter__search-input__3x1-d > form > button")
            )
        ).click()

        # 결과 확인
        summary_number_selector = "#app > div > div.BaseLayout__container__zPiGd.full-layout > div.Contents__root__KKNX7 > div > div.BookingList__summary-number__sJ7fW > strong"
        summary_number = get_element_text(wait, summary_number_selector, default_text="0")

        if summary_number != "1":
            driver.quit()
            return jsonify({"error": f"{booking_number} 예약번호는 존재하지 않습니다."})

        # 결과 수집
        results = {
            "예약자": get_element_text(wait, 예약자, "예약자 정보가 없습니다."),
            "전화번호": get_element_text(wait, 전화번호, "전화번호 정보가 없습니다."),
            "예약번호": get_element_text(wait, 예약번호, "예약번호 정보가 없습니다."),
            "예약상품": get_element_text(wait, 예약상품, "예약 상품 정보가 없습니다."),
            "이용일시": get_element_text(wait, 이용일시, "이용 일시 정보가 없습니다.")
        }

        driver.quit()
        return jsonify(results)

    except Exception as e:
        logging.error(f"서버 오류: {str(e)}")
        return jsonify({"error": f"서버 오류 발생: {str(e)}"}), 500


def get_element_text(wait, selector, default_text):
    try:
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))).text
    except Exception:
        return default_text


if __name__ == "__main__":
    app.run(debug=True)
