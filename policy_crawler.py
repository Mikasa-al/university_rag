
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime
import json
import time

# 郑州大学学生工作网：管理制度栏目，共3页
BASE_URL = "https://www5.zzu.edu.cn/student/glzd/"
LIST_URLS = [
    "https://www5.zzu.edu.cn/student/glzd.htm",
    "https://www5.zzu.edu.cn/student/glzd/2.htm",
    "https://www5.zzu.edu.cn/student/glzd/1.htm",
]

OUTPUT_DIR = Path("crawled_policies")
OUTPUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.trust_env = False
session.headers.update({"User-Agent": "Mozilla/5.0"})


def get_soup(url):
    response = session.get(url, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def get_policy_links():
    links = {}

    for list_url in LIST_URLS:
        print(f"\n正在读取列表页：{list_url}")

        try:
            soup = get_soup(list_url)

            for a in soup.select("a[href]"):
                href = a.get("href", "")
                text = a.get_text(" ", strip=True)
                if ".htm" in href and ("下一页" in text or text.isdigit()):
                    print("发现分页链接：", text, "->", urljoin(list_url, href))

            print("当前页面标题：", soup.title.get_text(strip=True))
            print("页面中的制度相关文字：")
            print(soup.get_text(" ", strip=True)[-1500:])

            for a in soup.select("a[href]"):
                title = a.get_text(" ", strip=True)
                detail_url = urljoin(list_url, a["href"])

                # 只收集管理制度栏目中的详情页
                if (
                        title
                        and "/student/info/1008/" in detail_url
                        and detail_url.endswith(".htm")
                ):
                    links[detail_url] = title

        except Exception as e:
            print("列表页读取失败：", list_url, e)

        time.sleep(1)
        print("\n===== 所有候选链接 =====")
        for url, title in links.items():
            print(title, "->", url)

    return links


def get_policy_content(url, list_title):
    soup = get_soup(url)

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if ".doc" in href.lower() or ".pdf" in href.lower():
            attachment_url = urljoin(url, href)
            filename = a.get_text(strip=True)
            download_attachment(attachment_url, filename)

    content = None
    for selector in [
        ".v_news_content",
        "#vsb_content",
        ".article-content",
    ]:
        content = soup.select_one(selector)
        if content:
            break

    if not content:
        return None

    title = soup.title.get_text(strip=True) if soup.title else list_title

    return {
        "title": list_title,
        "page_title": title,
        "source_url": url,
        "content": content.get_text("\n", strip=True),
        "crawled_at": datetime.now().isoformat(timespec="seconds"),
    }

def download_attachment(url, filename):
    """下载制度附件并保存到本地。"""
    save_dir = OUTPUT_DIR / "attachments"
    save_dir.mkdir(exist_ok=True)

    file_path = save_dir / filename

    response = session.get(url, timeout=30)
    response.raise_for_status()

    file_path.write_bytes(response.content)
    print("附件已下载：", file_path)

if __name__ == "__main__":
    links = get_policy_links()
    print(f"\n共发现 {len(links)} 个候选制度链接")

    results = []

    for index, (url, title) in enumerate(links.items(), start=1):
        try:
            policy = get_policy_content(url, title)

            if policy and policy["content"]:
                results.append(policy)
                print(f"[{index}/{len(links)}] 成功：{title}")
            else:
                print(f"[{index}/{len(links)}] 未找到正文：{title}")

        except Exception as e:
            print(f"[{index}/{len(links)}] 失败：{title}，原因：{e}")

        time.sleep(1)

    output_file = OUTPUT_DIR / "policies.json"
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n爬取完成！")
    print("候选链接数：", len(links))
    print("成功提取正文：", len(results))
    print("保存位置：", output_file.resolve())
