#!/usr/bin/env python

import argparse
import os
import runpy
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, List, NamedTuple, Optional, Tuple, Union

import argcomplete
import jinja2
import pkg_resources
import yaml
from argcomplete.completers import DirectoriesCompleter, FilesCompleter

__all__ = [
    "ProjectTemplate",
    "SearchPath",
    "GeneratedFile",
    "ProjectTemplateNotFoundError",
]

SearchPath = List[Path]


class GeneratedFile(NamedTuple):
    src: Path
    tgt: Path
    is_raw: bool
    is_main: bool

    @classmethod
    def from_yaml(cls, entry: dict) -> "GeneratedFile":
        if isinstance(entry, str):
            src, tgt = entry, entry
        else:
            src = entry["src"]
            tgt = entry["tgt"] if "tgt" in entry else src

        is_raw = bool("raw" in entry and entry["raw"])
        is_main = bool("main" in entry and entry["main"])

        return cls(Path(src), Path(tgt), is_raw, is_main)


class ProjectTemplateNotFoundError(Exception):
    def __init__(self, template_name, *args):
        super(ProjectTemplateNotFoundError, self).__init__(
            f'No project template named "{template_name}" was found.', *args
        )


class ProjectTemplate:
    """
    Template for a LaTeX-based project, stored as a directory following some file conventions.

    A template is essentially a directory containing several files to be copied
    as well as Jinja2 templates to be processed.  The template instantiation may
    receive several parameters, which are given as a YAML file.  For documentation
    purposes, **a *default configuration file* must be provided**, including default
    and/or dummy values for all accepted configuration entries.

    Project templates allow the directory structure of the generated projects to be
    lexible and affected by the configuration.  Thus, **a *contents template* must
    be provided**.  This is a Jinja2 template for a list of files that should
    be generated.

    In summary, template directory must containing at least the following two files:
      - The default configuration file "default-conf.yaml"
      - The contents template "contents.yaml"

    Each entry of the contents template may be either a string or an object with the
    following fields.  If a string is provided, it is used as both source and target path.

    src
      Path of the file to be copied or template to be processed, relative to the template root directory
    tgt
      Path of the file to be generated, relative to the project root directory
    is_raw (default=False)
      If true, the file is copied as-is.  Otherwise, it is used as a Jinja template.
    main (default=False)
      Can only be true for a single TeX file.  In that case, this file will be used as
      the main TeX file when generating a PDF directly from the template.


    Besides the files provided directly by the project template, resources from external
    "libraries" may also be imported from the Jinja templates, and entire files may be referred
    to in the contents template.  This is useful when importing personal LaTeX "libraries" when
    generating a new project, which can then safely be shared with co-authors or publishers
    without any additional dependencies.

    These resources are searched for in the given *library path* for the project template.
    """

    @classmethod
    def find(
        cls,
        name: str,
        template_path: SearchPath = None,
        lib_path: SearchPath = None,
        verbose: bool = False,
    ) -> "ProjectTemplate":
        """
      Search for a named template in the file system.

      :param name:
      Name of the searched template

      :param template_path:
      List of directories that may contain templates.
      If omitted, it is obtained with function ``search_paths()``.

      :param lib_path:
      List of directories that contain "libraries".
      If omitted, it is obtained with function ``search_paths()``.

      :param verbose:
      If true, report attempts at finding the template.

      :return:
      The

      :raise:
      ProjectTemplateNotFoundError

      """
        if verbose:
            print(f'Looking for template "{name}"')

        if template_path is None or lib_path is None:
            tpath, lpath = search_paths()
            template_path = template_path or tpath
            lib_path = lib_path or lpath

        for dir in template_path:
            path = Path(dir) / name
            if verbose:
                print("  trying " + str(path), end="")
            if cls.is_template(path):
                if verbose:
                    print(" FOUND!")
                return cls(path, lib_path)
            elif verbose:
                print()

        raise ProjectTemplateNotFoundError(name)

    @classmethod
    def find_all(
        cls, template_path: SearchPath, verbose: bool = False
    ) -> Iterable[str]:
        if verbose:
            print("Listing all templates")

        for dir in template_path:
            if not dir.is_dir():
                continue
            if verbose:
                print(f"checking {dir}")

            for subdir in Path(dir).iterdir():
                if cls.is_template(subdir):
                    yield subdir.name

    @classmethod
    def is_template(cls, directory: Path) -> bool:
        """Check if the given directory conforms to the project template conventions."""
        return (
            directory.is_dir()
            and (directory / "default-conf.yaml").is_file()
            and (directory / "contents.yaml").is_file()
        )

    def __init__(self, root_dir: Union[str, Path], lib_path: SearchPath):
        self.__root_dir = Path(root_dir)

        paths = [root_dir] + list(lib_path)
        self.__env = jinja2.Environment(
            block_start_string=r"\STMT{",
            block_end_string=r"}",
            variable_start_string=r"\EXPR{",
            variable_end_string=r"}",
            comment_start_string=r"\#{",
            comment_end_string=r"}",
            line_statement_prefix="%%$",
            line_comment_prefix="%%#",
            # trim_blocks = True,
            # lstrip_blocks = True,
            autoescape=False,
            loader=jinja2.FileSystemLoader([str(p) for p in paths]),
            keep_trailing_newline=True,
        )

    @property
    def name(self) -> str:
        return self.__root_dir.name

    @property
    def default_conf_file(self) -> Path:
        return self.__root_dir / "default-conf.yaml"

    def load_default_conf(self) -> dict:
        with open(str(self.default_conf_file)) as default_conf:
            return yaml.full_load(default_conf)

    def generate(self, config: dict, target_dir: Union[str, Path]):
        config = self.__config_with_defaults(config)
        env = self.__env

        target_dir = Path(target_dir)
        if not target_dir.exists():
            target_dir.mkdir(parents=True)

        for entry in self.get_generated_files(config):
            out_path = target_dir / entry.tgt
            if not out_path.parent.exists():
                out_path.parent.mkdir(parents=True)

            if entry.is_raw:
                in_path = self.__root_dir / entry.src
                shutil.copyfile(in_path, out_path)

            else:
                template = env.get_template(str(entry.src))
                with open(out_path, "w") as out:
                    template.stream(config).dump(out)

    def compile_pdf(
        self,
        config: dict,
        *,
        output_path: Union[str, Path, None] = None,
        build_dir: Union[str, Path, None] = None,
        overwrite: bool = False,
        verbose: bool = False,
    ) -> Path:
        """Generate the given project template and compile the resulting PDF.

        Both parameters ``output_path`` and ``build_dir`` are optional, but at
        least one of them should be provided.

        :param config:
        Configuration dictionary for the project template.

        :param output_path:
        Optional path where the output file will be written.
        If an existing directory is given, uses the filename from the project's
        main TeX file.  Existing files are never overwritten, instead a suffix is
        added to ensure that a new file is created.

        :param build_dir:
        Optional path where the project will be generated.
        If omitted, a temporary directory will be used and deleted as soon as
        compilation completes.

        :param overwrite:
        If false, add a suffix to the output filename to avoid overwriting
        existing files.

        :param verbose:
        If true, write the compilation progress to the standard output.

        :return:
        Path to the generateed file.

        :raise:
        ValueError when the template does not specify a main file.
        """
        output_path = None if output_path is None else Path(output_path)
        if build_dir is None:
            with TemporaryDirectory() as build_dir:
                return self.__compile_pdf(
                    config, output_path, Path(build_dir), overwrite, verbose
                )
        else:
            return self.__compile_pdf(
                config, output_path, Path(build_dir), overwrite, verbose
            )

    def __compile_pdf(
        self,
        config: dict,
        output_path: Optional[Path],
        build_dir: Path,
        overwrite: bool,
        verbose: bool,
    ) -> Path:
        self.generate(config, build_dir)

        main_file = self.get_main_latex_file(config)
        if main_file is None:
            raise ValueError(f"Template '{self.name}' does not specify a main file.")

        if verbose:
            print(f"Building from {main_file.tgt}")
        subprocess.run(
            ["latexmk", "-pdf", main_file.tgt],
            cwd=str(build_dir),
            stdout=sys.stdout if verbose else subprocess.DEVNULL,
            stderr=sys.stderr if verbose else subprocess.DEVNULL,
        )

        generated_file = (build_dir / main_file.tgt).with_suffix(".pdf")
        if output_path is not None:
            if output_path.is_dir():
                output_path = (output_path / main_file.tgt).with_suffix(".pdf")
            output_file, i = output_path, 1
            while output_file.exists() and not overwrite:
                output_file = output_path.parent / f"{output_path.stem} ({i}).pdf"
                i += 1
            shutil.copyfile(str(generated_file), str(output_file))
            return output_file
        else:
            return generated_file

    def get_generated_files(self, config: dict) -> List[GeneratedFile]:
        """Obtain a list of files that should be generated with the given config."""
        config = self.__config_with_defaults(config)
        file_list = self.__env.get_template("contents.yaml").render(config)
        return [GeneratedFile.from_yaml(entry) for entry in yaml.full_load(file_list)]

    def get_main_latex_file(self, config: dict) -> Optional[GeneratedFile]:
        """Obtain the main LaTeX file that may be used to compile a PDF, if there is one."""
        for entry in self.get_generated_files(config):
            if entry.is_main:
                return entry
        return None

    def __config_with_defaults(self, config: dict) -> dict:
        return {**self.load_default_conf(), **config}

