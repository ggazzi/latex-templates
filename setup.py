from setuptools import setup

setup(
    name='latex_templates',
    version='0.1dev1',
    description='Set of LaTeX project templates.',
    url='https://github.com/ggazzi/latex-templates',
    author='Guilherme Grochau Azzi',
    author_email='ggazzi@inf.ufrgs.br',
    license='MIT',
    install_requires=['PyYAML', 'Jinja2'],
    packages=['latex_templates'],
    entry_points= {
      'console_scripts': ['latex-templates=latex_templates:main']
    },
    include_package_data=True
  )

