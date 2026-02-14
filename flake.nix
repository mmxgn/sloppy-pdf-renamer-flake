{
  description = "Rename PDF files based on their titles";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in
      {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "sloppy-pdf-renamer";
          version = "0.1.0";
          src = ./.;

          pyproject = true;

          nativeBuildInputs = with python.pkgs; [
            poetry-core
          ];

          propagatedBuildInputs = with python.pkgs; [
            pypdf
            pdfplumber
          ];

          # Skip tests during build for now
          # Can be enabled once test suite is complete
          doCheck = false;

          meta = with pkgs.lib; {
            description = "Rename PDF files based on their titles";
            homepage = "https://github.com/mmxgn/sloppy-pdf-renamer-flake";
            license = licenses.mit;
            maintainers = [ ];
          };
        };

        # Alias for convenience
        packages.sloppy-pdf-renamer = self.packages.${system}.default;

        # Development shell with all dependencies
        devShells.default = pkgs.mkShell {
          buildInputs = with python.pkgs; [
            python
            poetry-core
            pypdf
            pdfplumber
            pytest
            pytest-cov
          ];

          shellHook = ''
            echo "Sloppy PDF Renamer development environment"
            echo "Run 'python -m sloppy_pdf_renamer --help' to test the CLI"
          '';
        };
      }
    );
}
