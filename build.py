#!/usr/bin/env python3
"""
CS2-Chatbot Build Script
Builds a portable executable using PyInstaller
"""

import os
import shutil
import subprocess
import sys

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist']  # Don't clean spec files
    files_to_clean = []  # Don't clean spec files
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    import glob
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            print(f"Cleaning {file}...")
            os.remove(file)

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Use the spec file for more control
    cmd = [
        'pyinstaller',
        '--noconfirm',                 # Overwrite without asking
        'CS2-Chatbot.spec'            # Use the custom spec file
    ]
    
    print("Building CS2-Chatbot executable using spec file...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def post_build_cleanup():
    """Clean up after build and organize output"""
    if os.path.exists('dist/CS2-Chatbot.exe'):
        print("\n✅ Build completed successfully!")
        print(f"📁 Executable location: {os.path.abspath('dist/CS2-Chatbot.exe')}")
        
        # Get file size
        size = os.path.getsize('dist/CS2-Chatbot.exe')
        size_mb = size / (1024 * 1024)
        print(f"📊 File size: {size_mb:.1f} MB")
        
        # Create a release folder with additional files
        release_dir = 'release'
        if os.path.exists(release_dir):
            shutil.rmtree(release_dir)
        os.makedirs(release_dir)
        
        # Copy executable
        shutil.copy2('dist/CS2-Chatbot.exe', 'release/')
        
        # Copy important files
        files_to_copy = ['README.md', 'LICENSE']
        for file in files_to_copy:
            if os.path.exists(file):
                shutil.copy2(file, 'release/')
        
        print(f"📦 Release package created in: {os.path.abspath('release')}")
        print("\nFiles in release package:")
        for file in os.listdir('release'):
            print(f"  - {file}")
            
    else:
        print("❌ Build failed - executable not found")

if __name__ == "__main__":
    print("🚀 CS2-Chatbot Build Process Starting...")
    print("=" * 50)
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️ Warning: Not running in virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborting build.")
            sys.exit(1)
    
    # Build process
    print("\n1. Cleaning previous builds...")
    clean_build()
    
    print("\n2. Building executable...")
    success = build_executable()
    
    if success:
        print("\n3. Post-build cleanup...")
        post_build_cleanup()
    else:
        print("\n❌ Build process failed!")
        sys.exit(1)
    
    print("\n🎉 Build process completed!")
