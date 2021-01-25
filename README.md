# Webspray
Fuzz for hidden proxies, vhosts, and URLs

## Example 1: "Dirbust" across multiple hosts
NOTE: Webspray arguments accept any combination of strings and/or files containing strings
~~~
$ ./webspray.py ./evilcorp_hosts.txt --append /web.config.bak /robots.txt
~~~

## Example 2: Scan for hidden proxies by trying to visit an internal-only resource
TIP: You can specify the `--no-connect` option to skip the `CONNECT` HTTP method and send the request anyway
~~~
$ ./webspray.py http://intranet.evilcorp.local --proxies ./evilcorp_tcp_8080.txt
~~~

## Example 3: Scan for virtual hosts
~~~
$ ./webspray.py http://1.1.1.1 http://2.2.2.2 --vhosts ./evilcorp_vhosts.txt
~~~

## Combining these attacks, to infinity and beyond...
Any of the above attacks can be chained together.
![image](https://user-images.githubusercontent.com/20261699/97918182-b1dc5580-1d23-11eb-8e7d-13589239ab8a.png)

## Help
~~~
$ ./webspray.py --help
usage: webspray.py [-h] [-a APPEND [APPEND ...]] [-v VHOSTS [VHOSTS ...]] [-p PROXIES [PROXIES ...]] [-n] [-c COOKIES [COOKIES ...]] [-t THREADS] [-i IGNORE [IGNORE ...]]
                   [-s SAVE [SAVE ...]] [-m METHOD] [-T TIMEOUT] [-U USER_AGENT] [-d]
                   urls [urls ...]

Fuzz for hidden proxies, vhosts, and URLs

positional arguments:
  urls                  URLs

optional arguments:
  -h, --help            show this help message and exit
  -a APPEND [APPEND ...], --append APPEND [APPEND ...]
                        append these to the URLs
  -v VHOSTS [VHOSTS ...], --vhosts VHOSTS [VHOSTS ...]
                        try each of these virtual hosts
  -p PROXIES [PROXIES ...], --proxies PROXIES [PROXIES ...]
                        try against each of these proxies (proto://proxy:port) (if you're trying to proxy through Burp, use proxychains)
  -n, --no-connect      for each specified proxy, change the url path only (no CONNECT method)
  -c COOKIES [COOKIES ...], --cookies COOKIES [COOKIES ...]
                        cookies
  -t THREADS, --threads THREADS
                        threads
  -i IGNORE [IGNORE ...], --ignore IGNORE [IGNORE ...]
                        HTTP status codes to ignore (default: 301,302,400,401,403,404,500,502,503)
  -s SAVE [SAVE ...], --save SAVE [SAVE ...]
                        Save responses with these status codes (default: 200 only)
  -m METHOD, --method METHOD
                        HTTP method to use
  -T TIMEOUT, --timeout TIMEOUT
                        HTTP Timeout
  -U USER_AGENT, --user-agent USER_AGENT
                        Change User-Agent header (default: Windows 10 Chrome)
  -d, --debug           Be more annoying
~~~