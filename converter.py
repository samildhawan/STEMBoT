import os
import re

from lxml import etree
from lxml.builder import unicode
from py_asciimath.translator.translator import Tex2ASCIIMath


class Converter(Tex2ASCIIMath):
    def __init__(self):
        super().__init__()


    def _process_greek(self, expr):
        greek_dict = {'Α': r'\Alpha',   'α': r'\alpha',
                      'Β': r'\Beta',    'β': r'\beta',
                      'Γ': r'\Gamma',   'γ': r'\gamma',
                      'Δ': r'\Delta',   'δ': r'\delta',
                      'Ε': r'\Epsilon', 'ε': r'\epsilon',
                      'Ζ': r'\Zeta',    'ζ': r'\zeta',
                      'Η': r'\Eta',     'η': r'\eta',
                      'Θ': r'\Theta',   'θ': r'\theta',
                      'Ι': r'\Iota',    'ι': r'\iota',
                      'Κ': r'\Kappa',   'κ': r'\kappa',
                      'Λ': r'\Lambda',  'λ': r'\lambda',
                      'Μ': r'\Mu',      'μ': r'\mu',
                      'Ν': r'\Nu',      'ν': r'\nu',
                      'Ξ': r'\Xi',      'ξ': r'\xi',
                      'Ο': r'\Omicron', 'ο': r'\omicron',
                      'Π': r'\Pi',      'π': r'\pi',
                      'Ρ': r'\Rho',     'ρ': r'\rho',
                      'Σ': r'\Sigma',   'σ': r'\sigma',   'ς': r'\sigma',
                      'Τ': r'\Tau',     'τ': r'\tau',
                      'Υ': r'\Upsilon', 'υ': r'\upsilon',
                      'Φ': r'\Phi',     'φ': r'\phi',
                      'Χ': r'\Chi',     'χ': r'\chi',
                      'Ψ': r'\Psi',     'ψ': r'\psi',
                      'Ω': r'\Omega',   'ω': r'\omega'}

        for greek in greek_dict:
            expr = expr.replace(greek, greek_dict[greek])

        return expr


    def _process_signs(self, expr):
        expr = expr.replace('|', r'\vert')
        expr = expr.replace(r'\phantom{\rule{0.25em}{0ex}}', '')
        expr = expr.replace(r'\stackrel{‾}', r'\overline')
        expr = expr.replace(r'\displaystyle', '')
        return expr


    def _split_array(self, expr):
        expr_list = [expr]
        if r'\begin{array}' in expr:
            expr_list = expr.split(' & ')[1:]
            for i, expr in enumerate(expr_list):
                idx = expr.find('\hfill')
                expr_list[i] = expr[:idx]

        return expr_list

    def _process_frac(self, expr):
        idx = 0

        while True:
            idx = expr.find('frac', idx)
            lbrackets = 0
            rbrackets = 0

            if idx == -1:
                expr = expr.replace('frac', '')
                return expr

            while (lbrackets > rbrackets or lbrackets == 0) and idx < len(expr):
                if expr[idx] == '(':
                    lbrackets += 1
                elif expr[idx] == ')':
                    rbrackets += 1

                idx += 1

            expr = expr[:idx] + ' / ' + expr[idx:]


    def _process_divide(self, expr):
        idx = 0

        while True:
            idx = expr.find('//', idx)
            lbrackets = 0
            rbrackets = 0

            if idx == -1:
                expr = expr.replace('//', ' / (')
                return expr

            while lbrackets >= rbrackets and idx < len(expr):
                if expr[idx] == '(':
                    lbrackets += 1
                elif expr[idx] == ')':
                    rbrackets += 1

                idx += 1


            if idx >= len(expr):
                expr += ')'
            else:
                expr = expr[:idx] + ')' + expr[idx:]


    def _mml2tex_post(self, expr):
        expr = expr.replace('{(}', '(')
        expr = expr.replace('{)}', ')')
        expr = self._process_greek(expr)
        expr = self._process_signs(expr)
        expr = self._split_array(expr)
        return expr


    def _tex2ascii_post(self, expr):
        if expr.endswith(',') or expr.endswith('text(,)'):
            expr = expr.rstrip('text(,)')
        elif expr.endswith('.') or expr.endswith('text(.)'):
            expr = expr.rstrip('text(.)')
        expr = expr.rstrip()
        return self._process_frac(expr)


    def mml2tex(self, expr):
        xslt_file = os.path.join('mml2tex', 'mmltex.xsl')
        dom = etree.fromstring(expr)
        xslt = etree.parse(xslt_file)
        transform = etree.XSLT(xslt)
        newdom = transform(dom)
        tex = unicode(newdom)
        # print(tex)
        return self._mml2tex_post(tex)


    def tex2ascii(self, expr):
        ascii = self.translate(expr)
        # print(ascii)
        return self._tex2ascii_post(ascii)


    def ascii2python(self, expr, var_list):
        def repl_func_1(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return x.replace(' ', '')

        def repl_func_2(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            x = x.replace(' ', '')
            # try:
            #     float(x[2:-1])
            # except ValueError:
            #     return x
            return ' ** ' + x[1:]

        def repl_func_3(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            vars = x[5:-1].split(' ')
            exist = [var in var_list for var in vars]
            if all(exist) and ''.join(vars) not in var_list:
                return x[4:]
            return x[4:].replace(' ', '')

        def repl_func_4(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return x[1:-1]

        def repl_func_5(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return 'np.' + x[:3] + x[4:]

        def repl_func_6(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return 'np.' + x[:3] + '(' + x[4:] + ')'

        def repl_func_7(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return 'abs(' + x[2:-2] + ')'

        # remove spaces in _(?)
        pattern = '_\(.*?\)'
        expr = re.sub(pattern, repl_func_1, expr)

        # remove spaces in ^(?), replace ^ with **
        pattern = '\^\(.*?\)'
        expr = re.sub(pattern, repl_func_2, expr)

        # remove text and spaces in text(?)
        pattern = 'text\(.*?\)'
        expr = re.sub(pattern, repl_func_3, expr)

        # remove redundant brackets
        pattern = '\(\w*?\)'
        expr = re.sub(pattern, repl_func_4, expr)

        while True:
            expr_new = re.sub(pattern, repl_func_4, expr)
            if expr_new == expr:
                break
            expr = expr_new

        pattern = '\(\S\)'
        expr = re.sub(pattern, repl_func_4, expr)

        # replace sin (?) with np.sin(?)
        pattern = '(sin|cos|tan|exp)\s\(.*?\)'
        expr = re.sub(pattern, repl_func_5, expr)

        # replace sin ? with np.sin(?)
        pattern = '(sin|cos|tan|exp)\s\S*'
        expr = re.sub(pattern, repl_func_6, expr)

        # replace |:?:| with abs(?)
        pattern = '\|\:.*?\:\|'
        expr = re.sub(pattern, repl_func_7, expr)

        # replace sqrt() with np.sqrt()
        expr = expr.replace('sqrt(', 'np.sqrt(')

        # replace lambda with lambda_
        expr = expr.replace('lambda', 'lambda_')

        expr = self._process_divide(expr)

        operators = ['+', '-', '*', '/', '=', '>', '<', ',']

        expr_list = expr.split(' = ')
        left_expr = expr_list[0]
        right_expr = expr_list[1].split(' ')

        left_expr = left_expr.replace(' ', '')
        # left_expr = left_expr.replace('(', '')
        # left_expr = left_expr.replace(')', '')

        i = 0
        while i < len(right_expr) - 1:
            left_elem = True
            right_elem = True
            for o in operators:
                if o in right_expr[i]:
                    left_elem = False
                if o in right_expr[i + 1] and '(-' not in right_expr[i+1]:
                    right_elem = False

            if left_elem and right_elem:
                right_expr.insert(i + 1, '*')
                i += 1

            i += 1

        expr_final = left_expr + ' = ' + ' '.join(right_expr)
        return expr_final


    def html2python(self, expr):
        expr = expr.replace('<em>', '')
        expr = expr.replace('</em>', '')

        def repl_func_1(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return '_' + '(' + x[5:-6] + ')'

        def repl_func_2(matched):
            # if matched:
            x = matched.group(0)
            # print(x)
            return '^' + '(' + x[5:-6] + ')'

        # replace <sub>?</sub> with _(?)
        pattern = '<sub>.*?</sub>'
        expr = re.sub(pattern, repl_func_1, expr)

        # replace <sup>?</sup> with _(?)
        pattern = '<sup>.*?</sup>'
        expr = re.sub(pattern, repl_func_2, expr)

        return expr

    def name_post(self, expr):
        # print('Before: {}'.format(expr))
        expr = self.html2python(expr)
        expr = self._process_greek(expr)
        # expr = expr.replace('\\', '')
        # expr = expr.replace('(', '')
        # expr = expr.replace(')', '')
        # expr = expr.replace(' ', '')
        expr = expr.replace('lambda', 'lambda_')
        expr = ''.join(ch for ch in expr if ch.isalnum() or ch == '_')
        # print('After: {}'.format(expr))
        return expr


    def unit_post(self, expr):
        return self.html2python(expr)
