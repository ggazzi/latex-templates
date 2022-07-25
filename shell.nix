{ pkgs ? import <nixpkgs> {} }:


let
  python-with-packages = pkgs.python3.withPackages (pythonPackages: with pythonPackages; [
    (import ./default.nix { inherit pkgs pythonPackages; })
  ]);

  # texlive = pkgs.texlive.combine {
  #   inherit (pkgs.texlive) scheme-medium latex-bin latexmk eulervm;
  # };
  texlive = pkgs.texlive.combined.scheme-full;
in
pkgs.mkShell {
  buildInputs = [
    python-with-packages
    texlive
  ];
}