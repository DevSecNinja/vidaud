#!/usr/bin/env python3
"""
Validate that Renovate configuration can detect Python versions correctly.
This script simulates what Renovate regex managers would match.
"""
import json
import re
import yaml
from pathlib import Path


class RenovateValidator:
    """Validate Renovate configuration by testing regex patterns."""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.results = []
        
    def load_renovate_config(self):
        """Load renovate.json configuration."""
        renovate_path = self.repo_root / "renovate.json"
        with open(renovate_path) as f:
            return json.load(f)
            
    def test_github_actions_regex(self, config):
        """Test GitHub Actions workflow regex patterns."""
        print("🔍 Testing GitHub Actions Python version detection...")
        
        # Find the GitHub Actions regex manager
        gh_manager = None
        for manager in config.get("regexManagers", []):
            if "GitHub Actions workflows" in manager.get("description", ""):
                gh_manager = manager
                break
                
        if not gh_manager:
            self.results.append("❌ No GitHub Actions regex manager found")
            return
            
        # Load the CI workflow file
        ci_file = self.repo_root / ".github" / "workflows" / "ci.yml"
        with open(ci_file) as f:
            ci_content = f.read()
            
        # Test each regex pattern
        patterns = gh_manager["matchStrings"]
        matches_found = 0
        
        for pattern in patterns:
            # Convert Renovate named capture groups to Python regex
            # Renovate uses (?<name>...) but Python uses (?P<name>...)
            py_pattern = pattern.replace('(?<currentValue>', '(?P<currentValue>')
            regex = re.compile(py_pattern)
            matches = regex.findall(ci_content)
            if matches:
                matches_found += len(matches)
                print(f"  ✅ Pattern matched: {matches}")
                
        if matches_found > 0:
            self.results.append(f"✅ GitHub Actions: Found {matches_found} Python version references")
        else:
            self.results.append("❌ GitHub Actions: No Python versions detected")
            
    def test_dockerfile_detection(self, config):
        """Test that Docker base image detection works."""
        print("\n🔍 Testing Dockerfile Python version detection...")
        
        # Check if Docker package rule exists
        has_docker_rule = False
        for rule in config.get("packageRules", []):
            if "docker" in rule.get("matchDatasources", []):
                has_docker_rule = True
                break
                
        if has_docker_rule:
            print("  ✅ Docker datasource rule found")
            self.results.append("✅ Dockerfile: Docker base image tracking enabled")
        else:
            self.results.append("❌ Dockerfile: No Docker datasource rule found")
            
    def test_pyproject_regex(self, config):
        """Test pyproject.toml Black configuration regex."""
        print("\n🔍 Testing pyproject.toml Python version detection...")
        
        # Find the pyproject.toml regex manager
        pyproject_manager = None
        for manager in config.get("regexManagers", []):
            if "pyproject.toml" in manager.get("description", ""):
                pyproject_manager = manager
                break
                
        if not pyproject_manager:
            self.results.append("❌ No pyproject.toml regex manager found")
            return
            
        # Load pyproject.toml file
        pyproject_file = self.repo_root / "pyproject.toml"
        with open(pyproject_file) as f:
            pyproject_content = f.read()
            
        # Test the regex pattern
        patterns = pyproject_manager["matchStrings"]
        matches_found = 0
        
        for pattern in patterns:
            # Convert Renovate named capture groups to Python regex
            py_pattern = pattern.replace('(?<currentValue>', '(?P<currentValue>')
            regex = re.compile(py_pattern)
            matches = regex.findall(pyproject_content)
            if matches:
                matches_found += len(matches)
                print(f"  ✅ Pattern matched: {matches}")
                
        if matches_found > 0:
            self.results.append(f"✅ pyproject.toml: Found {matches_found} Python version references")
        else:
            self.results.append("❌ pyproject.toml: No Python versions detected")
            
    def test_devcontainer_regex(self, config):
        """Test DevContainer image regex."""
        print("\n🔍 Testing DevContainer Python version detection...")
        
        # Find the DevContainer regex manager
        devcontainer_manager = None
        for manager in config.get("regexManagers", []):
            if "DevContainer" in manager.get("description", ""):
                devcontainer_manager = manager
                break
                
        if not devcontainer_manager:
            self.results.append("❌ No DevContainer regex manager found")
            return
            
        # Load devcontainer.json file
        devcontainer_file = self.repo_root / ".devcontainer" / "devcontainer.json"
        with open(devcontainer_file) as f:
            devcontainer_content = f.read()
            
        # Test the regex pattern
        patterns = devcontainer_manager["matchStrings"]
        matches_found = 0
        
        for pattern in patterns:
            # Convert Renovate named capture groups to Python regex
            py_pattern = pattern.replace('(?<currentValue>', '(?P<currentValue>')
            regex = re.compile(py_pattern)
            matches = regex.findall(devcontainer_content)
            if matches:
                matches_found += len(matches)
                print(f"  ✅ Pattern matched: {matches}")
                
        if matches_found > 0:
            self.results.append(f"✅ DevContainer: Found {matches_found} Python version references")
        else:
            self.results.append("❌ DevContainer: No Python versions detected")
            
    def validate(self):
        """Run all validation tests."""
        print("🔧 Validating Renovate Python version detection...\n")
        
        try:
            config = self.load_renovate_config()
            
            self.test_github_actions_regex(config)
            self.test_dockerfile_detection(config)
            self.test_pyproject_regex(config)
            self.test_devcontainer_regex(config)
            
        except Exception as e:
            self.results.append(f"❌ Validation failed: {e}")
            
        # Print summary
        print("\n" + "="*50)
        print("📊 VALIDATION SUMMARY")
        print("="*50)
        
        for result in self.results:
            print(result)
            
        success_count = sum(1 for r in self.results if r.startswith("✅"))
        total_count = len(self.results)
        
        print(f"\n🎯 Results: {success_count}/{total_count} checks passed")
        
        if success_count == total_count:
            print("🎉 All validations passed! Renovate should properly track Python versions.")
            return True
        else:
            print("⚠️  Some validations failed. Please check the configuration.")
            return False


if __name__ == "__main__":
    validator = RenovateValidator()
    success = validator.validate()
    exit(0 if success else 1)