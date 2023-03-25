import requests
import time

def fetch_proxy_data():
    url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    response = requests.get(url)
    data = response.json()
    return data["data"]

def get_proxy_location(proxy_ip):
    url = f"http://ip-api.com/json/{proxy_ip}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "success":
        return {
            "country": data["country"],
            "region": data["regionName"],
            "city": data["city"]
        }
    else:
        return None

def test_proxy_speed(proxy):
    test_url = "http://httpbin.org/get"
    proxies = {
        "http": f"http://{proxy['ip']}:{proxy['port']}",
        "https": f"http://{proxy['ip']}:{proxy['port']}"
    }

    try:
        start_time = time.time()
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response.raise_for_status()
        elapsed_time = time.time() - start_time
    except requests.exceptions.RequestException:
        elapsed_time = None

    return elapsed_time

def filter_proxies(proxies, filter_type=None, value=None):
    print("Filtering proxies...")

    filtered_proxies = []
    total_proxies = len(proxies)
    
    with open("GOODPROXIES.txt", "w") as good_proxies_file:
        for index, proxy in enumerate(proxies):
            response_time = test_proxy_speed(proxy)
            print(f"Testing proxy {index + 1}/{total_proxies}: {proxy['ip']}:{proxy['port']}")

            if response_time is not None:
                proxy["response_time"] = response_time
                proxy["location"] = get_proxy_location(proxy["ip"])
                filtered_proxies.append(proxy)
                print(f"Proxy {proxy['ip']}:{proxy['port']} works! (Response Time: {response_time} seconds)")

                good_proxies_file.write(f"{proxy['ip']}:{proxy['port']}\n")

    # TODO: Implement filtering based on filter_type and value
    # For now, just printing the filtered_proxies
    print("Finished filtering proxies.")
    print(filtered_proxies)

def find_proxies():
    print('Finding proxies...')
    proxy_list = fetch_proxy_data()
    filter_proxies(proxy_list)

def main():
    print('1. Find and test proxies, keep working proxies')
    print('2. Find and test proxies, keep top % or # of working proxies')
    print('3. Test proxies in PROXIES.txt')
    print('4. Exit')
    option = input('Enter option: ')

    if option == '1':
        find_proxies()
    elif option == '2':
        print('1. Find and test proxies, keep fastest % of working proxies')
        print('2. Find and test proxies, keep fastest # of working proxies')
        option = input('Enter option: ')
        if option == '1':
            input_value = input('Enter %: ')
            find_proxies()
            filter_proxies(filter_type='%', value=input_value)
        elif option == '2':
            input_value = input('Enter #: ')
            find_proxies()
            filter_proxies(filter_type='#', value=input_value)
    elif option == '3':
        filter_proxies()
    else:
        print('Exiting...')
        sys.exit()

if __name__ == '__main__':
    main()
