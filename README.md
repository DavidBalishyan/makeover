# Makeover

Makeover is a simple, user-friendly build system wrapper designed to be a cleaner alternative to Make. It uses a simplified syntax in a `buildfile` to manage your project's build targets and dependencies.

## Features

- **Simple Syntax**: Cleaner and less cluttered than Makefile.
- **Python-Powered**: Written in Python, easy to extend.
- **Dependencies**: Supports target dependencies (DAG execution).
- **Variables**: Simple variable substitution (`${VAR}`).
- **Smart Builds**: Checks file modification times to skip unnecessary rebuilds.
- **Listing**: View available targets with `-l` or `--list`.

## Installation

You can install Makeover using itself!

1. Clone the repository:

   ```bash
   git clone https://github.com/DavidBalishyan/makeover.git
   cd makeover
   ```

2. Run the install target:
   ```bash
   ./main.py
   ```

This will install the `makeover` binary to `~/.local/bin`. Ensure this directory is in your `$PATH`.

## Usage

Create a file named `buildfile` in your project root.

### Example `buildfile`

```makefile
# Define variables
CC = python3
SRC = main.py

# Default target
all: test

# A target with dependencies
test:
    echo "Running tests..."
    ${CC} ${SRC} --version

# Simple cleanup target
clean:
    rm -rf *.o
```

### Documentation and Groups

You can document your targets with comments starting with `#` right before the target. You can also group targets using `[group: Name]`.

```makefile
[group: Main]
# Run the application
run:
    python3 main.py

[group: Utils]
# Clean up
clean:
    rm -rf build/
```

### Running Targets

Run a specific target:

```bash
makeover test
```

Run the default target (first one in file):

```bash
makeover
```

List available targets (with colors and grouping):

```bash
makeover -l
```
