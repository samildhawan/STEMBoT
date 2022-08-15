import os
from lxml import etree
from lxml.builder import unicode
from py_asciimath.translator.translator import Tex2ASCIIMath


class Converter(Tex2ASCIIMath):
    def __init__(self):
        super().__init__()


    def _remove_phantom(self, expr):
        return expr.replace(r'\phantom{\rule{0.25em}{0ex}}', '')


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
        # expr = expr.replace(r'\%', 'xxxxx')
        expr = expr.replace(r'\stackrel{‾}', r'\overline')
        expr = expr.replace(r'\mathit', r'\mathrm')
        # expr = expr.replace(r'\mathrm{⁰}', r'^{\circ}')
        # expr = expr.replace(r'\prime', 'xxxxx')

        return expr


    def _process_division(self, expr):
        return expr.replace('//', '/')


    def _process_frac(self, expr):
        idx = 0

        while True:
            idx = expr.find('frac', idx)
            lbrackets = 0
            rbrackets = 0

            if idx == -1:
                expr = expr.replace('frac', '')
                return expr

            while lbrackets > rbrackets or lbrackets == 0:
                if expr[idx] == '(':
                    lbrackets += 1
                elif expr[idx] == ')':
                    rbrackets += 1

                idx += 1

            expr = expr[:idx] + ' / ' + expr[idx:]


    def _mml2tex_post(self, expr):
        return self._process_signs(self._process_greek(self._remove_phantom(expr)))


    def _tex2ascii_post(self, expr):
        return self._process_frac(self._process_division(expr))


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
