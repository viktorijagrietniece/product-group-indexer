# pip install playwright
# terminālī jāpalaiž komandu "playwright install"

from playwright.sync_api import sync_playwright


def scrape_barbora_lv_temp():
    url = "https://barbora.lv/"
    url_paths = []

    with sync_playwright() as p:
        browser = p.webkit.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(".desktop-menu--parent-category-list")
        for category in page.query_selector_all(
            'xpath=//ul[@class="desktop-menu--parent-category-list"]/li'
        ):
            href = category.query_selector("a").get_attribute("href")
            url_paths.append(href)
        browser.close()

    print(url_paths)


if __name__ == "__main__":
    scrape_barbora_lv_temp()