def enumerate_templates(template_path: SearchPath, verbose: bool = False):
    for template in ProjectTemplate.find_all(template_path, verbose):
        yield template


def generate_config(template: ProjectTemplate, output_file: Union[str, Path]):
    config_file = Path(output_file)

    suffix = 0
    new_file = config_file
    while new_file.exists():
        suffix += 1
        new_file = config_file.with_suffix(config_file.suffix + ".{}".format(suffix))

    shutil.copyfile(str(template.default_conf_file), new_file)


def generate_project(
    template: ProjectTemplate, config, output_dir, should_compile, verbose
):
    template.generate(config, Path(output_dir))

    if should_compile:
        main_file = template.get_main_latex_file(config)
        if main_file is None:
            print("This template does not specify a main file.", file=sys.stderr)
            sys.exit(1)

        if verbose:
            print(f"Building from {main_file.tgt}")
        subprocess.run(["latexmk", "-pdf", main_file.tgt], cwd=output_dir)

        return (Path(output_dir) / main_file.tgt).with_suffix(".pdf")


DEFAULT_PATH = [
    "./",
    "{HOME}/.local/share/latex-templates/".format(HOME=Path.home()),
    "/usr/local/share/latex-templates/",
    "/usr/share/latex-templates/",
]

PATH_ENV_VAR = "LATEX_TEMPLATE_PATH"


