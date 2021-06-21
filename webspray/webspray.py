#!/usr/bin/env python3

import bs4
import sys
import time
import string
import logging
import argparse
import requests
import ipaddress
from .lib import logger
from pathlib import Path
#from concurrent.futures import ThreadPoolExecutor
from .lib.threadpool import ThreadPool

from urllib3.exceptions import InsecureRequestWarning
# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


log = logging.getLogger('webspray.cli')


default_headers = {}



class SprayResponse:

    def __init__(self, requests_response, vhost=None, proxy=None):

        self._response = requests_response
        self.vhost = vhost
        self.proxy = proxy


    @property
    def title(self):

        html = bs4.BeautifulSoup(self._response.text, 'lxml')
        try:
            return html.title.text.strip()
        except AttributeError:
            return ''


    def __getattr__(self, item):

        return getattr(self._response, item)


    def __str__(self):

        return '{:<4} {:<30} {:<30} {:<30} {:<30}'.format(
            self.status_code,
            self.title,
            self.url,
            (self.vhost if self.vhost else ''),
            (self.proxy if self.proxy else '')
        )



def get_lines(l):

    lines = set()

    for entry in l:
        try:
            with open(entry) as f:
                for line in f:
                    lines.add(line.strip())
        except (OSError, TypeError):
            lines.add(entry)

    return list(lines)



def get_urls(l):

    urls = set()

    for entry in l:
        try:
            with open(entry) as f:
                for line in f:
                    urls.add(line.strip())
        except OSError:
            urls.add(entry)

    validated_urls = set()
    for url in urls:
        for u in line_to_url(url):
            validated_urls.add(u)

    return list(validated_urls)


def line_to_url(l):

    urls = []

    try:
        ip_network = ipaddress.ip_network(l)
        for ip in ip_network:
            yield f'http://{ip}/'
            yield f'https://{ip}/'

    except ValueError:
        if not any([l.lower().startswith(x) for x in ['http://', 'https://']]):
            yield f'http://{l}'
            yield f'https://{l}'
        else:
            yield l



def save_response(response, vhost):

    if vhost is None:
        vhost = ''

    allowed_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_-.'

    save_dir = Path.home() / '.webspray' / 'responses'
    save_dir.mkdir(exist_ok=True)

    file_name = f'{int(time.time())}_{vhost}_' + ''.join([c for c in response.url.replace('/', '_').replace(':', '_') if c in allowed_chars]).replace('__', '_')
    if len(file_name) > 100:
        file_name = file_name[:50] + '...' + file_name[-50:]

    save_name = save_dir / file_name

    log.debug(f'Saving {response.url} to {save_name}')

    with open(save_name, 'w') as f:
        for header,value in response.headers.items():
            f.write(f'{header}: {value}\n')
        f.write(f'\n{response.text}')



class CustomPreparedRequest(requests.PreparedRequest):
    '''
    Custom class for modifying the path_url attribute
    '''
    def __init__(self, *args, **kwargs):
        self._path_url = kwargs.pop('path_url', None)
        super().__init__(*args, **kwargs)

    @property
    def path_url(self):
        return self._path_url


