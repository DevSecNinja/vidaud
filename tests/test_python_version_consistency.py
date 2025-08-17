"""Test Python version consistency across project files."""
import json
import re
import yaml
from pathlib import Path


class TestPythonVersionConsistency:
    """Test that Python versions are consistent across project configuration files."""
    
    @staticmethod
    def get_repo_root():
        """Get the repository root directory."""
        return Path(__file__).parent.parent
        
    def test_supported_python_versions_in_ci(self):
        """Test that CI workflow defines supported Python versions correctly."""
        ci_file = self.get_repo_root() / ".github" / "workflows" / "ci.yml"
        
        with open(ci_file, 'r') as f:
            ci_config = yaml.safe_load(f)
        
        # Check test matrix
        test_job = ci_config['jobs']['test']
        python_versions = test_job['strategy']['matrix']['python-version']
        
        assert isinstance(python_versions, list), "Python versions should be a list"
        assert len(python_versions) >= 2, "Should support multiple Python versions"
        assert "3.11" in python_versions, "Should support Python 3.11"
        assert "3.12" in python_versions, "Should support Python 3.12"
        
    def test_lint_job_python_version_consistency(self):
        """Test that lint job uses consistent Python version."""
        ci_file = self.get_repo_root() / ".github" / "workflows" / "ci.yml"
        
        with open(ci_file, 'r') as f:
            ci_config = yaml.safe_load(f)
        
        # Check lint job Python version
        lint_job = ci_config['jobs']['lint-and-security-scan']
        setup_python_step = None
        for step in lint_job['steps']:
            if step.get('name') == 'Set up Python':
                setup_python_step = step
                break
                
        assert setup_python_step is not None, "Should have Set up Python step"
        python_version = setup_python_step['with']['python-version']
        
        # Should use latest supported version (3.12)
        assert python_version == "3.12", f"Lint job should use Python 3.12, got {python_version}"
        
    def test_dockerfile_python_version_consistency(self):
        """Test that Dockerfile uses consistent Python version."""
        dockerfile = self.get_repo_root() / "Dockerfile"
        
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Find all Python base image references
        python_images = re.findall(r'FROM python:(\d+\.\d+(?:\.\d+)?)-slim', content)
        
        assert len(python_images) >= 2, "Dockerfile should have multiple Python base images"
        
        # All should use the same version
        unique_versions = set(python_images)
        assert len(unique_versions) == 1, f"All Python images should use same version, got {unique_versions}"
        
        # Should use our standardized version (3.12)
        version = python_images[0]
        assert version == "3.12", f"Dockerfile should use Python 3.12, got {version}"
        
    def test_devcontainer_python_version(self):
        """Test that devcontainer uses supported Python version."""
        devcontainer_file = self.get_repo_root() / ".devcontainer" / "devcontainer.json"
        
        with open(devcontainer_file, 'r') as f:
            devcontainer_config = json.load(f)
        
        image = devcontainer_config['image']
        
        # Should use Python 3.12
        assert "3.12" in image, f"DevContainer should use Python 3.12, got {image}"
        
    def test_pyproject_black_target_versions(self):
        """Test that pyproject.toml Black configuration uses consistent Python versions."""
        pyproject_file = self.get_repo_root() / "pyproject.toml"
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # Find Black target versions
        match = re.search(r"target-version\s*=\s*\[(.*?)\]", content)
        assert match, "Should find Black target-version configuration"
        
        target_versions_str = match.group(1)
        target_versions = [v.strip().strip("'\"") for v in target_versions_str.split(",")]
        
        # Should support py311 and py312
        assert "py311" in target_versions, "Black should target Python 3.11"
        assert "py312" in target_versions, "Black should target Python 3.12"
        
    def test_renovate_configuration_has_python_managers(self):
        """Test that Renovate configuration includes Python version tracking."""
        renovate_file = self.get_repo_root() / "renovate.json"
        
        with open(renovate_file, 'r') as f:
            renovate_config = json.load(f)
        
        # Should have regexManagers for Python versions
        assert "regexManagers" in renovate_config, "Should have regexManagers"
        
        regex_managers = renovate_config["regexManagers"]
        
        # Check for GitHub Actions Python version manager
        gh_actions_manager = None
        for manager in regex_managers:
            if "GitHub Actions workflows" in manager.get("description", ""):
                gh_actions_manager = manager
                break
                
        assert gh_actions_manager is not None, "Should have GitHub Actions Python version manager"
        assert ".github/workflows/" in str(gh_actions_manager["fileMatch"]), "Should match workflow files"
        
        # Check for Dockerfile manager
        dockerfile_manager = None
        for manager in regex_managers:
            if "Dockerfile" in manager.get("description", ""):
                dockerfile_manager = manager
                break
                
        assert dockerfile_manager is not None, "Should have Dockerfile Python version manager"