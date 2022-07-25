{ 
  pkgs ? import <nixpkgs> {},
  pythonPackages ? pkgs.python3Packages
}:

pythonPackages.buildPythonPackage rec {
  name = "latex-templates";
  version = "0.1.1";
  src = ./.;
  format = "setuptools";
  propagatedBuildInputs = with pythonPackages; [
    argcomplete
    jinja2
    pyyaml
    pkgs.texlive.combined.scheme-full
  ];
}