class CustomRequest(requests.Request):
    '''
    Custom class for modifying the path_url attribute
    '''
    def prepare(self, path_url):
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for transmission and returns it."""
        p = CustomPreparedRequest(path_url=path_url)
        p.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            files=self.files,
            data=self.data,
            json=self.json,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
            hooks=self.hooks,
        )
        return p


def visit_url(url, options, vhost=None, proxy=None):

    headers = dict()

    if vhost is not None:
        headers = {
            'Host': vhost
        }
    else:
        headers = dict()
    headers.update(default_headers)

    if proxy is not None:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    else:
        proxies = None

    try:

        if options.no_connect:

            if 'Host' not in headers:
                headers['Host'] = requests.utils.urlparse(url).netloc

            session = requests.Session()
            prepped_request = CustomRequest(
                options.method,
                proxy,
                cookies=options.cookies,
                headers=headers,
            ).prepare(path_url=url)

            response = session.send(
                prepped_request,
                timeout=options.timeout,
                allow_redirects=False,
                verify=False,
            )


        else:
            response = requests.request(
                options.method,
                url,
                cookies=options.cookies,
                headers=headers,
                timeout=options.timeout,
                allow_redirects=False,
                verify=False,
                proxies=proxies
            )

        log.info(str(SprayResponse(response, vhost=vhost, proxy=proxy)))

        #if response.status_code not in options.ignore:
        #    log.info(f'{response.status_code} / {len(response.text):09d} / {(proxy if proxy else "")} / {title}: {url}')
        #else:
        #    log.debug(f'{response.status_code} / {len(response.text):09d} / {(proxy if proxy else "")} / {title}: {url}')
        if response.status_code in options.save:
            save_response(response, vhost)

    except requests.exceptions.RequestException as e:
        log.debug(f'Error in request: {e}')

    except Exception as e:
        import traceback
        log.error(traceback.format_exc())

    except KeyboardInterrupt:
        log.error('Thread interrupted')
        raise


def main(options):

    with ThreadPool(max_workers=options.threads) as pool:
        for append in options.append:
            for url in options.targets:
                for proxy in options.proxies:
                    for vhost in options.vhosts:
                        pool.submit(visit_url, f'{url}{append}', options, vhost=vhost, proxy=proxy)


def go():

    default_user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
    default_ignore = [301,302,400,401,403,404,500,502,503]
    default_save = [200]

    parser = argparse.ArgumentParser(description='Fuzz for hidden proxies, vhosts, and URLs')
    parser.add_argument('targets', nargs='+', help='target hosts or URLs (accepts CIDR notation)')
    parser.add_argument('-a', '--append', nargs='+', default=[''], help='append these to the URLs')
    parser.add_argument('-v', '--vhosts', nargs='+', default=[None], help='try each of these virtual hosts')
    parser.add_argument('-p', '--proxies', nargs='+', default=[None], help='try against each of these proxies (proto://proxy:port) (if you\'re trying to proxy through Burp, use proxychains)')
    parser.add_argument('-n', '--no-connect', action='store_true', help='for each specified proxy, change the url path only (no CONNECT method)')
    parser.add_argument('-c', '--cookies', nargs='+', default={}, help='cookies')
    parser.add_argument('-t', '--threads', type=int, default=10, help='threads')
    parser.add_argument('-i', '--ignore', nargs='+', type=int, default=default_ignore, help=f'HTTP status codes to ignore (default: {",".join([str(i) for i in default_ignore])})')
    parser.add_argument('-s', '--save', type=int, nargs='+', default=default_save, help='Save responses with these status codes (default: 200 only)')
    parser.add_argument('-m', '--method', default='GET', help='HTTP method to use')
    parser.add_argument('-T', '--timeout', type=float, default=10.0, help='HTTP Timeout')
    parser.add_argument('-U', '--user-agent', default=default_user_agent, help='Change User-Agent header (default: Windows 10 Chrome)')
    parser.add_argument('-d', '--debug', action='store_true', help='Be more annoying')

    # log everything
    logging.getLogger('webspray').setLevel(logging.INFO)

    try:

        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(0)
        else:
            log.info(f'Logging to: {logger.logdir}')

        options = parser.parse_args()

        if options.debug:
            logging.getLogger('webspray').setLevel(logging.DEBUG)

        # log full command
        log.info(f'Full command: {" ".join(sys.argv)}')

        # handle proxies
        options.proxies = get_lines(options.proxies)
        log.info(f'Proxies: {len(options.proxies)}')

        # handle threads
        log.info(f'Threads: {options.threads}')

        # handle saves
        log.info(f'Saving status codes "{" ".join([str(s) for s in options.save])}" in ~/.webspray/responses')

        # handle urls
        options.targets = get_urls(options.targets)
        log.info(f'URLs: {len(options.targets):,}')

        # handle urls
        options.vhosts = get_lines(options.vhosts)
        log.info(f'Virtual Hosts: {len(options.vhosts):,}')

        # handle suffixes
        options.append = get_lines(options.append)
        log.info(f'Appending: {len(options.append):,}')

        # handle cookies
        if options.cookies:
            log.info('Using cookies:')
            cookies = {}
            for c in options.cookies:
                for cookie in c.split(';'):
                    try:
                        k,v = [x.strip() for x in cookie.split('=', 1)]
                        cookies[k] = v
                        log.info(f'    {k}')
                    except ValueError as e:
                        log.error(f'Error setting cookie: {e}')
                        continue
            options.cookies = cookies

        # handle user-agent
        default_headers.update({
            'User-Agent': options.user_agent
        })

        main(options)


    except argparse.ArgumentError as e:
        log.error(e)
        log.error('Check your syntax')
        sys.exit(2)

    except KeyboardInterrupt:
        log.critical('Interrupted')
        sys.exit(1)


if __name__ == '__main__':
    go()