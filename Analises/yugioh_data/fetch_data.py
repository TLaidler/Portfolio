import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def fetch_best_decks():
    url = "https://www.yugiohmeta.com/tier-list/deck-types/Blue-Eyes#TCG"
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # Wait for JS to load

    all_rows = []
    page = 1
    while True:
        # Wait for table to load
        time.sleep(2)
        try:
            table = driver.find_element(By.XPATH, "/html/body/div[2]/main/div/div[6]/div[1]/div/table")
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.XPATH, ".//span[contains(@class, 'table-row')]")
            for row in rows:
                tds = row.find_elements(By.TAG_NAME, "td")
                if len(tds) < 6:
                    continue
                # Engines: get all alt attributes from images in the 2nd <td>
                engine_imgs = tds[1].find_elements(By.TAG_NAME, "img")
                engines = ', '.join([img.get_attribute("alt") for img in engine_imgs if img.get_attribute("alt")])
                # Top: get alt/title from image in 3rd <td>
                top_img = tds[2].find_element(By.TAG_NAME, "img")
                top = top_img.get_attribute("title") or top_img.get_attribute("alt")
                # Players: text in 4th <td>
                players = tds[3].text.strip()
                # Price: text in 5th <td>
                price = tds[4].text.strip()
                # Date: text in 6th <td>
                date = tds[5].text.strip()
                all_rows.append([engines, top, players, price, date])
        except Exception as e:
            print("Table not found or structure changed:", e)
            break

        # Find the pagination container and all page number spans
        try:
            pagination = driver.find_element(By.XPATH, "/html/body/div[2]/main/div/div[6]/div[1]/div/div[2]/div/div[3]")
            page_spans = pagination.find_elements(By.XPATH, ".//span[@data-page-number]")
            # Find the next page span (not selected)
            next_page = None
            for span in page_spans:
                if span.get_attribute("class") and "selected" not in span.get_attribute("class"):
                    if int(span.get_attribute("data-page-number")) == page + 1:
                        next_page = span
                        break
            if next_page:
                next_page.click()
                page += 1
                time.sleep(2)
            else:
                break
        except Exception as e:
            print("Pagination not found or finished:", e)
            break

    driver.quit()
    df = pd.DataFrame(all_rows, columns=['Engine', 'Top', 'Players', 'Price', 'Date'])
    return df

if __name__ == "__main__":
    df = fetch_best_decks()
    print(df)
