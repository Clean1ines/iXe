#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright parser — DOM extraction (inner_text + images) + checkpoint + resume + SIGINT save.
Сохраняет читаемый текст (как в браузере), HTML блока и ссылки на изображения.
Запуск:
  pip install playwright beautifulsoup4
  python -m playwright install chromium
  python3 parse_fipi_playwright_dom.py
"""
import time, json, os, re, signal
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

PROJ = "AC437B34557F88EA4115D2F374B0A07B"
BASE = "https://ege.fipi.ru/bank/questions.php"
TOTAL_PAGES = 98
PAGESIZE = 10
OUTFILE = "fipi_ege_tasks_playwright_dom.json"
DEBUG_DIR = "debug_pages_playwright"
IMG_DIR = "downloaded_images"
CHECKPOINT_EVERY = 5
os.makedirs(DEBUG_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

all_tasks = []
seen_keys = set()
parsed_pages = set()
_should_exit = False

def save_progress():
    tmp = OUTFILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(all_tasks, f, ensure_ascii=False, indent=2)
        os.replace(tmp, OUTFILE)
        print(f"\n💾 Progress saved: {OUTFILE} (tasks={len(all_tasks)})")
    except Exception as e:
        print("⚠️ Save failed:", e)

def signal_handler(sig, frame):
    global _should_exit
    print("\n⏸️ SIGINT received — saving progress …")
    _should_exit = True
    save_progress()

signal.signal(signal.SIGINT, signal_handler)

def build_url(params):
    from urllib.parse import urlencode
    return BASE + "?" + urlencode(params, safe='/:(),+')

def extract_codes_from_info_text(info_text):
    return re.findall(r'\b\d+\.\d+\b', info_text)

def maybe_download_image(page_url, src, session=None):
    # src can be absolute or relative — make absolute
    abs_url = urljoin(page_url, src)
    # sanitize filename
    fname = os.path.basename(abs_url.split('?')[0])
    # make unique name
    target = os.path.join(IMG_DIR, fname)
    # if file exists, append counter
    if os.path.exists(target):
        base, ext = os.path.splitext(fname)
        i = 1
        while os.path.exists(os.path.join(IMG_DIR, f"{base}_{i}{ext}")):
            i += 1
        target = os.path.join(IMG_DIR, f"{base}_{i}{ext}")
    # use playwright to fetch? simpler: use builtin curl via playwright page to download binary (but here we avoid network complexity)
    # We'll attempt to fetch via requests if available; otherwise, skip actual download and return URL.
    try:
        import requests
        r = requests.get(abs_url, timeout=15)
        if r.status_code == 200:
            with open(target, "wb") as f:
                f.write(r.content)
            return target
    except Exception:
        pass
    return abs_url  # fallback: return absolute URL

def process_page_with_dom(page, cur_url, page_number):
    """Return list of parsed items from the current page using DOM extraction."""
    items = []
    # get all qblock elements
    qnodes = page.query_selector_all("div.qblock")
    for qnode in qnodes:
        # get block id
        block_id = qnode.get_attribute("id")
        # guid from input[name=guid] if present
        guid_el = qnode.query_selector("input[name=guid]")
        guid = guid_el.get_attribute("value") if guid_el else None

        # visible text as user sees it (MathJax rendered)
        try:
            text_display = qnode.inner_text().strip()
        except Exception:
            text_display = qnode.evaluate("el => el.innerText") if qnode else ""

        # inner HTML (may contain MathML or img tags)
        try:
            html = qnode.inner_html()
        except Exception:
            html = qnode.evaluate("el => el.innerHTML") if qnode else ""

        # collect images actually present in DOM
        imgs = []
        img_elements = qnode.query_selector_all("img")
        for img_el in img_elements:
            src = img_el.get_attribute("src")
            if src:
                imgs.append(src)

        # fallback: if no <img>, try to find ShowPictureQ('...') calls in HTML and extract path
        if not imgs:
            # search for ShowPictureQ('...') and similar in the outer HTML of the page (script tags inside qnode)
            scripts = qnode.query_selector_all("script")
            for s in scripts:
                txt = s.inner_text().strip()
                m = re.search(r"ShowPictureQ\(\s*'([^']+)'", txt)
                if m:
                    imgs.append(m.group(1))
                m2 = re.search(r"ShowPictureQ2WH\(\s*'([^']+)'", txt)
                if m2:
                    imgs.append(m2.group(1))
                # ShowPictureQ2WH sometimes uses two args; try to find any 'docs/...' inside script
                for m3 in re.findall(r"'([^']+docs/[^']+)'", txt):
                    imgs.append(m3)

        # normalize image URLs (make absolute relative to page)
        abs_imgs = [urljoin(cur_url, s) for s in imgs]

        # optionally download images (comment/uncomment if you want saved images)
        downloaded = []
        for src in abs_imgs:
            downloaded.append(maybe_download_image(cur_url, src))

        # get KES info from corresponding info block (id 'i' + id tail)
        kes_codes = []
        kes_descs = []
        if block_id:
            info_id = "i" + block_id[1:] if block_id.startswith("q") else "i" + block_id
            info_el = page.query_selector(f"#{info_id}")
            if info_el:
                info_text = info_el.inner_text().strip()
                kes_codes = extract_codes_from_info_text(info_text)
                # try to extract descriptions lines after codes
                # split by lines and pick lines containing code or following line
                lines = [ln.strip() for ln in info_text.splitlines() if ln.strip()]
                # naive: any line with code or containing keywords
                for ln in lines:
                    if re.search(r'\b\d+\.\d+\b', ln) or any(word in ln for word in ["Координаты","Тип ответа","КЭС","Показательные","Тригонометрические","Вероятность","Фигуры"]):
                        kes_descs.append(ln)

        item = {
            "block_id": block_id,
            "guid": guid,
            # visible, human-friendly text (MathJax rendered -> best for reading)
            "text_display": text_display,
            # raw block HTML (for further offline parsing if needed)
            "html": html,
            # images found (absolute), and local paths if downloaded
            "images": abs_imgs,
            "images_downloaded": downloaded,
            "kes_codes": kes_codes,
            "kes_descs": kes_descs,
            "source_page": page_number,
            "proj": PROJ
        }
        items.append(item)
    return items

def load_existing():
    global all_tasks, seen_keys, parsed_pages
    if os.path.exists(OUTFILE):
        try:
            with open(OUTFILE, "r", encoding="utf-8") as f:
                all_tasks = json.load(f)
            print(f"🔁 Loaded existing OUTFILE (tasks={len(all_tasks)})")
            for it in all_tasks:
                key = it.get("guid") or it.get("block_id")
                if key:
                    seen_keys.add(key)
                sp = it.get("source_page")
                if isinstance(sp, int):
                    parsed_pages.add(sp)
        except Exception as e:
            print("⚠️ Failed to load existing OUTFILE:", e)

def main():
    global all_tasks, seen_keys, parsed_pages, _should_exit
    load_existing()
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(user_agent=ua, locale="ru-RU")
        context.add_cookies([{"name":"md_auto","value":"qprint","domain":"ege.fipi.ru","path":"/"}])
        page = context.new_page()

        # init page
        params_init = {"proj": PROJ, "init_filter_themes": 1}
        url_init = build_url(params_init)
        print("Navigate init:", url_init)
        page.goto(url_init, wait_until="networkidle", timeout=20000)
        try:
            page.wait_for_selector("div.qblock", timeout=8000)
        except Exception:
            pass
        # process DOM
        items = process_page_with_dom(page, url_init, 1)
        added = 0
        for it in items:
            key = it.get("guid") or it.get("block_id")
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_tasks.append(it)
                added += 1
        parsed_pages.add(1)
        print(f" init parsed qblocks = {len(items)} (added {added})")

        # iterate pages
        for pnum in range(1, TOTAL_PAGES):
            if _should_exit:
                print("Exit on SIGINT...")
                break
            if (pnum+1) in parsed_pages:
                print(f"Page {pnum+1} already parsed (resume) — skipping")
                continue
            crtm = str(int(time.time()))
            params = {"proj": PROJ, "page": pnum, "pagesize": PAGESIZE, "crtm": crtm}
            url = build_url(params)
            print(f"Navigate page {pnum}: {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
            except Exception as e:
                print("goto failed:", e)
            try:
                page.wait_for_selector("div.qblock", timeout=7000)
            except Exception:
                pass
            items = process_page_with_dom(page, url, pnum+1)
            added = 0
            for it in items:
                key = it.get("guid") or it.get("block_id")
                if key and key not in seen_keys:
                    seen_keys.add(key)
                    all_tasks.append(it)
                    added += 1
            parsed_pages.add(pnum+1)
            print(f" page {pnum}: parsed qblocks = {len(items)} (added {added}) total tasks={len(all_tasks)}")
            if (pnum % CHECKPOINT_EVERY) == 0:
                save_progress()
            time.sleep(0.25)

        save_progress()
        context.close()
        browser.close()

    print("Done. Total tasks:", len(all_tasks))

if __name__ == "__main__":
    main()
