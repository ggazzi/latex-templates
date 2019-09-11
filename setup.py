from setuptools import setup

setup(
    name='latex_templates',
    version='0.1',
    description='Utilities for managing LaTeX templates',
    url='https://github.com/ggazzi/latex-templates',
    author='Guilherme Grochau Azzi',
    author_email='ggazzi@inf.ufrgs.br',
    license='MIT',
    install_requires=['PyYAML>=5.1', 'Jinja2', 'argcomplete'],
    packages=['latex_templates'],
    entry_points= {
      'console_scripts': ['latex-templates=latex_templates:main']
    },
    include_package_data=True
  )

