import warnings
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Suppress urllib3 warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")


def get_element_text(driver, by, value):
    """
    Find an element and return its text. Return "Not Found" if the element is missing.
    """
    try:
        return driver.find_element(by, value).text
    except NoSuchElementException:
        return "Not Found"


def google_maps_scraper(search_query, result_count):
    """
    Scrapes business information from Google Maps for a given query.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.google.com/maps")
    wait = WebDriverWait(driver, 15)

    # Find the search box and enter the search query
    search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    # Wait for the first results to load
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK")))

    results = []
    last_results_length = 0

    while len(results) < result_count:
        current_results = driver.find_elements(By.CLASS_NAME, "Nv2PK")

        if len(current_results) > last_results_length:
            # Process new results
            for place in current_results[last_results_length:]:
                try:
                    place.click()

                    # Wait for the details to fully load
                    wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
                    )

                    # Add a wait for stabilization
                    time.sleep(1)  # To stabilize DOM changes

                    # Retrieve each field in the correct order
                    name = get_element_text(driver, By.CLASS_NAME, "DUwDvf")
                    address = get_element_text(
                        driver,
                        By.XPATH,
                        "//button[@data-item-id='address']//div[contains(@class, 'rogA2c')]",
                    )
                    phone = get_element_text(
                        driver,
                        By.XPATH,
                        "//button[@data-item-id='phone']//div[contains(@class, 'rogA2c')]",
                    )
                    website = get_element_text(
                        driver,
                        By.XPATH,
                        "//a[@data-item-id='authority']//div[contains(@class, 'rogA2c')]",
                    )

                    # Ensure all fields are properly loaded
                    if name and (address or phone or website):
                        results.append(
                            {
                                "name": name,
                                "address": address,
                                "phone": phone,
                                "website": website,
                            }
                        )

                    # Exit if the required number of results is reached
                    if len(results) >= result_count:
                        break
                except Exception as e:
                    print(f"Error while processing place: {e}")
                    continue

            last_results_length = len(current_results)
        else:
            # Scroll and wait if there are no new results
            print("No new results, scrolling...")
            driver.execute_script(
                "document.querySelector(\"#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd\").scrollBy(0,2000);")

            time.sleep(2)

        # Exit if the required number of results is reached
        if len(results) >= result_count:
            break

    driver.quit()
    return results


if __name__ == "__main__":
    query = "restaurants in Istanbul"
    results_to_fetch = 20
    scraped_data = google_maps_scraper(query, results_to_fetch)

    # Save the data to a CSV file
    import csv

    with open("scraped_results.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["name", "address", "phone", "website"]
        )
        writer.writeheader()
        for data in scraped_data:
            writer.writerow(data)

    print(f"Scraped {len(scraped_data)} results and saved to scraped_results.csv")
