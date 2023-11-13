import os
import re
from collections import OrderedDict

import bs4
import torch

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from converter import Converter


class Scraper:
    def __init__(self, url,
                 usr_data_dir='Users/samildhawan/Library/Application Support/Google/Chrome/User Data/Default'):
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
        """Returns a boolean expression if <expr> contains any mathematical
        comparison signs or symbols. If any are found, return True as it
        indicates a valid mathematical expression"""
        signs = ['=', '<', '>', '≠', '≤', '≥', r'\le ', r'\leq ', r'\leqq ',
                 r'\leqslant ', r'\ge ', r'\geq ', r'\geqq ', r'\geqslant ']
        for sign in signs:
            if sign in expr:
                return True

        return False

    def parse(self):
        """Parses a webpage and creates a BeautifulSoup object for
        further HTML processing"""
        service = Service(executable_path=ChromeDriverManager().install())

        # Load default profile
        options = webdriver.ChromeOptions()
        options.add_argument(f"--usr_data_dir={self.usr_data_dir}")
        options.add_argument("profile-directory=Default")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get(self.url)

        # wait
        try:
            wait = WebDriverWait(driver, timeout=5)
            wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "#MathJax-Element-1-Frame")))
        except Exception as e:
            print('Timeout.')

        source = driver.page_source

        driver.quit()

        self.soup = bs4.BeautifulSoup(source, "html.parser")

    def _scrape_title(self):
        """Scrapes the title of the parsed webpage modifying the
        self.info['title'] attribute directly"""
        if not self.soup:
            raise NameError('The url is not parsed.')

        self.info['title'] = self.soup.find('meta', {'name': 'citation_title'})[
            'content']

    def _scrape_authors(self):
        """Scrapes the authors of the academic journal, modifying
        the self.info['authors'] attribute directly"""
        if not self.soup:
            raise NameError('The url is not parsed.')

        authors_first = self.soup.find('div',
                                       {'class': 'AuthorGroups'}).find_all(
            'span', {'class': 'given-name'})
        authors_last = self.soup.find('div',
                                      {'class': 'AuthorGroups'}).find_all(
            'span', {'class': 'surname'})
        total_authors = len(authors_first)

        if total_authors:
            for i in range(total_authors):
                self.info['authors'].append(
                    '{fn} {ln}'.format(fn=authors_first[i].contents[0],
                                       ln=authors_last[i].contents[0]))
        else:
            self.info['authors'].append('Unknown')

    def _scrape_table(self):
        """Scrapes the tables in the academic journal, extracting each of the
        variables in the table header and the corresponding values in the table
        body, handling cases where the variables span multiple rows and
        separates units from the variable names. This method modifies the
        self.info['var_dict'] attribute directly."""
        tables = self.soup.find_all('table')
        for table in tables:
            print(table)
            variables = [variable.contents for variable in
                         table.thead.tr.find_all('th') if variable.contents]
            values = []
            trs = table.tbody.find_all('tr')

            next = False
            for tr in trs:
                if next:
                    variables += [variable.contents for variable in
                                  tr.find_all('td') if variable.contents]
                    # print(variables)
                    next = False
                else:
                    values += [value.contents[0] for value in tr.find_all('td')
                               if value.contents]
                    # print(values)
                    next = True

            # print(variables)
            # print(values)

            if len(variables) != len(values):
                continue

            for i in range(len(variables)):
                try:
                    float(values[i])
                except ValueError:
                    continue

                # name, unit, value = '', '', float(values[i])
                # print(variables[i])

                if isinstance(variables[i][0], bs4.element.Tag):
                    # replace mathml with python
                    mathml = variables[i][0].find('script', attrs={
                        'id': re.compile(r'^MathJax')})
                    # print(mathml)
                    if mathml:
                        mathml_expr = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + \
                                      mathml.contents[0][6:]
                        tex_expr = self.converter.mml2tex(mathml_expr)[0]
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
                        unit = expr[idx + 1:]
                else:
                    name = expr
                    unit = 'Unknown'

                name = self.converter.name_post(name)
                unit = self.converter.unit_post(unit)

                if not name[0].isdigit():
                    self.info['var_dict'][' '.join([name, unit])] = float(
                        values[i])

            # print(variables)
            # print(values)
            # print(self.info['var_dict'])

    def _scrape_exprs(self):
        """Extracts mathematical expressions with an id attribute from the
        parsed web page. It then converts the MathML expressions to TeX, ASCII,
        and Python representations based on the converter.py."""
        if not self.soup:
            raise NameError('The url is not parsed.')

        exprs = self.soup.find_all('script',
                                   attrs={'id': re.compile(r'^MathJax')})
        var_list = [var.split(' ')[0] for var in self.get_var_dict()] + ['y']
        # tex2ascii = Tex2ASCIIMath()

        if exprs:
            for expr in exprs:
                mathml_expr = '<math xmlns="http://www.w3.org/1998/Math/MathML">' + \
                              expr.contents[0][6:]
                tex_exprs = self.converter.mml2tex(mathml_expr)
                for tex_expr in tex_exprs:
                    # print(tex_expr)
                    # print(self._is_expr(tex_expr))
                    if self._is_expr(tex_expr):
                        self.info['mathml_exprs'].append(mathml_expr)
                        print('TeX: {}'.format(tex_expr))
                        self.info['tex_exprs'].append(tex_expr)
                        ascii_expr = self.converter.tex2ascii(tex_expr)
                        print('ASCII: {}'.format(ascii_expr))
                        self.info['ascii_exprs'].append(ascii_expr)
                        python_expr = self.converter.ascii2python(ascii_expr,
                                                                  var_list)
                        print('Python: {}\n'.format(python_expr))
                        self.info['python_exprs'].append(python_expr)
                        var_list.append(python_expr.split(' = ')[0])
        else:
            self.info['mathml_exprs'] = None
            self.info['tex_exprs'] = None
            self.info['ascii_exprs'] = None
            self.info['python_exprs'] = None

    def _scrape_inline_exprs(self):
        """Extracts mathematical expressions defined in paragraphs of the parsed
        webpage"""

        if not self.soup:
            raise NameError('The url is not parsed.')
        exprs = self.soup.select('p')
        exprs = str(exprs)
        exprs = re.sub(r'\s', ' ', exprs)
        var_list = [var.split(' ')[0] for var in self.get_var_dict()] + ['y']

        explicit_variable = re.findall("\B<em>\w</em> = \d+\.?\d*", exprs)
        subscripted_variable = re.findall(
            "\B<em>\w</em><sub><em>\w</em></sub> = <em>\w</em><sub>\w</sub>",
            exprs)
        variable_with_subscript = re.findall(
            "\B<em>\w</em> = <em>\w</em><sub><em>\w</em></sub>", exprs)
        complex_expression = re.findall(
            "\B<em>\w</em><sub><em>\w</em></sub> = <em>\w</em><sub><em>\w</em></sub>",
            exprs)
        custom_char_pattern = re.findall("\B<em>\w</em><sub>\w</sub> = [^,]*", exprs)
        complete_list = explicit_variable + subscripted_variable + variable_with_subscript + complex_expression + custom_char_pattern

        # expression_pattern = variable_name
        full_list = []
        for lst in complete_list:
            clean = re.compile('<.*?>')
            new_list = [re.sub(clean, '', lst)]
            for new_lst in new_list:
                if new_lst not in full_list:
                    full_list += new_list

        for exp in full_list:
            if self._is_expr(exp):
                # tex_expr = self.converter.tex2ascii(tex_expr)
                # print('TeX: {}'.format(tex_expr))
                # self.info['tex_exprs'].append(tex_expr)
                # ascii_expr = self.converter.tex2ascii(tex_expr)
                # print('ASCII: {}'.format(ascii_expr))
                # self.info['ascii_exprs'].append(ascii_expr)
                print('Python: {}\n'.format(exp))
                self.info['python_exprs'].append(exp)
                var_list.append(exp.split(' = ')[0])

            else:
                self.info['mathml_exprs'] = None
                self.info['tex_exprs'] = None
                self.info['ascii_exprs'] = None
                self.info['python_exprs'] = None

    def _scrape_scientific_constants(self):
        """Extracts scientific constants defined in the paragraphs of the parsed
        webpage"""

        if not self.soup:
            raise NameError('The url is not parsed.')
        paragraphs = self.soup.select('p')
        paragraphs = str(paragraphs)
        paragraphs = re.sub(r'\s', ' ', paragraphs)
        var_list = [var.split(' ')[0] for var in self.get_var_dict()] + ['y']
        ordinary_constant = re.findall("\B<em>\w</em> is ", paragraphs)
        subscripted_constant = re.findall(
            "\B<em>\w</em><sub><em>\w</em></sub> is ",
            paragraphs)
        variable_with_subscript_constant = re.findall("\B<em>\w</em><sub>\w</sub> is ", paragraphs)
        constants_name = ordinary_constant + subscripted_constant + variable_with_subscript_constant
        print(constants_name)

        # constants_mapping = {}
        # for constant_name in constants_name:
        #     clean = re.compile('<.*?>')
        #     clean_name = re.sub(clean, '', constant_name)
        #     print(clean_name)

    def _substitute_values(self):
        """Substitutes dictionary values in equations list.
        Returns the list of equations with the dictionary values substituted.
        """
        updated_dict = {}
        for key, value in self.info['var_dict'].items():
            key = key.split()[0]  # Keep only the first word
            updated_dict[key] = value
        for index, equation in enumerate(self.info['python_exprs']):
            for key, value in updated_dict.items():
                equation = re.sub(r'(?<!\w){}(?!\w)'.format(key), str(value),
                                  equation)
            self.info['python_exprs'][index] = equation
        return self.info['python_exprs']

        # for index, equation in enumerate(equations):
        #     for key, value in dictionary.items():
        #         equation = re.sub(r'(?<!\w){}(?!\w)'.format(key), str(value),
        #                           equation)
        #     equations[index] = equation
        # return equations

    def particle_swarm_optimization(x):
        """This function hasn't been complete and needs to be adapted for
        the project. Function does a particle swarm optimization for
        values/equations which have unknown quantities and attempts to return
        accurate values for those values/equations.
        """
        k, K, n1, B, A, C, n2, E = x
        ep, R, rho, sigma = 0, 0, 1e-20, 0
        k, K, n1, B, A, C, n2, E = 21.5e6, 35e6, 5, 28.5e6, 0.28, 0.1, 1.8, 0.8e10

        etotalrate = 1
        ep = abs((sigma - R - k) / K) ** n1
        R = 0.5 * B / (rho ** 0.5) * (
                A * (1 - rho) * abs((sigma - R - k) / K) ** n1) - (
                    C * (rho ** n2))
        rho = (A * (1 - rho) * abs((sigma - R - k) / K) ** n1) - (
                C * (rho ** n2))
        sigma = E * (etotalrate - abs((sigma - R - k) / K) ** n1)

        return ep, R, rho, sigma

    def get_title(self):
        """Returns the title of the webpage"""
        return self.info['title']

    def get_authors(self):
        """Returns a list of strings of the authors from the webpage"""
        return self.info['authors']

    def get_var_dict(self):
        """Returns a dictionary containing the variables and their values
        extracted from the parsed web page."""
        return self.info['var_dict']

    def get_mathml_exprs(self):
        """Returns the list of MathML expressions extracted from the
        parsed web page."""
        return self.info['mathml_exprs']

    def get_tex_exprs(self):
        """Returns the list of TeX expressions extracted from the
        parsed web page."""
        return self.info['tex_exprs']

    def get_ascii_exprs(self):
        """Returns the list of ASCII expressions extracted from the
        parsed web page."""
        return self.info['ascii_exprs']

    def get_python_exprs(self):
        """Returns the list of Python expressions extracted from the
        parsed web page."""
        return self.info['python_exprs']

    def _generate_txt(self):
        """Writes the scraped information to a text file."""
        paper_id = self.url.split('/')[-1]
        if not os.path.exists('scraped_txt'):
            os.mkdir('scraped_txt')

        with open('scraped_txt\\{}.txt'.format(paper_id), 'w',
                  encoding='utf-8') as f:
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
        """Generates a Python file with the scraped information."""
        paper_id = self.url.split('/')[-1]
        if not os.path.exists('scraped_python'):
            os.mkdir('scraped_python')

        file_data = []
        with open('template.py', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                file_data.append(line)

        with open('scraped_python\\{}.py'.format(paper_id), 'w',
                  encoding='utf-8') as f:
            for line in file_data:
                # print(repr(line))
                f.write(line)

                # if 'All libraries go here' in line:
                #     # import libraries
                #     f.write('import numpy as np\n')
                #     f.write('import pandas as pd\n')
                #     f.write('rom matplotlib import pyplot as plt\n')
                #     f.write('from sympy import Symbol, Eq, solve\n')
                #     f.write('\n')

                if 'All equation parameters go here' in line:
                    # write variables
                    for var in self.get_var_dict():
                        temp = var.split(' ')
                        name = temp[0]
                        unit = ' '.join(temp[1:])
                        f.write('# {} (unit={})\n'.format(name, unit))
                        f.write(
                            '{} = {}\n'.format(name, self.get_var_dict()[var]))
                    f.write('\n')

                    for expr in self.get_python_exprs():
                        var = expr.split(' = ')[0]
                        f.write('{} = Symbol("{}")\n'.format(var, var))
                    # f.write('\n')

                elif 'All equations go here' in line:
                    # write expressions
                    f.write('    exprs = [\n')
                    for expr in self.get_python_exprs():
                        left, right = expr.split(' = ')
                        f.write('        Eq({}, {}),\n'.format(left, right))
                    f.write('    ]\n')
                    # f.write('\n')

                    # f.write('    sol = solve(exprs)\n')
                    # f.write('\n')
                    #
                    # f.write('    for key, val in sol.items():\n')
                    # f.write('        exec("{} = {}".format(key, val))\n')

    def _generate_python_test(self):
        """Generates a Python test file with the scraped information."""
        paper_id = self.url.split('/')[-1]
        if not os.path.exists('scraped_python'):
            os.mkdir('scraped_python')

        with open('scraped_python\\{}_test.py'.format(paper_id), 'w',
                  encoding='utf-8') as f:
            # import libraries
            f.write('import numpy as np\n')
            f.write('from sympy import Symbol, Eq, solve\n')
            f.write('\n')

            # write variables
            for var in self.get_var_dict():
                temp = var.split(' ')
                name = temp[0]
                unit = ' '.join(temp[1:])
                f.write('# {} (unit={})\n'.format(name, unit))
                f.write('{} = {}\n'.format(name, self.get_var_dict()[var]))
            f.write('\n')

            # write expressions
            for expr in self.get_python_exprs():
                var = expr.split(' = ')[0]
                f.write('{} = Symbol("{}")\n'.format(var, var))
            f.write('\n')

            f.write('exprs = [\n')
            for expr in self.get_python_exprs():
                left, right = expr.split(' = ')
                f.write('    Eq({}, {}),\n'.format(left, right))
            f.write(']\n')
            f.write('\n')

            f.write('sol = solve(exprs)[0]\n')
            f.write('\n')

            f.write('for key, val in sol.items():\n')
            f.write('    exec("{} = {}".format(key, val))\n')

    def scrape(self):
        """Returns the self.info dictionary through performing the scraping
        process, modifying the self.info dictionary, and then finally
        returning it"""
        self._scrape_table()
        self._scrape_title()
        self._scrape_authors()
        self._scrape_exprs()
        self._scrape_inline_exprs()
        # self.get_missing_parameters()
        self._generate_txt()
        self._generate_python()
        self._generate_python_test()
        return self.info


# scraper = Scraper(url='https://www.sciencedirect.com/science/article/pii/S0749641904001664',
#                   usr_data_dir='C:\\Users\\Vincent\\AppData\\Local\\Google\\Chrome\\User Data')

# scraper.parse()

# scraper.scrape_title()
# scraper.get_title()
#
# scraper.scrape_authors()
# scraper.get_authors()
#
# scraper.scrape_exprs()
# scraper.get_exprs()

# scraper.scrape()

# print(scraper.get_var_dict())
# print(scraper.get_python_exprs())


with open('paper_url.txt', 'r', encoding='utf-8') as f:
    urls = f.readlines()
    for url in urls:
        print(url.strip('\n'))
        scraper = Scraper(url=url.strip('\n'),
                          usr_data_dir='Users/samildhawan/Library/Application Support/Google/Chrome/User Data')

        scraper.parse()
        print('Scraping {}: '.format(url[:-1]))
        scraper.scrape()

        print(scraper.get_var_dict())
        print(scraper.get_python_exprs())
        # print(scraper.get_missing_parameters())
