import sys
import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import concurrent.futures

def fetch_proxies():
    print("Fetching proxies...")
    url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    response = requests.get(url)
    data = response.json()
    return data["data"]

def test_proxy_speed(proxy):
    test_url = "https://httpbin.org/ip"
    proxies = {
        "http": f"{proxy['ip']}:{proxy['port']}",
        "https": f"{proxy['ip']}:{proxy['port']}",
    }
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(test_url, proxies=proxies, timeout=5)
        if response.status_code == 200:
            return response.elapsed.total_seconds()
    except requests.exceptions.RequestException:
        pass

    return None

def get_proxy_location(ip_address):
    location_url = f"https://ipapi.co/{ip_address}/json/"
    response = requests.get(location_url)
    location_data = response.json()
    return {
        "country": location_data.get("country_name"),
        "region": location_data.get("region"),
        "city": location_data.get("city"),
    }

def test_and_save_proxy(proxy, total_proxies, index):
    response_time = test_proxy_speed(proxy)
    print(f"Testing proxy {index + 1}/{total_proxies}: {proxy['ip']}:{proxy['port']}")

    if response_time is not None:
        proxy["response_time"] = response_time
        proxy["location"] = get_proxy_location(proxy["ip"])
        print(f"Proxy {proxy['ip']}:{proxy['port']} works! (Response Time: {response_time} seconds)")

        with open("GOODPROXIES.txt", "a") as good_proxies_file:
            good_proxies_file.write(f"{proxy['ip']}:{proxy['port']}\n")

        return proxy

    return None

def filter_proxies(proxies, filter_type=None, value=None):
    print("Filtering proxies...")

    filtered_proxies = []
    total_proxies = len(proxies)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(test_and_save_proxy, proxy, total_proxies, index) for index, proxy in enumerate(proxies)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                filtered_proxies.append(result)

    if filter_type == '%':
        percentage = int(value)
        filtered_proxies = sorted(filtered_proxies, key=lambda x: x["response_time"])
        top_proxies = int(len(filtered_proxies) * percentage / 100)
        filtered_proxies = filtered_proxies[:top_proxies]
    elif filter_type == '#':
        number = int(value)
        filtered_proxies = sorted(filtered_proxies, key=lambda x: x["response_time"])
        filtered_proxies = filtered_proxies[:number]

    print("Finished filtering proxies.")
    print(filtered_proxies)


def main():
    while True:
        print("1. Find and test proxies, save working proxies")
        print("2. Find and test proxies, save top % or # of working proxies")
        print("3. Test proxies in PROXIES.txt")
        print("4. Exit")

        option = input("Enter option: ")

        if option == "1":
            proxies = fetch_proxies()
            filter_proxies(proxies)
        elif option == "2":
            print("1. Find and test proxies, keep fastest % of working proxies")
            print("2. Find and test proxies, keep fastest # of working proxies")
            filter_option = input("Enter option: ")

            if filter_option == "1":
                percentage = input("Enter %: ")
                proxies = fetch_proxies()
                filter_proxies(proxies, filter_type="%", value=percentage)
            elif filter_option == "2":
                number = input("Enter #: ")
                proxies = fetch_proxies()
                filter_proxies(proxies, filter_type="#", value=number)
        elif option == "3":
            with open("PROXIES.txt", "r") as proxies_file:
                proxies = [line.strip() for line in proxies_file.readlines()]
            filter_proxies(proxies)
        elif option == "4":
            print("Exiting...")
            sys.exit()
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
