import re
from pathlib import Path
from bs4 import BeautifulSoup
from utils.downloader import AssetDownloader

class UnwantedElementRemover:
    def process(self, soup: BeautifulSoup, run_folder_page: Path):
        downloaded_files = {}
        downloaded_images = {}
        # Remove hint divs
        for div in soup.find_all('div', class_=re.compile(r'hint'), attrs={'id': 'hint', 'name': 'hint'}):
            div.decompose()
        # Remove status title spans
        for span in soup.find_all('span', class_=re.compile(r'status-title-text')):
            span.decompose()
        # Remove task status spans
        for span in soup.find_all('span', class_=re.compile(r'task-status')):
            span.decompose()
        # Remove table rows with bgcolor
        for tr in soup.find_all('tr', attrs={'bgcolor': '#FFFFFF'}):
            tr.decompose()
        return soup, {}
class ImageScriptProcessor:
    def process(self, soup: BeautifulSoup, run_folder_page: Path, downloader: AssetDownloader = None):
        if downloader is None:
            raise ValueError("AssetDownloader must be provided")
        assets_dir = run_folder_page / "assets"
        downloaded_files = {}
        downloaded_images = {}
        for script in soup.find_all('script', string=re.compile(r"ShowPicture$$'[^']*'$$")):
            match = re.search(r"ShowPicture$$'([^']*)'$$", script.string)
            if match:
                img_url = match.group(1)
                local_path = downloader.download(img_url, assets_dir, asset_type='image')
                if local_path:
                    img_tag = soup.new_tag('img', src=f"assets/{local_path.name}")
                    script.replace_with(img_tag)
                    downloaded_images[img_url] = f"assets/{local_path.name}"
        return soup, {'downloaded_files': downloaded_files}
class FileLinkProcessor:
    def process(self, soup: BeautifulSoup, run_folder_page: Path, downloader: AssetDownloader = None):
        if downloader is None:
            raise ValueError("AssetDownloader must be provided")
        assets_dir = run_folder_page / "assets"
        downloaded_files = {}
        downloaded_images = {}
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('javascript:'):
                match = re.search(r"window\.open$$'([^']*)'", href)
                if match:
                    file_url = match.group(1).lstrip('../')
                    local_path = downloader.download(file_url, assets_dir, asset_type='file')
                    if local_path:
                        a['href'] = f"assets/{local_path.name}"
                        downloaded_images[file_url] = f"assets/{local_path.name}"
            elif href.endswith(('.pdf', '.zip', '.doc', '.docx')):
                file_url = href.lstrip('../')
                local_path = downloader.download(file_url, assets_dir, asset_type='file')
                if local_path:
                    a['href'] = f"assets/{local_path.name}"
                    downloaded_images[file_url] = f"assets/{local_path.name}"
        return soup, {'downloaded_files': downloaded_files}
class TaskInfoProcessor:
    def process(self, soup: BeautifulSoup, run_folder_page: Path):
        for button in soup.find_all('div', class_='info-button'):
            button['onclick'] = "toggleInfo(this); return false;"
        return soup, {}
class InputFieldRemover:
    def process(self, soup: BeautifulSoup, run_folder_page: Path):
        for inp in soup.find_all('input', attrs={'name': 'answer'}):
            inp.decompose()
        return soup, {}
class MathMLRemover:
    def process(self, soup: BeautifulSoup, run_folder_page: Path):
        for tag in soup.find_all(['math', 'mml:math']):
            tag.decompose()
        return soup, {}
