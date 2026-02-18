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

          # Ensure zenity is available on PATH so the file-chooser and result
          # dialogs work when launched from a GNOME file manager.
          makeWrapperArgs = [
            "--prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.zenity ]}"
          ];

          postInstall = ''
            install -Dm644 ${./sloppy-pdf-renamer.desktop} \
              $out/share/applications/sloppy-pdf-renamer.desktop
          '';

          doCheck = false;

          meta = with pkgs.lib; {
            description = "Rename PDF files based on their titles";
            homepage = "https://github.com/mmxgn/sloppy-pdf-renamer-flake";
            license = licenses.mit;
            maintainers = [ ];
            mainProgram = "sloppy-pdf-renamer";
          };
        };

        # Alias for convenience
        packages.sloppy-pdf-renamer = self.packages.${system}.default;

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/sloppy-pdf-renamer";
        };

        # Development shell with all dependencies
        devShells.default = pkgs.mkShell {
          buildInputs = with python.pkgs; [
            python
            poetry-core
            pypdf
            pdfplumber
            pytest
            pytest-cov
          ] ++ [ pkgs.zenity ];

          shellHook = ''
            echo "Sloppy PDF Renamer development environment"
            echo "Run 'python -m sloppy_pdf_renamer --help' to test the CLI"
          '';
        };
      }
    );
}
