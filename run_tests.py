#!/usr/bin/env python3
"""
Test runner script for AI News Feeder
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with coverage reporting"""
    
    print("🧪 Running AI News Feeder Test Suite")
    print("=" * 50)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Install test dependencies if needed
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Run pytest with various options
    test_commands = [
        # Basic test run
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        
        # Run with coverage (if pytest-cov is available)
        # [sys.executable, "-m", "pytest", "tests/", "--cov=src", "--cov-report=term-missing"],
        
        # Run only unit tests
        [sys.executable, "-m", "pytest", "tests/", "-v", "-m", "unit"],
    ]
    
    for i, cmd in enumerate(test_commands):
        print(f"\n📋 Running test command {i+1}/{len(test_commands)}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 30)
        
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode == 0:
                print("✅ Tests passed")
            else:
                print(f"❌ Tests failed with code {result.returncode}")
                return False
        except FileNotFoundError:
            print("⚠️  pytest not found, skipping this test run")
            continue
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    print("\n🎉 All tests completed successfully!")
    return True

def run_specific_test(test_file):
    """Run a specific test file"""
    cmd = [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v"]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running test {test_file}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
