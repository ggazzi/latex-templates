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

## Templates and Libraries

This contains several LaTeX _project templates_ which may share some code in the form of _libraries_.
Each project template corresponds to a subdirectory of `templates/` with the mandatory files described below.
Libraries are a collection of templates for located in `libraries/`, which are can be `include`d into any template.
The organization of libraries is purely by convention.

Each _project template_ consists of a directory containing a _default configuration file_  `default-conf.yaml`, a _contents template_ `contents.yaml` and multiple _file templates_, possibly including subdirectories.

The default configuration file `default-conf.yaml` should contain all values that will be use in the file templates.
These values may be overridden by another configuration file when instantiating the project template.

The content template `files.yaml` determines which file templates will be instantiated for this project.
Its instantiation should result in a list where each item is either a pair `{src: x, tgt: y}` or a single string, which is then used as both source and target.
The `src` field defines the path to the file template, relative either to the project template root or the the libraries root.
The `tgt` field determines the path to the generated file, relative to the generated project root.

### Template Syntax

Instead of the regular Jinja2 syntax, the following is adopted since it integrates better with LaTeX.

 - Statements: `\STMT{ ... }` instead of `{% ... %}` 
 - Expressions: `\EXPR{ ... }` instead of `{{ ... }}` 
 - Comments: `\#{ ... }` instead of `{# .. #}`
 - Line Statements: `%$ ...` instead of `# ...`
 - Line Comments: `%# ...` instead of `## ...`

## Why create this?

The main motivation is to have a lightweight set of LaTeX libraries with the following requirements:

  - Easy reuse when creating new projects
  - Easy sharing of projects with co-authors
  - Suitability of projects for publication

The last two points mean that these libraries must be _copied_ into each project, instead of being left in the environment.
This is useful for small or domain-specific utilities, since incorporating them in the standard LaTeX distributions is not feasible or desirable.
