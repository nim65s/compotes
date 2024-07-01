{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      poetry2nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
      in
      {
        packages = {
          compotes = mkPoetryApplication {
            projectDir = self;
            overrides = defaultPoetryOverrides.extend (
              self: super: {
                django-autoslug = super.django-autoslug.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                });
                django-bootstrap5 = super.django-bootstrap5.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                });
                dparse = super.dparse.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.hatchling ];
                });
                yeouia = super.yeouia.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.poetry-core ];
                });
                safety-schemas = super.safety-schemas.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.poetry-core ];
                });
                dmdm = super.dmdm.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.poetry-core ];
                });
                nmdmail = super.nmdmail.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.poetry-core ];
                });
                ndh = super.ndh.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.poetry-core ];
                });
                emails = super.emails.overridePythonAttrs (old: {
                  buildInputs = (old.buildInputs or [ ]) ++ [ super.setuptools ];
                });
              }
            );
          };
          default = self.packages.${system}.compotes;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.compotes ];
          packages = [ pkgs.poetry ];
        };
      }
    );
}
