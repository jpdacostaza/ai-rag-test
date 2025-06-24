#!/usr/bin/env python3
"""
One-Command Setup for OpenWebUI API Keys
Quick setup wizard that guides users through the entire process.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("🚀 OpenWebUI API Key Quick Setup")
    print("=" * 40)
    print("This wizard will help you set up API key management in 3 easy steps!")
    print()

def check_system():
    """Detect the operating system and available tools."""
    system = "windows" if os.name == 'nt' else "unix"
    
    # Check for PowerShell on Windows
    has_powershell = False
    if system == "windows":
        try:
            result = subprocess.run(["pwsh", "-Command", "echo 'test'"], 
                                  capture_output=True, text=True, timeout=5)
            has_powershell = result.returncode == 0
        except:
            try:
                result = subprocess.run(["powershell", "-Command", "echo 'test'"], 
                                      capture_output=True, text=True, timeout=5)
                has_powershell = result.returncode == 0
            except:
                pass
    
    return system, has_powershell

def run_setup_script(system, has_powershell):
    """Run the appropriate setup script."""
    script_dir = Path(__file__).parent
    
    if system == "windows" and has_powershell:
        print("🪟 Running PowerShell setup script...")
        ps_script = script_dir / "setup-api-keys.ps1"
        if ps_script.exists():
            try:
                subprocess.run(["pwsh", "-File", str(ps_script)], check=True)
                return True
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(["powershell", "-File", str(ps_script)], check=True)
                    return True
                except subprocess.CalledProcessError:
                    print("❌ PowerShell script failed")
                    return False
        else:
            print("❌ PowerShell script not found")
            return False
    else:
        # Try bash script
        bash_script = script_dir / "setup-api-keys.sh"
        if bash_script.exists():
            print("🐧 Running bash setup script...")
            try:
                # Make executable first
                os.chmod(bash_script, 0o755)
                subprocess.run([str(bash_script)], check=True)
                return True
            except subprocess.CalledProcessError:
                print("❌ Bash script failed")
                return False
        else:
            print("❌ Bash script not found")
            return False

def run_python_setup():
    """Fallback to Python setup."""
    script_dir = Path(__file__).parent
    api_manager = script_dir / "api_key_manager.py"
    
    if api_manager.exists():
        print("🐍 Running Python setup script...")
        try:
            subprocess.run([sys.executable, str(api_manager)], check=True)
            return True
        except subprocess.CalledProcessError:
            print("❌ Python setup failed")
            return False
    else:
        print("❌ Python setup script not found")
        return False

def show_quick_options():
    """Show quick setup options."""
    print("\n📋 Quick Setup Options:")
    print()
    print("1. 🔑 Set environment variables (fastest)")
    print("2. 📝 Interactive Python setup (recommended)")
    print("3. 📄 Manual configuration file")
    print("4. 🧪 Just test current setup")
    print("5. 📖 View documentation")
    print("6. ❌ Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-6): ").strip()
            if choice in "123456":
                return int(choice)
            else:
                print("Please enter a number between 1 and 6.")
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            return 6

def setup_env_vars():
    """Quick environment variable setup."""
    print("\n🔧 Environment Variable Setup")
    print("-" * 30)
    
    api_key = input("Enter your OpenWebUI API key: ").strip()
    if not api_key:
        print("❌ No API key provided.")
        return False
    
    base_url = input("Enter base URL [http://localhost:3000]: ").strip()
    if not base_url:
        base_url = "http://localhost:3000"
    
    # Set for current session
    os.environ["OPENWEBUI_API_KEY"] = api_key
    os.environ["OPENWEBUI_BASE_URL"] = base_url
    
    print("\n✅ Environment variables set for this session!")
    
    # Show instructions for permanent setup
    print("\n💡 To make these permanent:")
    if os.name == 'nt':
        print(f"   PowerShell: $env:OPENWEBUI_API_KEY='{api_key}'")
        print(f"              $env:OPENWEBUI_BASE_URL='{base_url}'")
    else:
        print(f"   Bash: export OPENWEBUI_API_KEY='{api_key}'")
        print(f"         export OPENWEBUI_BASE_URL='{base_url}'")
        print("   Add these to your ~/.bashrc or ~/.zshrc")
    
    return True

def create_config_file():
    """Help create configuration file."""
    script_dir = Path(__file__).parent
    example_file = script_dir / "openwebui_api_keys.example.json"
    config_file = script_dir / "openwebui_api_keys.json"
    
    if config_file.exists():
        overwrite = input("Configuration file exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            return False
    
    if example_file.exists():
        print("\n📄 Creating configuration file from example...")
        try:
            import shutil
            shutil.copy(example_file, config_file)
            print(f"✅ Created {config_file}")
            print(f"📝 Please edit {config_file} with your API keys")
            
            # Try to open in default editor
            if os.name == 'nt':
                os.startfile(config_file)
            else:
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.run([editor, str(config_file)])
            
            return True
        except Exception as e:
            print(f"❌ Error creating config file: {e}")
            return False
    else:
        print("❌ Example configuration file not found")
        return False

def test_current_setup():
    """Test the current configuration."""
    script_dir = Path(__file__).parent
    diagnostic = script_dir / "debug" / "demo-tests" / "debug-tools" / "openwebui_memory_diagnostic.py"
    
    if diagnostic.exists():
        print("\n🧪 Testing current setup...")
        try:
            subprocess.run([sys.executable, str(diagnostic)], check=True)
            return True
        except subprocess.CalledProcessError:
            print("❌ Test failed. Check your configuration.")
            return False
    else:
        print("❌ Diagnostic tool not found")
        return False

def show_documentation():
    """Show available documentation."""
    script_dir = Path(__file__).parent
    docs = [
        ("API_KEY_MANAGEMENT.md", "Complete API key documentation"),
        ("SHELL_SCRIPTS_GUIDE.md", "Shell script usage guide"),
        ("openwebui_api_keys.example.json", "Example configuration"),
    ]
    
    print("\n📖 Available Documentation:")
    for filename, description in docs:
        file_path = script_dir / filename
        status = "✅" if file_path.exists() else "❌"
        print(f"   {status} {filename} - {description}")
    
    print(f"\n📁 All files are in: {script_dir}")

def main():
    """Main setup wizard."""
    print_banner()
    
    # Step 1: Check system
    print("Step 1: Detecting system...")
    system, has_powershell = check_system()
    print(f"   🖥️  System: {system}")
    if system == "windows":
        print(f"   💻 PowerShell: {'✅ Available' if has_powershell else '❌ Not found'}")
    print()
    
    # Step 2: Try shell script first
    print("Step 2: Checking for shell scripts...")
    if run_setup_script(system, has_powershell):
        print("✅ Shell script setup completed!")
        return
    
    # Step 3: Fallback to quick options
    print("Step 3: Quick setup options...")
    
    while True:
        choice = show_quick_options()
        
        if choice == 1:
            if setup_env_vars():
                print("\n🎉 Setup complete! Try running a diagnostic test.")
                break
        elif choice == 2:
            if run_python_setup():
                print("\n🎉 Python setup completed!")
                break
        elif choice == 3:
            if create_config_file():
                print("\n🎉 Configuration file created!")
                break
        elif choice == 4:
            test_current_setup()
        elif choice == 5:
            show_documentation()
        elif choice == 6:
            print("👋 Goodbye!")
            break
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled. Run again anytime!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the documentation or run the individual setup scripts.")
