import bs4
import os
import re
from collections import OrderedDict
from converter import Converter
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
        self.converter = Converter()
        self.expr_list = []
        self.info = OrderedDict({
            'title': None,
            'authors': [],
            'url': url,
            'var_dict': {},
            'mathml_exprs': [],
            'tex_exprs': [],
            'ascii_exprs': [],
            'python_exprs': []
        })


    def _is_expr(self, expr):
        signs = ['=', '<', '>', '≠', '≤', '≥', r'\le ', r'\leq ', r'\leqq ', r'\leqslant ', r'\ge ', r'\geq ', r'\geqq ', r'\geqslant ']
        for sign in signs:
            if sign in expr:
                return True

        return False


    # def _mml2tex(self, expr):
    #     xslt_file = os.path.join('mml2tex', 'mmltex.xsl')
    #     dom = etree.fromstring(expr)
    #     xslt = etree.parse(xslt_file)
    #     transform = etree.XSLT(xslt)
    #     newdom = transform(dom)
    #     return unicode(newdom)


    def parse(self):
        service = Service(executable_path=ChromeDriverManager().install())

        # Load default profile
        options = webdriver.ChromeOptions()
        options.add_argument('user-data-dir={}'.format(self.usr_data_dir))

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(self.url)

        # wait
        try:
            wait = WebDriverWait(driver, timeout=5)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#MathJax-Element-1-Frame")))
        except Exception as e:
            print('Timeout.')

        source = driver.page_source

        driver.quit()

        self.soup = bs4.BeautifulSoup(source, "html.parser")


    def _scrape_title(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        self.info['title'] = self.soup.find('meta', {'name': 'citation_title'})['content']


    def _scrape_authors(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        authors_first = self.soup.find('div', {'class': 'AuthorGroups'}).find_all('span', {'class': 'given-name'})
        authors_last = self.soup.find('div', {'class': 'AuthorGroups'}).find_all('span', {'class': 'surname'})
        total_authors = len(authors_first)

        if total_authors:
            for i in range(total_authors):
                self.info['authors'].append('{fn} {ln}'.format(fn=authors_first[i].contents[0], ln=authors_last[i].contents[0]))
        else:
            self.info['authors'].append('Unknown')


    def _scrape_table(self):
        tables = self.soup.find_all('table')
        for table in tables:
            variables = [variable.contents for variable in table.thead.tr.find_all('th')]
            values = [value.contents[0] for value in table.tbody.tr.find_all('td')]

            # print(variables)
            # print(values)

            for i in range(len(variables)):
                try:
                    float(values[i])
                except ValueError:
                    continue

                # name, unit, value = '', '', float(values[i])

                if isinstance(variables[i][0], bs4.element.Tag):
                    # replace mathml with python
                    mathml = variables[i][0].find('script', attrs={'id': re.compile(r'^MathJax')})
                    # print(mathml)
                    if mathml:
                        mathml_expr = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + mathml.contents[0][6:]
                        tex_expr = self.converter.mml2tex(mathml_expr)
                        ascii_expr = self.converter.tex2ascii(tex_expr)
                        # python_expr = self.converter.ascii2python(ascii_expr)
                        variables[i][0] = ascii_expr

                variables[i] = [str(v) for v in variables[i]]

                expr = ''.join(variables[i])

                # separate units
                if expr[-1] == ')':
                    idx = expr.rfind(' (')
                    if idx <= 0:
                        name = expr
                        unit = 'Unknown'
                    else:
                        name = expr[:idx]
                        unit = expr[idx+1:]
                else:
                    name = expr
                    unit = 'Unknown'

                name = self.converter.name_post(name)
                unit = self.converter.unit_post(unit)

                self.info['var_dict'][' '.join([name, unit])] = float(values[i])

            # print(variables)
            # print(values)


    def _scrape_exprs(self):
        if not self.soup:
            raise NameError('The url is not parsed.')

        exprs = self.soup.find_all('script', attrs={'id': re.compile(r'^MathJax')})
        # tex2ascii = Tex2ASCIIMath()

        if exprs:
            for expr in exprs:
                mathml_expr = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + expr.contents[0][6:]
                tex_expr = self.converter.mml2tex(mathml_expr)
                if self._is_expr(tex_expr):
                    self.info['mathml_exprs'].append(mathml_expr)
                    # print('TeX: {}'.format(tex_expr))
                    self.info['tex_exprs'].append(tex_expr)
                    ascii_expr = self.converter.tex2ascii(tex_expr)
                    # print('ASCII: {}'.format(ascii_expr))
                    self.info['ascii_exprs'].append(ascii_expr)
                    python_expr = self.converter.ascii2python(ascii_expr)
                    # print('Python: {}'.format(python_expr))
                    self.info['python_exprs'].append(python_expr)
        else:
            self.info['mathml_exprs'] = None
            self.info['tex_exprs'] = None
            self.info['ascii_exprs'] = None
            self.info['python_exprs'] = None


    def get_title(self):
        return self.info['title']


    def get_authors(self):
        return self.info['authors']


    def get_var_dict(self):
        return self.info['var_dict']


    def get_mathml_exprs(self):
        return self.info['mathml_exprs']


    def get_tex_exprs(self):
        return self.info['tex_exprs']


    def get_ascii_exprs(self):
        return self.info['ascii_exprs']


    def get_python_exprs(self):
        return self.info['python_exprs']


    def _generate_txt(self):
        paper_id = self.url.split('/')[-1]
        if not os.path.exists('scraped_txt'):
            os.mkdir('scraped_txt')

        with open('scraped_txt\\{}.txt'.format(paper_id), 'w', encoding='utf-8') as f:
            f.write('Title: {}\n'.format(self.get_title()))
            f.write('Authors: {}\n'.format(', '.join(self.get_authors())))
            f.write('URL: {}\n'.format(self.url))

            f.write('\nMath Expressions in MathML: \n')
            for expr in self.get_mathml_exprs():
                f.write('{}\n'.format(expr))

            f.write('\nMath Expressions in TeX: \n')
            for expr in self.get_tex_exprs():
                f.write('{}\n'.format(expr))

            f.write('\nMath Expressions in ASCII: \n')
            for expr in self.get_ascii_exprs():
                f.write('{}\n'.format(expr))

            f.write('\nMath Expressions in Python: \n')
            for expr in self.get_python_exprs():
                f.write('{}\n'.format(expr))


    def _generate_python(self):
        paper_id = self.url.split('/')[-1]
        if not os.path.exists('scraped_python'):
            os.mkdir('scraped_python')

        with open('scraped_python\\{}.py'.format(paper_id), 'w', encoding='utf-8') as f:
            # import libraries
            f.write('import numpy as np\n')
            f.write('\n')

            # write variables
            for var in self.get_var_dict():
                temp = var.split(' ')
                name = temp[0]
                unit = ' '.join(temp[1:])
                f.write('# {} (unit={})\n'.format(name, unit))
                f.write('{} = {}\n'.format(name, self.get_var_dict()[var]))
            f.write('\n')

            for expr in self.get_python_exprs():
                f.write('{}\n'.format(expr))


    def scrape(self):
        self._scrape_table()
        self._scrape_title()
        self._scrape_authors()
        self._scrape_exprs()
        self._generate_txt()
        self._generate_python()
        return self.info



scraper = Scraper(url='https://www.sciencedirect.com/science/article/pii/S0924013617301334',
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

scraper.scrape()

print(scraper.get_var_dict())
print(scraper.get_python_exprs())

# for idx, expr in enumerate(scraper.get_tex_exprs()):
#     print(idx, expr)
#
#     try:
#         c = Converter()
#         print(c.tex2ascii(expr))
#     except Exception as e:
#         print('WRONG!!!!!!!!!!')
#         print(e)
#
#     print()

# tex_exprs = scraper.get_tex_exprs()
# ascii_exprs = scraper.get_ascii_exprs()
# for idx in range(len(tex_exprs)):
#     print('{}. TeX: {}'.format(idx, tex_exprs[idx]))
#     print('ASCII: {}'.format(ascii_exprs[idx]))

# with open('paper_url.txt', 'r', encoding='utf-8') as f:
#     urls = f.readlines()
#     for url in urls:
#         print(url[:-1])
#         scraper = Scraper(url=url[:-1],
#                           usr_data_dir='C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data')
#
#         scraper.parse()
#         scraper.scrape()
