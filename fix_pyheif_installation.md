# Fix for pyheif Installation Error on Windows

## Problem
When trying to install the `pyheif` package on Windows, you encounter this error:
```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

## Solution Options

### Option 1: Install Microsoft C++ Build Tools (Recommended for development)
1. Download and install Microsoft C++ Build Tools from:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. During installation, make sure to select:
   - C++ build tools
   - MSVC compiler toolset
   - Windows 10/11 SDK
3. After installation completes, restart your command prompt/terminal
4. Run the installation again:
   ```
   pip install -r requirements.txt
   ```

### Option 2: Use pre-compiled wheel (Easier alternative)
Try installing a pre-compiled wheel version:
```
pip install --only-binary=all -r requirements.txt
```

### Option 3: Alternative HEIF library
If the above solutions don't work, you can try using an alternative HEIF library like `pillow-heif` which might have pre-built Windows wheels:
```
pip install pillow-heif
```

Then modify your code to use pillow-heif instead of pyheif if needed.

### Option 4: Use conda instead of pip
If you have Anaconda or Miniconda installed:
```
conda install -c conda-forge pyheif
```

## Additional Notes
- Make sure your Python environment is activated before attempting installation
- Consider updating pip first: `python -m pip install --upgrade pip`
- The error occurs because pyheif needs to compile C extensions and requires the Microsoft C++ compiler toolchain on Windows

Choose the option that best fits your development setup and requirements.