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


class Scraper:
    def __init__(self, url, usr_data_dir='C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data'):
        self.url = url
        self.usr_data_dir = usr_data_dir
        self.soup = None
        self.title = None
        self.authors = []
        self.expr_list = []


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
        wait = WebDriverWait(driver, timeout=10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#MathJax-Element-1-Frame")))

        source = driver.page_source

        driver.quit()

        self.soup = BeautifulSoup(source, "html.parser")


    def scrape_title(self):
        self.title = self.soup.find('meta', {'name': 'citation_title'})['content']


    def scrape_authors(self):
        authors_first = self.soup.find("div", {"class": "AuthorGroups"}).findAll("span", {"class": "given-name"})
        authors_last = self.soup.find("div", {"class": "AuthorGroups"}).findAll("span", {"class": "surname"})
        total_authors = len(authors_first)

        for i in range(total_authors):
            self.authors.append('{fn} {ln}'.format(fn=authors_first[i].contents[0], ln=authors_last[i].contents[0]))


    def scrape_exprs(self):
        if not self.soup:
            raise NameError('The url is not parsed.')
        # found = soup.find_all('script', attrs={'type': 'math/tex; mode=display'})
        # found = soup.find_all('script', attrs={'id': 'MathJax-Element-a'})
        # found = soup.find_all('script', attrs={'id': 'MathJax-Element-1'})
        found = self.soup.find_all('script', attrs={'id': re.compile(r'^MathJax')})

        if found:
            return_value = True

            for expr in found:
                self.expr_list.append(expr.string)

            return True

        return False


    def get_title(self):
        print(self.title)


    def get_authors(self):
        print(self.authors)


    def get_exprs(self):
        idx = 1
        if self.expr_list:
            for expr in self.expr_list:
                expr = self.mml2tex(expr)

                if self.is_expr(expr):
                    print('Expression {idx}: {expr}'.format(idx=idx, expr=expr))
                    idx += 1

        else:
            print('No expressions were scraped')


    def generate_txt(self):
        self.scrape_title()
        self.scrape_authors()
        self.scrape_exprs()

        paper_id = self.url.split('/')[-1]
        with open('{}.txt'.format(paper_id), 'w', encoding='utf-8') as f:
            f.write('Title: {}\n'.format(self.title))
            f.write('Authors: {}\n'.format(', '.join(self.authors)))
            f.write('Math Expressions: \n')

            for expr in self.expr_list:
                expr = self.mml2tex(expr)

                if self.is_expr(expr):
                    f.write('{}\n'.format(expr))



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

scraper.generate_txt()
