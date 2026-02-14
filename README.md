# Sloppy PDF Renamer

Automatically rename PDF files based on their titles. Many PDFs have cryptic filenames (e.g., `document_final_v3.pdf`, `1234567.pdf`) while containing clear titles in their metadata or content. This tool extracts the title and uses it as the filename.

## TL;DR - Quick Start

Run without installing (using Nix):

```bash
# Preview what would be renamed (safe, doesn't modify files)
nix run github:mmxgn/sloppy-pdf-renamer-flake -- document.pdf --dry-run

# Actually rename the file (removes --dry-run flag, will rename your file!)
nix run github:mmxgn/sloppy-pdf-renamer-flake -- document.pdf

# Batch process a directory
nix run github:mmxgn/sloppy-pdf-renamer-flake -- ~/Downloads --recursive --dry-run
```

**⚠️ Warning:** Removing the `--dry-run` flag will rename your files. Always test with `--dry-run` first!

## Features

- **Smart title extraction**: Tries PDF metadata first, falls back to content parsing
- **Safe renaming**: Preview changes with `--dry-run` before applying
- **Batch processing**: Process entire directories with `--recursive`
- **Duplicate handling**: Automatically appends `(1)`, `(2)`, etc. for duplicates
- **Filename sanitization**: Removes invalid characters and normalizes whitespace
- **Nix flake**: Easy installation and integration with NixOS/home-manager

## Installation

### Using Nix Flakes

Install directly from the repository:

```bash
nix profile install github:mmxgn/sloppy-pdf-renamer-flake
```

Or add to your NixOS configuration:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    sloppy-pdf-renamer.url = "github:mmxgn/sloppy-pdf-renamer-flake";
  };

  outputs = { self, nixpkgs, sloppy-pdf-renamer }: {
    nixosConfigurations.yourhost = nixpkgs.lib.nixosSystem {
      # ...
      environment.systemPackages = [
        sloppy-pdf-renamer.packages.${system}.default
      ];
    };
  };
}
```

Or use with home-manager:

```nix
{
  inputs = {
    home-manager.url = "github:nix-community/home-manager";
    sloppy-pdf-renamer.url = "github:mmxgn/sloppy-pdf-renamer-flake";
  };

  # In home.nix:
  home.packages = [
    sloppy-pdf-renamer.packages.${system}.default
  ];
}
```

### Development

Enter the development environment:

```bash
nix develop
```

Build the package:

```bash
nix build
```

Run without installing:

```bash
nix run . -- --help
```

## Usage

### Basic Usage

Rename a single PDF file:

```bash
sloppy-pdf-renamer document.pdf
```

Preview changes without renaming (dry-run):

```bash
sloppy-pdf-renamer document.pdf --dry-run
```

### Batch Processing

Rename all PDFs in a directory:

```bash
sloppy-pdf-renamer ~/Documents/papers
```

Process directories recursively:

```bash
sloppy-pdf-renamer ~/Downloads --recursive
```

### Examples

```bash
# Single file with preview
sloppy-pdf-renamer ~/Downloads/1234567.pdf --dry-run
# Output: Would rename: 1234567.pdf -> Research Paper on Machine Learning.pdf

# Batch processing with verbose output
sloppy-pdf-renamer ~/Documents --recursive --verbose

# Process current directory
sloppy-pdf-renamer . -r
```

## How It Works

1. **Metadata extraction**: First tries to read the `/Title` field from PDF metadata
2. **Content fallback**: If metadata is missing, extracts text from the first page and uses heuristics to identify the title
3. **Sanitization**: Removes invalid filename characters (`/ \ : * ? " < > |`), normalizes whitespace, and limits length to 200 characters
4. **Duplicate handling**: If the target filename exists, appends `(1)`, `(2)`, etc.
5. **Renaming**: Renames the file in place (same directory)

## Command-Line Options

```
sloppy-pdf-renamer <path> [options]

Arguments:
  path                  PDF file or directory to process

Options:
  --dry-run            Preview changes without actually renaming files
  -r, --recursive      Process subdirectories recursively
  -v, --verbose        Show detailed logging output
  -h, --help           Show help message
```

## Exit Codes

- `0`: Success (at least one file renamed)
- `1`: Failure (no files renamed or error occurred)

## Testing

Run the test suite:

```bash
nix develop
python -m pytest tests/ -v
```

Run with coverage:

```bash
python -m pytest tests/ --cov=sloppy_pdf_renamer --cov-report=html
```

## Dependencies

- **Python 3.9+**
- **pypdf** (4.x): Modern PyPDF2 fork for metadata extraction
- **pdfplumber** (0.11.x): Content parsing and text extraction

## Project Structure

```
.
├── flake.nix              # Nix flake definition
├── pyproject.toml         # Python project metadata
├── README.md              # This file
├── sloppy_pdf_renamer/
│   ├── __init__.py       # Package marker
│   ├── __main__.py       # Entry point for python -m sloppy_pdf_renamer
│   ├── cli.py            # CLI implementation
│   ├── extractor.py      # PDF title extraction
│   └── renamer.py        # Filename sanitization and renaming
└── tests/
    ├── test_extractor.py # Extractor tests
    └── test_renamer.py   # Renamer tests
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Limitations

- Only processes PDF files (`.pdf` extension)
- Renames files in place (no option to copy to a different directory)
- Title extraction heuristics may not work for all PDF formats
- Very long titles are truncated to 200 characters
