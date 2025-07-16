"""
Code cleanup utility for maintaining code quality.
Removes temporary files, unused imports, and performs basic formatting checks.
"""

import os
import shutil
import glob
import time
from pathlib import Path

def cleanup_temp_files():
    """Remove temporary files and test databases"""
    patterns_to_remove = [
        "test_*.db",
        "*.pyc",
        "__pycache__",
        "*.log",
        ".pytest_cache"
    ]
    
    removed_count = 0
    
    for pattern in patterns_to_remove:
        if pattern == "__pycache__":
            # Remove __pycache__ directories
            for root, dirs, files in os.walk("."):
                for dir_name in dirs:
                    if dir_name == "__pycache__":
                        dir_path = os.path.join(root, dir_name)
                        try:
                            shutil.rmtree(dir_path)
                            print(f"Removed directory: {dir_path}")
                            removed_count += 1
                        except Exception as e:
                            print(f"Failed to remove {dir_path}: {e}")
        else:
            # Remove files matching pattern
            for file_path in glob.glob(pattern):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Removed file: {file_path}")
                        removed_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"Removed directory: {file_path}")
                        removed_count += 1
                except Exception as e:
                    print(f"Failed to remove {file_path}: {e}")
    
    return removed_count

def check_code_structure():
    """Check basic code structure and provide maintenance suggestions"""
    python_files = list(Path(".").glob("**/*.py"))
    
    print(f"\nCode Structure Analysis:")
    print(f"Python files found: {len(python_files)}")
    
    # Check for proper imports
    import_issues = []
    
    for py_file in python_files:
        if py_file.name.startswith(("test_", "fix_", "cleanup_")):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for missing docstrings
                if not content.strip().startswith('"""'):
                    import_issues.append(f"{py_file}: Missing module docstring")
                
                # Check for proper typing imports
                if "Tuple" in content and "from typing import" not in content:
                    import_issues.append(f"{py_file}: Uses Tuple but missing typing import")
                
        except Exception as e:
            import_issues.append(f"{py_file}: Could not analyze - {e}")
    
    if import_issues:
        print("\nPotential Issues Found:")
        for issue in import_issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(import_issues) > 10:
            print(f"  ... and {len(import_issues) - 10} more")
    else:
        print("\n[OK] No obvious code structure issues found")
    
    return len(import_issues)

def optimize_cache():
    """Clean up and optimize cache directory"""
    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("No cache directory found")
        return 0
    
    cache_files = list(cache_dir.glob("*.json"))
    old_cache_count = 0
    
    for cache_file in cache_files:
        # Remove cache files older than 7 days
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > 7 * 24 * 3600:  # 7 days in seconds
            try:
                cache_file.unlink()
                old_cache_count += 1
                print(f"Removed old cache: {cache_file.name}")
            except Exception as e:
                print(f"Failed to remove cache {cache_file}: {e}")
    
    return old_cache_count

def main():
    """Run all cleanup operations"""
    print("Ashes of Creation Artisan Toolbox - Code Cleanup")
    print("=" * 50)
    
    # Clean up temporary files
    print("1. Cleaning temporary files...")
    temp_removed = cleanup_temp_files()
    print(f"   Removed {temp_removed} temporary items")
    
    # Check code structure
    print("\n2. Checking code structure...")
    import time
    issues = check_code_structure()
    
    # Optimize cache
    print("\n3. Optimizing cache...")
    cache_removed = optimize_cache()
    print(f"   Removed {cache_removed} old cache files")
    
    # Summary
    print("\n" + "=" * 50)
    print("CLEANUP SUMMARY")
    print("=" * 50)
    print(f"Temporary files removed: {temp_removed}")
    print(f"Code issues found: {issues}")
    print(f"Old cache files removed: {cache_removed}")
    
    if issues == 0 and temp_removed >= 0:
        print("\n[OK] Cleanup completed successfully!")
    else:
        print(f"\n[WARNING] Found {issues} code issues to review")

if __name__ == "__main__":
    main()