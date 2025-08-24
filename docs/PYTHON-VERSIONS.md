# Python Version Management

This document describes how Python versions are managed across the vidaud project and how Renovate automatically tracks and updates them.

## Supported Python Versions

The project currently supports:
- **Python 3.11** - Minimum supported version
- **Python 3.12** - Primary/latest supported version

## Version Definitions

Python versions are defined in the following files:

### 1. CI/CD Pipeline (`.github/workflows/ci.yml`)
- **Test Matrix**: Tests run on both Python 3.11 and 3.12 to ensure compatibility
- **Lint Job**: Uses Python 3.12 (latest supported version) for linting and security checks
- **Coverage**: Uploads coverage from Python 3.12 builds

### 2. Docker Configuration (`Dockerfile`)
- **Base Images**: Uses `python:3.12-slim` for consistent containerized deployments
- **Multi-stage Build**: Both builder and final stages use the same Python version

### 3. Development Environment (`.devcontainer/devcontainer.json`)
- **DevContainer**: Uses Python 3.12 for consistent development experience
- **Extensions**: Configured for Python 3.12 tooling

### 4. Tool Configuration (`pyproject.toml`)
- **Black Formatter**: Targets `py311` and `py312` for code formatting
- **Test Configuration**: Supports all configured Python versions

## Renovate Integration

The project uses Renovate to automatically track and update Python versions across all files.

### Configuration (`renovate.json`)

#### Package Rules
- Groups all Python version updates under "Python version updates"
- Requires manual review (auto-merge disabled)
- Schedules updates for Sundays to minimize disruption

#### Regex Managers
Renovate uses custom regex managers to detect Python versions in:

1. **GitHub Actions Workflows**
   - Matches `python-version: "X.Y"` and matrix arrays
   - Updates both single versions and version arrays

2. **pyproject.toml Black Configuration**
   - Matches `target-version = ['pyXXX', 'pyXXX']` patterns
   - Maintains Black formatter compatibility

3. **DevContainer Images**
   - Matches Python versions in Microsoft DevContainer base images
   - Ensures development environment stays current

### Update Process

When a new Python version is released:

1. **Renovate Detection**: Custom regex managers detect version references
2. **PR Creation**: Renovate creates a single PR grouping all Python version updates
3. **Manual Review**: Team reviews the PR (auto-merge disabled for major changes)
4. **Automated Testing**: CI runs tests on all supported versions
5. **Version Consistency**: All files are updated simultaneously

## Testing Version Consistency

The project includes automated tests (`tests/test_python_version_consistency.py`) that verify:

- CI workflow defines correct Python versions
- Dockerfile uses consistent Python version
- DevContainer uses supported Python version
- pyproject.toml targets correct Python versions
- Renovate configuration includes all necessary managers

## Adding New Python Versions

To add support for a new Python version:

1. **Update CI Matrix**: Add the version to the test matrix in `.github/workflows/ci.yml`
2. **Update Black Config**: Add the corresponding `pyXXX` target in `pyproject.toml`
3. **Consider Docker Update**: Update Dockerfile if the new version should be the primary
4. **Run Tests**: Ensure all tests pass with the new version
5. **Update Documentation**: Update this file and any version requirements

## Version Upgrade Strategy

### Minor Version Updates (e.g., 3.12.1 → 3.12.2)
- Automatically handled by Renovate digest updates
- Can be auto-merged for patch updates

### Major Version Updates (e.g., 3.12 → 3.13)
- Require manual review and testing
- Should update all files simultaneously
- May require code changes for compatibility

## Troubleshooting

### Version Inconsistency
If Python versions become inconsistent across files:
1. Run `python -m pytest tests/test_python_version_consistency.py -v`
2. Check which files have mismatched versions
3. Update manually or wait for next Renovate run

### Renovate Not Detecting Updates
Check that:
- Regex patterns match the current file format
- File paths in `fileMatch` are correct
- GitHub Actions and Docker datasources are enabled

### CI Failures After Version Update
1. Check if new Python version has breaking changes
2. Update dependencies that may not support the new version
3. Consider updating code for compatibility issues

## Best Practices

1. **Keep Versions Synchronized**: All files should use consistent Python versions
2. **Test Thoroughly**: Always test new Python versions with the full test suite
3. **Update Dependencies**: Check that all dependencies support new Python versions
4. **Document Changes**: Update documentation when changing supported versions
5. **Gradual Migration**: When dropping support for older versions, do so gradually