def search_paths() -> Tuple[SearchPath, SearchPath]:
    """Obtain search paths for templates and libraries, respectively.

    Use base directories from the LATEX_TEMPLATE_PATH variable, or a default list of directories.
    Assume that each listed directory has a ``templates'' and a ``libraries'' subdirectory.
    """
    if PATH_ENV_VAR in os.environ and os.environ[PATH_ENV_VAR]:
        path = os.environ[PATH_ENV_VAR].split(":")
    else:
        path = DEFAULT_PATH

    template_path = [Path(p) / "templates" for p in path]
    lib_path = [Path(p) / "libraries" for p in path]

    template_path.append(Path(pkg_resources.resource_filename(__name__, "templates")))
    lib_path.append(Path(pkg_resources.resource_filename(__name__, "libraries")))

    return template_path, lib_path


def parse_args(template_path=None):
    templates = (
        list(enumerate_templates(template_path)) if template_path is not None else None
    )

    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Generate a LaTeX project from a template.",
        epilog=textwrap.dedent(
            f"""
      Templates are searched according to the `{PATH_ENV_VAR}' variable, by default:
        "{':'.join(DEFAULT_PATH)}"
    """
        ),
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--import",
        metavar="PYTHON_FILE",
        action="append",
        dest="import_modules",
        default=[],
        help="Additional python files to import, useful if the YAML configs contain tags.",
    )

    commands = parser.add_subparsers()
    parser.set_defaults(command="list")

    parser_list = commands.add_parser("list", help="List all available templates.")
    parser_list.set_defaults(command="list")

    parser_genconf = commands.add_parser(
        "genconf", help="Generate a default config file for the given template."
    )
    parser_genconf.set_defaults(command="genconf")
    parser_genconf.add_argument(
        "template",
        type=str,
        metavar="TEMPLATE",
        help="Name of the desired template.",
        choices=templates,
    )
    parser_genconf.add_argument(
        "--output-file",
        "-o",
        metavar="FILE",
        default="./config.yaml",
        help="File where the default config is written [default=./config.yaml]",
    ).completer = FilesCompleter

    parser_gen = commands.add_parser(
        "generate", help="Generate a template based on a config file."
    )
    parser_gen.set_defaults(command="generate")
    parser_gen.add_argument(
        "template",
        metavar="TEMPLATE",
        help="Name of the desired template.",
        choices=templates,
    )
    parser_gen.add_argument(
        "output_dir",
        metavar="OUT_DIR",
        help="Directory where the generated files will be written.",
    ).completer = DirectoriesCompleter
    parser_gen.add_argument(
        "--config-file",
        "-c",
        metavar="FILE",
        default="./config.yaml",
        help="Configuration file for the template [default=./config.yaml]",
    ).completer = FilesCompleter
    parser_gen.add_argument(
        "--build",
        "-b",
        default=False,
        action="store_true",
        help="Build the generated template with latexmk.",
    )

    parser_build = commands.add_parser(
        "build", help="Generate a PDF document from a template"
    )
    parser_build.set_defaults(command="build")
    parser_build.add_argument(
        "template",
        metavar="TEMPLATE",
        help="Name of the desired template.",
        choices=templates,
    )
    parser_build.add_argument(
        "--output-file", "-o", metavar="FILE", type=Path, default=None
    ).completer = FilesCompleter
    parser_build.add_argument(
        "--config-file",
        "-c",
        metavar="FILE",
        default="./config.yaml",
        help="Configuration file for the template [default=./config.yaml]",
    ).completer = FilesCompleter
    parser_build.add_argument(
        "--force-overwrite",
        "-f",
        action="store_true",
        help="Overwrite the output file if it exists, instead of adding a suffix.",
    )

    argcomplete.autocomplete(parser)
    return parser.parse_args()


def main():
    template_path, lib_path = search_paths()
    args = parse_args(template_path)

    if args.verbose:
        print(f"Template lookup paths: {template_path}")

    for module in args.import_modules:
        runpy.run_path(module)

    if args.command == "list":
        for template in enumerate_templates(template_path, args.verbose):
            print(template)
    else:
        template = ProjectTemplate.find(
            args.template, template_path, lib_path, verbose=args.verbose
        )

        if args.command == "genconf":
            generate_config(template, args.output_file)

        else:
            with open(args.config_file) as config_file:
                config = yaml.full_load(config_file)
            config['cwd'] = Path(args.config_file).resolve().parent

            if args.command == "generate":
                if args.build:
                    template.compile_pdf(
                        config,
                        build_dir=args.output_dir,
                        verbose=args.verbose,
                        overwrite=True,
                    )
                else:
                    template.generate(config, args.output_dir)

            elif args.command == "build":
                template.compile_pdf(
                    config,
                    output_path=args.output_file or Path(),
                    verbose=args.verbose,
                    overwrite=args.force_overwrite,
                )


if __name__ == "__main__":
    main()
