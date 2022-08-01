import os
import re
from bs4 import BeautifulSoup
from lxml import etree
from lxml.builder import unicode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager



url = 'https://www.sciencedirect.com/science/article/pii/S0749641918304856'
user_data_dir = 'C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data'
expr_list = []


def parse(url, user_data_dir):
    service = Service(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('user-data-dir=' + user_data_dir)

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    # cookies = {
    #     'EUID': 'a14ede68-a2e9-405b-92a2-d0d0269d7573',
    #     'mboxes': '%7B%22corporate-sign-in%22%3A%7B%22variation%22%3A%22%232%22%2C%22enabled%22%3Atrue%7D%7D',
    #     'utt': '518522c91c5528188a1e0e3-19d74522339c6c21',
    #     'acw': '93287acb8eae9742142970d2a3f3915a559cgxrqb%7C%24%7C574911598340AC3D6D952140709A6A6D28658A9DD1F9B38212525DE0AA1C05E5413D5CE5132BE64C4E828145E875EF258F3EE9BB8062CC870E9169905BBD791CB0469A67597464825D387A21AFA2E514',
    #     'has_multiple_organizations': 'false',
    #     'fingerPrintToken': '445a3a5f30ee0a0d480dc7d11d6f374c',
    #     'AMCVS_4D6368F454EC41940A4C98A6%40AdobeOrg': '1',
    #     'sd_access': 'eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..MRTXAT4bYf2cH55FVLZF5A.x-gzh9c7jOjH7gL6p50W-NgUSUbUtmV6mbj7w3qe47nq0uyHrhqwtdMRzKSGt7nSRcZO5bS-CUCGvE-FwCtUHxvFyhQpbhS5vA6Zk8Wk0SY2rEiEi-wxZwC8Rz7PSSk7bwLRn9oiLA581fS1iu4Qdw.xmDGmQTngU-CYSiVNk6KVA',
    #     'sd_session_id': 'eea0df812a84e34d802a27c8edc1ab1a27f5gxrqb',
    #     'id_ab': 'IDP',
    #     'wasShibboleth': 'true',
    #     'AMCV_4D6368F454EC41940A4C98A6%40AdobeOrg': '-2121179033%7CMCIDTS%7C19206%7CMCMID%7C87227847617155765904403905662509717686%7CMCAID%7CNONE%7CMCOPTOUT-1659335649s%7CNONE%7CMCAAMLH-1659933249%7C6%7CMCAAMB-1659933249%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCCIDH%7C-2101185554%7CMCSYNCSOP%7C411-19213%7CvVersion%7C5.3.0',
    #     'mbox': 'session%23fa94af74ad594157a779925594d96583%231659331858%7CPC%238a4607b97fa0485ea95ad4a5bb35c7ab.37_0%231722574798',
    #     '__cf_bm': 'VtznrdtOtniJMWEnu9Rk1clZRyb_ChE913GD7RM4h0U-1659329997-0-Abz7VrofaaomAbfUxjVDqPYcgP8MggL0k76o6+94PiIV5wHYkEpJGOIoon/AuVQENlfKIp11guO1U29FgIGwq01B84iBas3as+vJcdCG0I3L',
    #     'MIAMISESSION': '9a07eb94-28aa-48f3-9fb5-0696c994ecd2:3836782805',
    #     'SD_REMOTEACCESS': 'eyJhY2NvdW50SWQiOiIxMTI3OSIsInRpbWVzdGFtcCI6MTY1OTMzMDAwNTY3MX0=',
    #     's_pers': '%20c19%3Dsd%253Aproduct%253Ajournal%253Aarticle%7C1659331807540%3B%20v68%3D1659330005882%7C1659331807546%3B%20v8%3D1659330007551%7C1753938007551%3B%20v8_s%3DLess%2520than%25201%2520day%7C1659331807551%3B',
    #     's_sess': '%20s_cpc%3D0%3B%20s_ppvl%3Dsd%25253Aproduct%25253Ajournal%25253Aarticle%252C20%252C15%252C5236%252C2048%252C1042%252C2048%252C1152%252C1.25%252CP%3B%20e41%3D1%3B%20s_cc%3Dtrue%3B%20s_ppv%3Dsd%25253Aproduct%25253Ajournal%25253Aarticle%252C3%252C3%252C1042%252C2048%252C214%252C2048%252C1152%252C1.25%252CP%3B',
    # }
    #
    # for name, value in cookies.items():
    #     driver.add_cookie({'name': name, 'value': value})

    # wait
    wait = WebDriverWait(driver, timeout=10)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#MathJax-Element-1-Frame")))

    source = driver.page_source

    driver.quit()

    soup = BeautifulSoup(source, "html.parser")
    return soup


def scrape(soup):
    # found = soup.find_all('script', attrs={'type': 'math/tex; mode=display'})
    # found = soup.find_all('script', attrs={'id': 'MathJax-Element-a'})
    # found = soup.find_all('script', attrs={'id': 'MathJax-Element-1'})
    found = soup.find_all('script', attrs={'id': re.compile(r'^MathJax')})

    if found:
        return_value = True

        for expr in found:
            expr_list.append(expr.string)

        return True

    return False


def mml2tex(expr):
    xslt_file = os.path.join('Converter', 'mmltex.xsl')
    dom = etree.fromstring(expr)
    xslt = etree.parse(xslt_file)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)
    return unicode(newdom)


def get_expressions():
    if expr_list:
        for idx, expr in enumerate(expr_list):
            print('Expression {idx}: {expr}'.format(idx=idx, expr=mml2tex(expr)))

    else:
        print('No expressions were scraped')


soup = parse(url, user_data_dir)
scrape(soup)

# for expr in expr_list:
#     print('MathML: {}'.format(expr))
#     print('TeX: {}'.format(mml2tex(expr)))
#     print('')

get_expressions()
