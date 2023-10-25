import time
from html2text import HTML2Text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


WAIT_FOR_PAGE = 1 # wait 1 second for website to load


def get_website(address):
    if not address.startswith("http"):
        return f"Wrong address {address} for the website"
    try:
        html = get_website_html(address)
    except Exception as e:
        return f"Cant access website at {address}"

    h = HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    txt = h.handle(html)

    response = ""
    try:
        fname = address.split("/")[-1].split(".")[0]
        with open(f"{fname}.html", "w") as fout:
            fout.write(html)
        response += f"Website from {address} saved to file {fname}.html\n"

        with open(f"{fname}.txt", "w") as fout:
            fout.write(txt)
        response += f"Text from {address} saved to file {fname}.txt\n"
    except Exception as e:
        pass

    if len(txt.split(" ")) < 200:
        response += f"The website from {address} has the following content:\n{txt}"
    else:
        response += f"The website from {address} has the following beginning:\n{' '.join(txt.split(' ')[:100])}"

    response += "\n"
    return response


def get_website_text(address):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options) #executable_path=driver_path)
    # Go to the website
    driver.get(address)
    # Get the content of the website
    time.sleep(WAIT_FOR_PAGE)
    content = driver.page_source
    driver.quit()
    h = HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    return h.handle(content)

def get_website_html(address):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options) #executable_path=driver_path)
    # Go to the website
    driver.get(address)
    # Get the content of the website
    time.sleep(WAIT_FOR_PAGE) 
    return driver.page_source
    