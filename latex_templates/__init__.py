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
    if verbose: print('Looking for template "{}"'.format(name))

    for dir in template_path:
      path = Path(dir) / name
      if verbose: print('  trying ' + str(path))
      if path.is_dir():
        return cls(path, lib_path)

    raise Exception('No template "{}" found.'.format(name))

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
      template = env.get_template(entry['src'])

      out_path = target_dir / entry['tgt']
      if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True)
      with open(out_path, 'w') as out:
        template.stream(config).dump(out)

def parse_args():

  parser = argparse.ArgumentParser(description='Generate a LaTeX project from a template.')
  parser.add_argument('template', metavar='TEMPLATE', help='Name of the desired template.')
  parser.add_argument('config', metavar='CONFIG_FILE', help='Configuration file.')
  parser.add_argument('output_dir', metavar='OUT_DIR',
                        help='Directory where the generated files will be written.')
  parser.add_argument('--get-config', '-c', action='store_true',
                    help='Instead of generating the template, create a default config file for it.')
  parser.add_argument('--path', '-p', dest='template_path',
                      help='Paths where templates and libraries are searched, colon-separated.')
  parser.add_argument('--verbose', '-v', action='store_true')

  return parser.parse_args()

DEFAULT_PATH = ':'.join([
    './',
    '{HOME}/.local/share/latex-templates/'.format(HOME=os.environ['HOME']),
    '/usr/local/share/latex-templates/',
    '/usr/share/latex-templates/'])


def main():
  args = parse_args()

  path = args.template_path.split(':') if args.template_path else DEFAULT_PATH
  template_path = [ Path(p) / 'templates' for p in path ]
  lib_path = [ Path(p) / 'libraries' for p in path ]
  template_path.append(pkg_resources.resource_filename(__name__, 'templates'))
  lib_path.append(pkg_resources.resource_filename(__name__, 'libraries'))

  template = Template.find(template_path, args.template, lib_path)

  if args.get_config:
    config_file = Path(args.config)
    
    suffix = 0
    new_file = config_file
    while new_file.exists():
      suffix += 1
      new_file = config_file.with_suffix(config_file.suffix + '.{}'.format(suffix))

    shutil.copyfile(template.get_default_conf_file(), new_file)
  
  else:
    with open(args.config) as config_file:
      config = yaml.load(config_file)

    template.generate(config, Path(args.output_dir))

if __name__ == '__main__':
  main()