#!/usr/bin/env python3
import os
import io
import re
import time
import requests
import traceback
from datetime import datetime, date
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from PIL import Image
import pytesseract
import cv2
import shutil
from pathlib import Path

# -----------------------------------
#            CONFIG
# -----------------------------------
LOGIN_URL = "https://reports.ongc.co.in/"
NEWS_PAGE = "https://reports.ongc.co.in/group/reports_en/home/media/oil-and-gas-in-media/news-in-media"
TRENDING_PAGE = "https://reports.ongc.co.in/group/reports_en"

USERNAME = "vbnetwork"
PASSWORD = "Ongc!4321"

pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

FIREFOX_BIN = "/usr/bin/firefox-esr"
GECKO_BIN = "/usr/local/bin/geckodriver"

HEADLESS = True
current_log_time = datetime.now().strftime("%d-%m-%y, %H:%M:%S")

# -----------------------------------
#        BROWSER SETUP
# -----------------------------------
options = Options()
options.binary_location = FIREFOX_BIN
if HEADLESS:
    options.add_argument("--headless")

service = Service(GECKO_BIN)


# -----------------------------------
#        HELPER FUNCTIONS
# -----------------------------------
def save_debug(driver, prefix="debug"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(f"{prefix}_{ts}.png")
    with open(f"{prefix}_{ts}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"{current_log_time} [debug] Saved HTML & screenshot.")


def check_site_available(driver, url, timeout=10):
    """Return True if site loads WITHOUT overwriting files."""
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        time.sleep(1)
        if "<html" in driver.page_source.lower():
            print(f"{current_log_time} [info] Site is reachable.")
            return True
        print(f"{current_log_time} [error] Site HTML invalid.")
        return False
    except Exception:
        print(f"{current_log_time} [error] Site not reachable (exception).")
        return False


def ocr_from_captcha_file(cap_img):
    img = cv2.imread(cap_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape[:2]
    if max(h, w) < 200:
        gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 11, 2)
    th = cv2.medianBlur(th, 3)

    tmp = f"tmp_{int(time.time())}.png"
    cv2.imwrite(tmp, th)

    try:
        txt = pytesseract.image_to_string(
            tmp,
            config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        )
    finally:
        try: os.remove(tmp)
        except: pass

    return re.sub(r"[^A-Za-z0-9]", "", txt).strip()


# -----------------------------------
#       PDF DOWNLOAD (SAFE MODE)
# -----------------------------------
def find_and_download_pdf_for_date(driver, page_url, target_date=None,
                                   save_dir="/home/ubuntu/learn/practice/downloads"):

    if target_date is None:
        target_date = date.today()

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"{current_log_time} [info] Opening news PDF page:", page_url)
    driver.get(page_url)
    time.sleep(2)

    anchors = driver.find_elements(By.TAG_NAME, "a")

    numeric_date_re = re.compile(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b')
    textual_date_re = re.compile(
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*,?\s+\d{4}\b',
        re.I
    )

    def parse_date(s):
        if not s:
            return None

        s = s.strip()

        m = numeric_date_re.search(s)
        if m:
            ds = m.group(0).replace("/", "-").replace(".", "-")
            for fmt in ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(ds, fmt).date()
                except:
                    pass

        m = textual_date_re.search(s)
        if m:
            ds = m.group(0).replace(",", "")
            for fmt in ("%d %b %Y", "%d %B %Y"):
                try:
                    return datetime.strptime(ds, fmt).date()
                except:
                    pass

        return None

    pdf_candidates = []

    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
            txt = a.text.strip()
            if ".pdf" in href.lower():
                d = parse_date(txt) or parse_date(href)
                pdf_candidates.append({"href": href, "date": d})
        except:
            pass

    if not pdf_candidates:
        print(f"{current_log_time} [warn] No PDF found.")
        return None

    with_dates = [c for c in pdf_candidates if c["date"]]

    chosen = None
    exact = [c for c in with_dates if c["date"] == target_date]
    if exact:
        chosen = exact[0]
    else:
        eligible = [c for c in with_dates if c["date"] <= target_date]
        chosen = max(eligible, key=lambda x: x["date"]) if eligible else max(with_dates, key=lambda x: x["date"])

    pdf_url = urljoin(page_url, chosen["href"])
    print(f"{current_log_time} [info] Downloading:", pdf_url)

    session = requests.Session()
    for ck in driver.get_cookies():
        session.cookies.set(ck["name"], ck["value"])

    resp = session.get(pdf_url, stream=True)
    if resp.status_code != 200:
        print(f"{current_log_time} [error] PDF download failed:", resp.status_code)
        return None
    formatted_date = target_date.strftime("%d.%m.%Y")

    final_path = os.path.join(save_dir, f"Oil and Gas News - {formatted_date}.pdf")
    print(f"{current_log_time} {final_path}")
    
    #src = Path(final_path)                 # full source path
    #dst = Path("/mnt/upload") / src.name

    #shutil.copy2(src, dst)

    with open(final_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)

    print(f"{current_log_time} [ok] PDF saved as:", final_path)

    src = Path(final_path)                 # full source path
    dst = Path("/mnt/upload") / src.name

    shutil.copy2(src, dst)



    return final_path


# -----------------------------------
#     TRENDING FETCH + DAILY FILE
# -----------------------------------
def extract_trending_carousel(driver, page_url=TRENDING_PAGE):
    print(f"{current_log_time} [info] Opening Trending Stories (carousel):", page_url)
    driver.get(page_url)
    time.sleep(3)

    # ----------------------------
    # FIX: expand slider visibility
    # ----------------------------
    driver.execute_script("""
        let slider = document.querySelector('#trendSlider');
        if (slider) slider.style.overflow = 'visible';
    """)

    # Stop autoplay to stabilize DOM
    driver.execute_script("""
        try {
            if (window.$ && $('#trendSlider').data('owl.carousel')) {
                $('#trendSlider').trigger('stop.owl.autoplay');
            }
        } catch(e) {}
    """)

    time.sleep(1)

    # Get ALL items (cloned + real)
    items = driver.find_elements(By.CSS_SELECTOR, "#trendSlider .item")

    print(f"{current_log_time} [info] Found raw items: {len(items)}")

    if not items:
        print(f"{current_log_time} [error] No carousel items detected!")
        return None

    results = []
    seen_links = set()

    # Prepare image dir
    today_str = date.today().strftime("%Y-%m-%d")
    image_dir = Path(f"/home/ubuntu/learn/practice/trending_images/{today_str}")
    image_dir.mkdir(parents=True, exist_ok=True)

    for idx, item in enumerate(items, start=1):

        try:
            a = item.find_element(By.TAG_NAME, "a")
            link = a.get_attribute("href")
            if not link:
                continue

            # Deduplicate by URL
            if link in seen_links:
                continue
            seen_links.add(link)

            # IMAGE
            try:
                img_url = item.find_element(By.CSS_SELECTOR, ".storyThumb img").get_attribute("src")
            except:
                img_url = ""

            # DATE
            # try:
            #     date_txt = item.find_element(By.CSS_SELECTOR, ".dateTime").text.strip()
            # except:
            #     date_txt = ""

            # TITLE (THIS WAS FAILING → FIXED)
            try:
                title = item.find_element(By.CSS_SELECTOR, ".storyTitle").get_attribute("textContent").strip()
            except:
                title = ""

            # ----------------------------
            # Download image
            # ----------------------------
            img_file = None
            if img_url:
                img_file = image_dir / f"carousel_{idx}.jpg"
                try:
                    session = requests.Session()
                    for ck in driver.get_cookies():
                        session.cookies.set(ck["name"], ck["value"])

                    resp = session.get(img_url, stream=True, timeout=10)
                    if resp.status_code == 200:
                        with open(img_file, "wb") as f:
                            for chunk in resp.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                        print(f"{current_log_time} [ok] Downloaded image: {img_file}")
                    else:
                        print(f"{current_log_time} [error] Image download failed: {resp.status_code}")

                except Exception as e:
                    print(f"{current_log_time} [error] Exception downloading:", e)
                    img_file = None

            results.append({
                "title": title,
                "date": date_txt,
                "url": link,
                "img_url": img_url,
                "img_file": str(img_file) if img_file else None
            })

        except Exception as e:
            print(f"{current_log_time} [warn] Error parsing an item:", e)

    # ----------------------------
    # SAVE SUMMARY FILE
    # ----------------------------
    out_file = f"/home/ubuntu/learn/practice/trending_carousel_{today_str}.txt"

    with open(out_file, "w", encoding="utf-8") as f:
        for r in results:
            f.write("TITLE: " + r["title"] + "\n")
            f.write("DATE: " + r["date"] + "\n")
            f.write("IMAGE URL: " + (r["img_url"] or "") + "\n")
            f.write("IMAGE FILE: " + (r["img_file"] or "") + "\n")
            f.write("URL: " + r["url"] + "\n\n")

    print(f"{current_log_time} [ok] Saved carousel summary:", out_file)

    # Copy summary to mount
    src = Path(out_file)
    dst = Path("/mnt/upload") / src.name
    shutil.copy2(src, dst)

    return results



# -----------------------------------
#                MAIN
# -----------------------------------
def main():
    driver = webdriver.Firefox(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # ---- SAFE CHECK BEFORE ANYTHING ----
        print(f"{current_log_time} [info] Checking site availability...")
        if not check_site_available(driver, LOGIN_URL):
            print(f"{current_log_time} [FAIL-SAFE] Site unreachable → NOT overwriting files.")
            return

        # reload page cleanly
        driver.get(LOGIN_URL)
        time.sleep(1)

        # ---- LOGIN ----
        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "_com_liferay_login_web_portlet_LoginPortlet_login"))
        )
        password_input = driver.find_element(By.ID, "_com_liferay_login_web_portlet_LoginPortlet_password")

        captcha_elem = wait.until(EC.presence_of_element_located((By.ID, "captcha_img")))
        #cap_file = f"captcha_{int(time.time())}.png"
        
        CAPTCHA_DIR = "/home/ubuntu/learn/practice/captchas"
        os.makedirs(CAPTCHA_DIR, exist_ok=True)
        cap_file = os.path.join(CAPTCHA_DIR,f"captcha_{int(time.time())}.png")


        captcha_elem.screenshot(cap_file)

        captcha_text = ocr_from_captcha_file(cap_file)

        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)

        try:
            captcha_input = driver.find_element(By.ID, "_com_liferay_login_web_portlet_LoginPortlet_captchText")
        except:
            captcha_input = driver.find_element(By.NAME, "captchaText")

        captcha_input.send_keys(captcha_text)

        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary")))
        submit.click()

        time.sleep(2)

        # ---- CHECK LOGIN SUCCESS SAFELY ----
        if "logout" not in driver.page_source.lower():
            print(f"{current_log_time} [FAIL-SAFE] Login failed → DO NOT overwrite files.")
            return

        print(f"{current_log_time} [info] Login successful.")

        # ---- TRENDING EXTRACTION ----
        trending = extract_trending_carousel(driver)
        if not trending:
            print(f"{current_log_time} [FAIL-SAFE] Trending extraction failed → NOT overwriting PDF.")
            return

        # ---- PDF DOWNLOAD ----
        find_and_download_pdf_for_date(driver, NEWS_PAGE, target_date=date.today())
        
        # ---- SENDING FILES TO MOUNT DIRECTORY ----

        
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()