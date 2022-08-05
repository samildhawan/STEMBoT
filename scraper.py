import os
import re
from bs4 import BeautifulSoup
from collections import OrderedDict
from lxml import etree
from lxml.builder import unicode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class Scraper:
    def __init__(self, url, usr_data_dir='C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data'):
        self.url = url
        self.usr_data_dir = usr_data_dir
        self.soup = None
        self.expr_list = []
        self.info = OrderedDict({
            'title': None,
            'authors': [],
            'url': url,
            'mathml_exprs': [],
            'tex_exprs': []
        })


    def is_expr(self, expr):
        signs = ['=', '<', '>', '≠', '≤', '≥']
        for sign in signs:
            if sign in expr:
                return True

        return False


    def mml2tex(self, expr):
        xslt_file = os.path.join('Converter', 'mmltex.xsl')
        dom = etree.fromstring(expr)
        xslt = etree.parse(xslt_file)
        transform = etree.XSLT(xslt)
        newdom = transform(dom)
        return unicode(newdom)


    def parse(self):
        service = Service(executable_path=ChromeDriverManager().install())

        # Load default profile
        options = webdriver.ChromeOptions()
        options.add_argument('user-data-dir={}'.format(self.usr_data_dir))

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(self.url)

        # wait
        try:
            wait = WebDriverWait(driver, timeout=10)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#MathJax-Element-1-Frame")))
        except:
            print('Timeout.')

        source = driver.page_source

        driver.quit()

        self.soup = BeautifulSoup(source, "html.parser")


    def scrape_title(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        self.info['title'] = self.soup.find('meta', {'name': 'citation_title'})['content']


    def scrape_authors(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        authors_first = self.soup.find("div", {"class": "AuthorGroups"}).findAll("span", {"class": "given-name"})
        authors_last = self.soup.find("div", {"class": "AuthorGroups"}).findAll("span", {"class": "surname"})
        total_authors = len(authors_first)

        if total_authors:
            for i in range(total_authors):
                self.info['authors'].append('{fn} {ln}'.format(fn=authors_first[i].contents[0], ln=authors_last[i].contents[0]))
        else:
            self.info['authors'] = None


    def scrape_exprs(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        exprs = self.soup.find_all('script', attrs={'id': re.compile(r'^MathJax')})

        if exprs:
            for expr in exprs:
                if self.is_expr(self.mml2tex(expr.string)):
                    self.info['mathml_exprs'].append(expr.string)
                    self.info['tex_exprs'].append(self.mml2tex(expr.string))
        else:
            self.info['mathml_exprs'] = None
            self.info['tex_exprs'] = None


    def get_title(self):
        return self.info['title']


    def get_authors(self):
        return self.info['authors']


    def get_mathml_exprs(self):
        return self.info['mathml_exprs']


    def get_tex_exprs(self):
        return self.info['tex_exprs']


    def generate_txt(self):
        paper_id = self.url.split('/')[-1]
        with open('scraped_txt\\{}.txt'.format(paper_id), 'w', encoding='utf-8') as f:
            f.write('Title: {}\n'.format(self.get_title()))
            f.write('Authors: {}\n'.format(', '.join(self.get_authors())))
            f.write('URL: {}\n'.format(self.url))

            f.write('Math Expressions in MathML: \n')
            for expr in self.get_mathml_exprs():
                f.write('{}\n'.format(expr))

            f.write('Math Expressions in TeX: \n')
            for expr in self.get_tex_exprs():
                f.write('{}\n'.format(expr))


    def scrape(self):
        self.scrape_title()
        self.scrape_authors()
        self.scrape_exprs()
        self.generate_txt()
        return self.info



scraper = Scraper(url='https://www.sciencedirect.com/science/article/pii/S2588840421000019',
                  usr_data_dir='C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data')

scraper.parse()

# scraper.scrape_title()
# scraper.get_title()
#
# scraper.scrape_authors()
# scraper.get_authors()
#
# scraper.scrape_exprs()
# scraper.get_exprs()

print(scraper.scrape())
