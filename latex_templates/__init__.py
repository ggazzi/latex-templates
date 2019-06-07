#!/usr/bin/env python

import jinja2
import yaml
import sys
import argparse
import pkg_resources
import shutil
import os
from pathlib import Path

class Template:

  @classmethod
  def find(cls, template_path, name, lib_path, verbose=False):
    if verbose: print(f'Looking for template "{name}"')

    for dir in template_path:
      path = Path(dir) / name
      if verbose: print('  trying ' + str(path), end='')
      if cls.is_template(path):
        if verbose: print(' FOUND!')
        return cls(path, lib_path)
      elif verbose: print()

    raise Exception('No template "{}" found.'.format(name))

  @classmethod
  def find_all(cls, template_path, verbose=False):
    if verbose: print('Listing all templates')

    for dir in template_path:
      if not dir.is_dir(): continue
      if verbose: print(f'checking {dir}')

      for subdir in Path(dir).iterdir():
        if cls.is_template(subdir):
          yield subdir.name

  @classmethod
  def is_template(cls, directory):
    return (
      directory.is_dir() and
      (directory / 'default-conf.yaml').is_file() and
      (directory / 'contents.yaml').is_file()
    )

  def __init__(self, root_dir, lib_path):
    self.__root_dir = Path(root_dir)

    paths = [root_dir] + list(lib_path)
    self.__env = jinja2.Environment(
        block_start_string = r'\STMT{',
        block_end_string = r'}',
        variable_start_string = r'\EXPR{',
        variable_end_string = r'}',
        comment_start_string = r'\#{',
        comment_end_string = r'}',
        line_statement_prefix = '%%$',
        line_comment_prefix = '%%#',
        #trim_blocks = True,
        #lstrip_blocks = True,
        autoescape = False,
        loader = jinja2.FileSystemLoader([str(p) for p in paths]),
        keep_trailing_newline=True
      )

  def get_default_conf_file(self):
    return self.__root_dir / 'default-conf.yaml'
  
  def get_default_conf(self):
    with open(self.get_default_conf_file()) as default_conf:
      return yaml.load(default_conf)

  def generate(self, config, target_dir):
    config = {**self.get_default_conf(), **config}
    env = self.__env

    target_dir = Path(target_dir)
    if not target_dir.exists():
      target_dir.mkdir(parents=True)

    file_list = env.get_template('contents.yaml').render(config)
    for entry in yaml.load(file_list):
      if isinstance(entry, str):
        entry = {'src': entry, 'tgt': entry}
      elif 'tgt' not in entry:
        entry['tgt'] = entry['src']

      out_path = target_dir / entry['tgt']
      if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True)

      if 'raw' in entry and entry['raw']:
        in_path = self.__root_dir / entry['src']
        shutil.copyfile(in_path, out_path)

      else:
        template = env.get_template(entry['src'])
        with open(out_path, 'w') as out:
          template.stream(config).dump(out)

def parse_args():

  parser = argparse.ArgumentParser(description='Generate a LaTeX project from a template.')
  parser.add_argument('--path', '-p', dest='template_path', default=None,
                      help='Paths where templates and libraries are searched, colon-separated.')
  parser.add_argument('--verbose', '-v', action='store_true')

  commands = parser.add_subparsers()

  parser_list = commands.add_parser('list', help='List all available templates.')
  parser_list.set_defaults(command='list')

  parser_genconf = commands.add_parser('genconf', help='Generate a default config file for the given template.')
  parser_genconf.add_argument('template', metavar='TEMPLATE', help='Name of the desired template.')
  parser_genconf.add_argument('--output-file', '-o', metavar='FILE', default='./config.yaml',
                              help='File where the default config is written [default=./config.yaml]')
  parser_genconf.set_defaults(command='genconf')

  parser_gen = commands.add_parser('generate', help='Generate a template based on a config file.')
  parser_gen.add_argument('template', metavar='TEMPLATE', help='Name of the desired template.')
  parser_gen.add_argument('output_dir', metavar='OUT_DIR',                                  
                          help='Directory where the generated files will be written.')
  parser_gen.add_argument('--config-file', '-c', metavar='FILE', default='./config.yaml',
                          help='Configuration file for the generated template [default=./config.yaml]')
  parser_gen.set_defaults(command='generate')

  return parser.parse_args()

DEFAULT_PATH = [
  './',
  '{HOME}/.local/share/latex-templates/'.format(HOME=os.environ['HOME']),
  '/usr/local/share/latex-templates/',
  '/usr/share/latex-templates/'
]


def main():
  args = parse_args()

  path = args.template_path.split(':') if args.template_path else DEFAULT_PATH
  if args.verbose:
    print(f'Template lookup paths: {path}')

  template_path = [ Path(p) / 'templates' for p in path ]
  lib_path = [ Path(p) / 'libraries' for p in path ]
  template_path.append(Path(pkg_resources.resource_filename(__name__, 'templates')))
  lib_path.append(Path(pkg_resources.resource_filename(__name__, 'libraries')))

  if args.command == 'list':
    for template in Template.find_all(template_path, verbose=args.verbose):
      print(template)

  else:
    template = Template.find(template_path, args.template, lib_path, verbose=args.verbose)

    if args.command == 'genconf':
      config_file = Path(args.output_file)
      
      suffix = 0
      new_file = config_file
      while new_file.exists():
        suffix += 1
        new_file = config_file.with_suffix(config_file.suffix + '.{}'.format(suffix))

      shutil.copyfile(template.get_default_conf_file(), new_file)
    
    else:
      with open(args.config_file) as config_file:
        config = yaml.load(config_file)

      template.generate(config, Path(args.output_dir))

if __name__ == '__main__':
  main()