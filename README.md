# LaTeX Templates

A collection of configurable templates for LaTeX projects.
The templates are handled by Jinja2, with configuration loaded from YAML files.

## Dependencies

This depends on PyYAML and Jinja2, both of which may be installed via pip:

```bash
pip install PyYAML Jinja2
```

## Usage

To generate templates, use the script `latex-templates.py`.
Call it with the `-h` option for further information.

Each template corresponds to a directory under `templates/`.
In the root directory for each template, two files are mandatory: `default-conf.yaml` and `files.yaml`.

The `default-conf.yaml` contains the default configuration for the template.
It should contain all necessary values accessible to the template.

The `files.yaml` is a template for a YAML file, used to select further templates that will be instantiated.
The result of processing `files.yaml` should be a list containing `{src: x, tgt: y}` pairs, or single strings which are taken as source and target.
The `src` field is the path to a template file, relative to the template root.
The `tgt` field is the path where the generated file should be written, relative to the root of the generated project.

## Template Syntax

Instead of the regular Jinja2 syntax, the following is adopted since it integrates better with LaTeX.

 - Statements: instead of `{% ... %}`, `\STMT{ ... }`
 - Expressions: instead of `{{ ... }}`, `\EXPR{ ... }`
 - Comments: instead of `{# .. #}`, `\#{ ... }`
 - Line Statements: instead of `# ...`, `%$ ...`
 - Line Comments: instead of `## ...`, `%# ...`