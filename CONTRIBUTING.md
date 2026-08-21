# Contributing Guidelines

Thanks for your interest in contributing to this project.

## How to Contribute

1. Fork the repo.
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b my-new-feature
   ```
3. Make your changes and test them thoroughly.
4. Commit your changes with a clear message:
   ```bash
   git commit -m "Add feature XYZ"
   ```
5. Push to your branch:
   ```bash
   git push origin my-new-feature
   ```
6. Open a Pull Request explaining what was changed and why.

## Areas to Contribute

- Support for other EEG headsets (OpenBCI, Muse, etc.)
- Signal filtering and noise reduction
- Path planning or ROS integration
- Hardware schematics and 3D mount designs
- Bug fixes and documentation improvements

## Guidelines

- Keep Python code compliant with standard PEP 8.
- Ensure Arduino sketches compile without errors in Arduino IDE.
- Do not commit build artifacts, cache files, or temp files.
