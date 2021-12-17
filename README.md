# ScreenConnect-UserEnum

ScreenConnect 6.3.13446.6374-2666439717 user enumeration tool

## How To
~~~
usage: screenconnect_userenum.py [-h] [-c cnt] [-v] [-s] [-p P] url wordlist

http://example.com/Login user enumeration tool

positional arguments:
  url         http://example.com/Login
  wordlist    username wordlist

optional arguments:
  -h, --help  show this help message and exit
  -c cnt      process (thread) count, default 10, too many processes may cause connection problems
  -v          verbose mode
  -s          stop on first user found
  -p P        proxy
~~~


example: python3 screenconnect_userenum.py  -p socks5://127.0.0.1:9050 -v http://example.com/Login user.txt
