{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        rec {
          packages = {
            default = packages.latex-templates;
            latex-templates = import ./default.nix {
              inherit pkgs;
              pythonPackages = pkgs.python3Packages;
            };

            devShell = import ./shell.nix { inherit pkgs; };
          };
        }
      );
}
