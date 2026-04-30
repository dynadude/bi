# bi

## Table of contents

- [Overview](#overview)
- [Usage](#usage)
- [Installation](#installation)
	- [Native](#native)
        - [Windows](#windows)
        - [Linux](#linux)
	- [Python](#python)
- [Building](#building)

## Overview

The bi python script performs a git-bisect-like binary search on the contents of a text file, treating each line as a 'revision' to test.
The text file you should use the script on should not contain duplicates, and be logically-sorted (chronologically for most uses).

**This project is not affiliated with Git™**

## Usage
Basic bi commands include `bi start <file_name>`, `bi bad`, `bi good` and `bi status`.

Please refer to the built-in help text by either running `bi` with no arguments, or running `bi help` for more advanced usage.

## Installation

### Native

This installation method requires no dependencies

#### Windows

1. Download the bi exe file from a release in the [Releases](https://github.com/dynadude/bi/releases) page.
2. Rename the file to `bi.exe`
3. Put the file in either `C:\Windows\System32` for a system-wide installation, or some dir in your `PATH` environment variable for a user-specific installation
  
#### Linux    

1. Download the appropriate binary for your system (FYI, most linux systems use GNU) from a release in the [Releases](https://github.com/dynadude/bi/releases) page.
2. Rename the file to `bi`
3. Put the file in either `/usr/local/bin` for a system-wide installation, or `~/.local/bin` for a user-specific installation

### Python

This installation method requires a pre-existing python3 installation.

**The earliest Python version tested and working was 3.10.0 (bi does not work on 3.9.25 and earlier)**

**This installation Method only works on Linux because it supports shebangs**
  
1. Download the source code from a release in the [Releases](https://github.com/dynadude/bi/releases) page (or just clone the repo and check out the desired revision).
2. Extract the archive (only if downloaded from the [Releases](https://github.com/dynadude/bi/releases) page)
3. Rename `bi.py` to `bi`
4. Put the file in either `/usr/local/bin` for a system-wide installation, or `~/.local/bin` for a user-specific installation

## Building

**Building bi requires a working docker installation**

**The build artifacts are stored in the `dist/` directory**

1. Clone this repository by executing:

```sh
git clone https://github.com/dynadude/bi
```

3. Execute `build.sh`

```sh
./build.sh
```
