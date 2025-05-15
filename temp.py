# pip install playwright
# terminālī jāpalaiž komandu "playwright install"

from playwright.sync_api import sync_playwright
from fake_useragent import UserAgent
from lxml.html import fromstring  # https://lxml.de/lxmlhtml.html

UA = UserAgent()


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


# lt versijā Playwright risinājums nestrādā kategoriju ieguvei:
# manuāli var nokopēt "//*[@id="desktop-menu-placeholder"]/div/div/ul" elementa saturu https://barbora.lt/:
def scrape_barbora_lt_temp():
    ul = """
    <ul class="desktop-menu--parent-category-list"><li id="fti-desktop-subcategory-0"><div id="fti-desktop-category-0" class="desktop-menu--category "><a class="category-item--title" href="/darzoves-ir-vaisiai"><span>Daržovės ir vaisiai</span></a></div></li><li id="fti-desktop-subcategory-1"><div id="fti-desktop-category-1" class="desktop-menu--category "><a class="category-item--title" href="/pieno-gaminiai-ir-kiausiniai"><span>Pieno gaminiai ir kiaušiniai</span></a></div></li><li id="fti-desktop-subcategory-2"><div id="fti-desktop-category-2" class="desktop-menu--category "><a class="category-item--title" href="/duonos-gaminiai-ir-konditerija"><span>Duonos gaminiai ir konditerija</span></a></div></li><li id="fti-desktop-subcategory-3"><div id="fti-desktop-category-3" class="desktop-menu--category "><a class="category-item--title" href="/mesa-zuvis-ir-kulinarija"><span>Mėsa, žuvis ir kulinarija</span></a></div></li><li id="fti-desktop-subcategory-4"><div id="fti-desktop-category-4" class="desktop-menu--category "><a class="category-item--title" href="/bakaleja"><span>Bakalėja</span></a></div></li><li id="fti-desktop-subcategory-5"><div id="fti-desktop-category-5" class="desktop-menu--category "><a class="category-item--title" href="/saldytas-maistas"><span>Šaldytas maistas</span></a></div></li><li id="fti-desktop-subcategory-6"><div id="fti-desktop-category-6" class="desktop-menu--category "><a class="category-item--title" href="/gerimai"><span>Gėrimai</span></a></div></li><li id="fti-desktop-subcategory-7"><div id="fti-desktop-category-7" class="desktop-menu--category "><a class="category-item--title" href="/kudikiu-ir-vaiku-prekes"><span>Kūdikių ir vaikų prekės</span></a></div></li><li id="fti-desktop-subcategory-8"><div id="fti-desktop-category-8" class="desktop-menu--category "><a class="category-item--title" href="/kosmetika-ir-higiena"><span>Kosmetika ir higiena</span></a></div></li><li id="fti-desktop-subcategory-9"><div id="fti-desktop-category-9" class="desktop-menu--category "><a class="category-item--title" href="/svaros-ir-gyvunu-prekes"><span>Švaros ir gyvūnų prekės</span></a></div></li><li id="fti-desktop-subcategory-10"><div id="fti-desktop-category-10" class="desktop-menu--category "><a class="category-item--title" href="/namai-ir-laisvalaikis"><span>Namai ir laisvalaikis</span></a></div></li></ul>
    """
    url_paths = []
    html = fromstring(ul)
    for a in html.xpath("//a"):
        url_paths.append(a.get("href"))
    print(url_paths)


if __name__ == "__main__":
    scrape_barbora_lv_temp()
    scrape_barbora_lt_temp()
