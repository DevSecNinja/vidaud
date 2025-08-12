# Code Quality Configuration

This project uses standardized configuration files for code quality tools to ensure consistency across development environments, CI/CD pipelines, and team members.

## Configuration Files

### `.flake8` - Python Linting Configuration

Contains settings for the flake8 linter:

- **Line length**: 88 characters (consistent with Black)
- **Ignored rules**: E203, W503, E501 (compatibility with Black formatter)
- **Excluded directories**: Git, cache, build artifacts, virtual environments
- **Additional features**: Source display, error counting, complexity checking

### `pyproject.toml` - Tool Configuration

Contains configuration for multiple Python tools:

#### `[tool.black]` - Code Formatting
- **Target versions**: Python 3.11, 3.12
- **Line length**: 88 characters
- **Exclusions**: Build artifacts, virtual environments, dev containers

#### `[tool.pytest.ini_options]` - Testing
- **Test discovery**: Automatic discovery of test files and functions
- **Markers**: Unit, integration, and slow test categorization
- **Coverage**: Source code coverage reporting

#### `[tool.bandit]` - Security Scanning
- **Exclusions**: Test directories (tests often contain intentionally insecure code)
- **Skipped checks**: Assert usage (B101) for test files

#### `[tool.coverage.run]` - Coverage Configuration
- **Source tracking**: Only track `src/` directory
- **Exclusions**: Test files, cache directories

## Usage

### Local Development

All tools automatically pick up their configuration:

```bash
# Linting (uses .flake8 automatically)
make lint

# Formatting (uses pyproject.toml [tool.black] automatically)
make lint-fix

# Testing (uses pyproject.toml [tool.pytest.ini_options] automatically)
make test

# Security (uses pyproject.toml [tool.bandit] automatically)
make security
```

### VS Code DevContainer

The `.devcontainer/devcontainer.json` is configured to use these files automatically:

- Flake8 settings are applied without command-line arguments
- Black formatting uses the project configuration
- Python testing discovers tests according to pytest configuration

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs tools without any additional arguments, relying entirely on the configuration files:

```yaml
# Linting
- name: Lint with flake8
  run: python -m flake8 src/ tests/

# Formatting check
- name: Check formatting with black
  run: python -m black --check src/ tests/

# Security scanning
- name: Security check with bandit
  run: python -m bandit -r src/
```

## Benefits

1. **Consistency**: Same rules across all environments
2. **Maintainability**: Single source of truth for tool configuration
3. **Portability**: Configuration travels with the code
4. **Team Collaboration**: Everyone uses identical settings
5. **CI/CD Integration**: No duplication between local and remote environments

## Configuration Standards

- **Line Length**: 88 characters (Black's default, good balance of readability and efficiency)
- **Python Versions**: Support for 3.11 and 3.12
- **Code Style**: PEP 8 compliant with Black formatting
- **Security**: Bandit scanning with appropriate exclusions
- **Testing**: Comprehensive test discovery with coverage reporting

## Customization

To modify the configuration:

1. **Linting rules**: Edit `.flake8`
2. **Code formatting**: Edit `[tool.black]` in `pyproject.toml`
3. **Test configuration**: Edit `[tool.pytest.ini_options]` in `pyproject.toml`
4. **Security rules**: Edit `[tool.bandit]` in `pyproject.toml`

Changes will automatically apply to:
- Local development (Makefile commands)
- VS Code DevContainer environment
- CI/CD pipeline execution
- Team member environments
