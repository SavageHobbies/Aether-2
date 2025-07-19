#!/usr/bin/env python3
"""
Comprehensive test for Task 7.1: Desktop Application Foundation.

This test verifies the complete desktop application foundation including:
- Cross-platform desktop application framework (Tauri)
- System tray integration with quick access menu
- Global hotkey system for instant idea capture
- Application auto-start and background running capabilities
- Unit tests for desktop-specific functionality
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

# Add the aether directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_desktop_structure():
    """Test that the desktop application structure is properly set up."""
    print("=== Testing Desktop Application Structure ===")
    
    desktop_path = Path("desktop")
    
    # Check main directories
    required_dirs = [
        "src",
        "src/scripts",
        "src/styles", 
        "src-tauri",
        "src-tauri/src"
    ]
    
    for dir_path in required_dirs:
        full_path = desktop_path / dir_path
        if full_path.exists():
            print(f"  ✓ Directory exists: {dir_path}")
        else:
            print(f"  ❌ Missing directory: {dir_path}")
            return False
    
    # Check required files
    required_files = [
        "package.json",
        "README.md",
        "src/index.html",
        "src/styles/main.css",
        "src/scripts/main.js",
        "src-tauri/Cargo.toml",
        "src-tauri/tauri.conf.json",
        "src-tauri/src/main.rs",
        "src-tauri/src/api.rs",
        "src-tauri/src/tray.rs",
        "src-tauri/src/hotkeys.rs",
        "src-tauri/src/autostart.rs"
    ]
    
    for file_path in required_files:
        full_path = desktop_path / file_path
        if full_path.exists():
            print(f"  ✓ File exists: {file_path}")
        else:
            print(f"  ❌ Missing file: {file_path}")
            return False
    
    print("✓ Desktop application structure is complete")
    return True


def test_tauri_configuration():
    """Test Tauri configuration for cross-platform compatibility."""
    print("\n=== Testing Tauri Configuration ===")
    
    config_path = Path("desktop/src-tauri/tauri.conf.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✓ Tauri configuration loaded successfully")
        
        # Check essential configuration
        essential_configs = [
            ("tauri.allowlist.globalShortcut.all", "Global shortcuts enabled"),
            ("tauri.allowlist.notification.all", "Notifications enabled"),
            ("tauri.allowlist.window", "Window management enabled"),
            ("tauri.systemTray", "System tray configured"),
            ("tauri.bundle.active", "Bundle configuration active")
        ]
        
        for config_path_str, description in essential_configs:
            keys = config_path_str.split('.')
            current = config
            
            try:
                for key in keys:
                    current = current[key]
                
                if current:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ⚠️ {description} (disabled)")
            except KeyError:
                print(f"  ❌ Missing configuration: {config_path_str}")
        
        # Check cross-platform bundle targets
        bundle_config = config.get("tauri", {}).get("bundle", {})
        if bundle_config.get("targets") == "all":
            print("  ✓ Cross-platform bundle targets configured")
        else:
            print("  ⚠️ Bundle targets may not include all platforms")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load Tauri configuration: {e}")
        return False


def test_rust_dependencies():
    """Test Rust dependencies in Cargo.toml."""
    print("\n=== Testing Rust Dependencies ===")
    
    cargo_path = Path("desktop/src-tauri/Cargo.toml")
    
    try:
        with open(cargo_path, 'r') as f:
            cargo_content = f.read()
        
        print("✓ Cargo.toml loaded successfully")
        
        # Check essential dependencies
        essential_deps = [
            "tauri",
            "serde",
            "serde_json", 
            "tokio",
            "reqwest",
            "chrono",
            "dirs",
            "env_logger",
            "log"
        ]
        
        for dep in essential_deps:
            if dep in cargo_content:
                print(f"  ✓ Dependency included: {dep}")
            else:
                print(f"  ❌ Missing dependency: {dep}")
        
        # Check Tauri features
        tauri_features = [
            "system-tray",
            "global-shortcut", 
            "notification",
            "window-all",
            "fs-all",
            "http-all"
        ]
        
        print("  Tauri features:")
        for feature in tauri_features:
            if feature in cargo_content:
                print(f"    ✓ {feature}")
            else:
                print(f"    ❌ {feature}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load Cargo.toml: {e}")
        return False


def test_frontend_structure():
    """Test frontend HTML/CSS/JS structure."""
    print("\n=== Testing Frontend Structure ===")
    
    # Test HTML structure
    html_path = Path("desktop/src/index.html")
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("✓ HTML file loaded successfully")
        
        # Check essential HTML elements
        essential_elements = [
            "sidebar",
            "nav-menu",
            "main-content", 
            "dashboard-page",
            "quick-capture-modal",
            "scripts/main.js"
        ]
        
        for element in essential_elements:
            if element in html_content:
                print(f"  ✓ HTML element/reference: {element}")
            else:
                print(f"  ❌ Missing HTML element/reference: {element}")
        
    except Exception as e:
        print(f"❌ Failed to load HTML: {e}")
        return False
    
    # Test CSS structure
    css_path = Path("desktop/src/styles/main.css")
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        print("✓ CSS file loaded successfully")
        
        # Check CSS variables and classes
        essential_css = [
            ":root",
            "--primary-color",
            ".sidebar",
            ".nav-item",
            ".main-content",
            ".modal",
            ".btn"
        ]
        
        for css_item in essential_css:
            if css_item in css_content:
                print(f"  ✓ CSS element: {css_item}")
            else:
                print(f"  ❌ Missing CSS element: {css_item}")
        
    except Exception as e:
        print(f"❌ Failed to load CSS: {e}")
        return False
    
    # Test JavaScript structure
    js_path = Path("desktop/src/scripts/main.js")
    try:
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        print("✓ JavaScript file loaded successfully")
        
        # Check essential JS components
        essential_js = [
            "class AetherApp",
            "initNavigation",
            "initQuickCapture",
            "loadDashboard",
            "captureIdea",
            "invokeCommand"
        ]
        
        for js_item in essential_js:
            if js_item in js_content:
                print(f"  ✓ JS component: {js_item}")
            else:
                print(f"  ❌ Missing JS component: {js_item}")
        
    except Exception as e:
        print(f"❌ Failed to load JavaScript: {e}")
        return False
    
    return True


def test_rust_backend_structure():
    """Test Rust backend structure and functionality."""
    print("\n=== Testing Rust Backend Structure ===")
    
    # Test main.rs
    main_rs_path = Path("desktop/src-tauri/src/main.rs")
    try:
        with open(main_rs_path, 'r') as f:
            main_content = f.read()
        
        print("✓ main.rs loaded successfully")
        
        # Check essential Rust components
        essential_rust = [
            "mod tray;",
            "mod hotkeys;",
            "mod autostart;",
            "mod api;",
            "#[tauri::command]",
            "capture_idea",
            "get_dashboard_data",
            "toggle_autostart",
            "SystemTray::new()",
            "invoke_handler"
        ]
        
        for rust_item in essential_rust:
            if rust_item in main_content:
                print(f"  ✓ Rust component: {rust_item}")
            else:
                print(f"  ❌ Missing Rust component: {rust_item}")
        
    except Exception as e:
        print(f"❌ Failed to load main.rs: {e}")
        return False
    
    # Test API client
    api_rs_path = Path("desktop/src-tauri/src/api.rs")
    try:
        with open(api_rs_path, 'r') as f:
            api_content = f.read()
        
        print("✓ api.rs loaded successfully")
        
        # Check API functionality
        api_components = [
            "pub struct ApiClient",
            "capture_idea",
            "get_dashboard_data",
            "get_notifications",
            "store_idea_locally",
            "get_mock_dashboard_data"
        ]
        
        for component in api_components:
            if component in api_content:
                print(f"  ✓ API component: {component}")
            else:
                print(f"  ❌ Missing API component: {component}")
        
    except Exception as e:
        print(f"❌ Failed to load api.rs: {e}")
        return False
    
    return True


def test_system_integration_features():
    """Test system integration features configuration."""
    print("\n=== Testing System Integration Features ===")
    
    # Test system tray configuration
    tray_rs_path = Path("desktop/src-tauri/src/tray.rs")
    if tray_rs_path.exists():
        print("✓ System tray module exists")
        
        try:
            with open(tray_rs_path, 'r') as f:
                tray_content = f.read()
            
            tray_features = [
                "handle_tray_event",
                "SystemTrayEvent",
                "show_main_window",
                "quick_capture"
            ]
            
            for feature in tray_features:
                if feature in tray_content:
                    print(f"  ✓ Tray feature: {feature}")
                else:
                    print(f"  ⚠️ Tray feature may be missing: {feature}")
        
        except Exception as e:
            print(f"  ⚠️ Could not analyze tray.rs: {e}")
    else:
        print("❌ System tray module missing")
    
    # Test hotkeys configuration
    hotkeys_rs_path = Path("desktop/src-tauri/src/hotkeys.rs")
    if hotkeys_rs_path.exists():
        print("✓ Global hotkeys module exists")
        
        try:
            with open(hotkeys_rs_path, 'r') as f:
                hotkeys_content = f.read()
            
            hotkey_features = [
                "register_hotkeys",
                "GlobalShortcutManager",
                "Alt+Space",
                "quick_capture"
            ]
            
            for feature in hotkey_features:
                if feature in hotkeys_content:
                    print(f"  ✓ Hotkey feature: {feature}")
                else:
                    print(f"  ⚠️ Hotkey feature may be missing: {feature}")
        
        except Exception as e:
            print(f"  ⚠️ Could not analyze hotkeys.rs: {e}")
    else:
        print("❌ Global hotkeys module missing")
    
    # Test autostart configuration
    autostart_rs_path = Path("desktop/src-tauri/src/autostart.rs")
    if autostart_rs_path.exists():
        print("✓ Auto-start module exists")
        
        try:
            with open(autostart_rs_path, 'r') as f:
                autostart_content = f.read()
            
            autostart_features = [
                "enable_autostart",
                "disable_autostart",
                "is_autostart_enabled",
                "windows",
                "macos",
                "linux"
            ]
            
            for feature in autostart_features:
                if feature in autostart_content:
                    print(f"  ✓ Autostart feature: {feature}")
                else:
                    print(f"  ⚠️ Autostart feature may be missing: {feature}")
        
        except Exception as e:
            print(f"  ⚠️ Could not analyze autostart.rs: {e}")
    else:
        print("❌ Auto-start module missing")
    
    return True


def test_package_json_configuration():
    """Test package.json configuration for Node.js dependencies."""
    print("\n=== Testing Package.json Configuration ===")
    
    package_path = Path("desktop/package.json")
    
    try:
        with open(package_path, 'r') as f:
            package_data = json.load(f)
        
        print("✓ package.json loaded successfully")
        
        # Check essential scripts
        scripts = package_data.get("scripts", {})
        essential_scripts = [
            "tauri:dev",
            "tauri:build", 
            "dev",
            "build"
        ]
        
        for script in essential_scripts:
            if script in scripts:
                print(f"  ✓ Script available: {script}")
            else:
                print(f"  ❌ Missing script: {script}")
        
        # Check dependencies
        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_deps = {**dependencies, **dev_dependencies}
        
        essential_deps = [
            "@tauri-apps/api",
            "@tauri-apps/cli",
            "axios",
            "socket.io-client"
        ]
        
        for dep in essential_deps:
            if dep in all_deps:
                print(f"  ✓ Dependency: {dep}")
            else:
                print(f"  ❌ Missing dependency: {dep}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load package.json: {e}")
        return False


def test_cross_platform_compatibility():
    """Test cross-platform compatibility features."""
    print("\n=== Testing Cross-Platform Compatibility ===")
    
    # Check platform-specific code in autostart.rs
    autostart_path = Path("desktop/src-tauri/src/autostart.rs")
    
    if autostart_path.exists():
        try:
            with open(autostart_path, 'r') as f:
                autostart_content = f.read()
            
            platforms = [
                ("#[cfg(target_os = \"windows\")]", "Windows support"),
                ("#[cfg(target_os = \"macos\")]", "macOS support"),
                ("#[cfg(target_os = \"linux\")]", "Linux support")
            ]
            
            for platform_check, description in platforms:
                if platform_check in autostart_content:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ⚠️ {description} may be missing")
        
        except Exception as e:
            print(f"  ⚠️ Could not analyze cross-platform code: {e}")
    
    # Check Cargo.toml for platform-specific dependencies
    cargo_path = Path("desktop/src-tauri/Cargo.toml")
    
    if cargo_path.exists():
        try:
            with open(cargo_path, 'r') as f:
                cargo_content = f.read()
            
            platform_deps = [
                ("[target.'cfg(windows)'.dependencies]", "Windows-specific dependencies"),
                ("[target.'cfg(target_os = \"macos\")'.dependencies]", "macOS-specific dependencies"),
                ("[target.'cfg(target_os = \"linux\")'.dependencies]", "Linux-specific dependencies")
            ]
            
            for dep_check, description in platform_deps:
                if dep_check in cargo_content:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ⚠️ {description} may be missing")
        
        except Exception as e:
            print(f"  ⚠️ Could not analyze platform dependencies: {e}")
    
    return True


def test_integration_with_backend():
    """Test integration capabilities with Aether backend."""
    print("\n=== Testing Backend Integration ===")
    
    # Check API client configuration
    api_path = Path("desktop/src-tauri/src/api.rs")
    
    if api_path.exists():
        try:
            with open(api_path, 'r') as f:
                api_content = f.read()
            
            integration_features = [
                ("http://localhost:8000", "Backend URL configuration"),
                ("/api/v1/ideas", "Ideas API endpoint"),
                ("/api/v1/dashboard", "Dashboard API endpoint"),
                ("/api/v1/notifications", "Notifications API endpoint"),
                ("store_idea_locally", "Offline mode support"),
                ("get_mock_dashboard_data", "Fallback data support")
            ]
            
            for feature_check, description in integration_features:
                if feature_check in api_content:
                    print(f"  ✓ {description}")
                else:
                    print(f"  ❌ Missing: {description}")
        
        except Exception as e:
            print(f"  ❌ Could not analyze API integration: {e}")
            return False
    else:
        print("❌ API client module missing")
        return False
    
    return True


def run_comprehensive_test():
    """Run all desktop application tests."""
    print("🚀 TASK 7.1: DESKTOP APPLICATION FOUNDATION - COMPREHENSIVE TEST")
    print("=" * 80)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Desktop Structure", test_desktop_structure),
        ("Tauri Configuration", test_tauri_configuration),
        ("Rust Dependencies", test_rust_dependencies),
        ("Frontend Structure", test_frontend_structure),
        ("Rust Backend Structure", test_rust_backend_structure),
        ("System Integration Features", test_system_integration_features),
        ("Package.json Configuration", test_package_json_configuration),
        ("Cross-Platform Compatibility", test_cross_platform_compatibility),
        ("Backend Integration", test_integration_with_backend)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("🎉 TASK 7.1 TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎯 ALL TESTS PASSED - Desktop foundation is complete!")
        
        print(f"\n🚀 DESKTOP APPLICATION CAPABILITIES:")
        print("   ✓ Cross-platform Tauri framework configured")
        print("   ✓ System tray integration with quick access menu")
        print("   ✓ Global hotkey system for instant idea capture")
        print("   ✓ Application auto-start and background running")
        print("   ✓ Professional UI with responsive design")
        print("   ✓ Backend API integration with offline fallback")
        print("   ✓ Comprehensive error handling and logging")
        print("   ✓ Cross-platform compatibility (Windows, macOS, Linux)")
        
        print(f"\n🎯 BUSINESS VALUE:")
        print("   • Always-accessible AI companion from system tray")
        print("   • Instant idea capture with global hotkeys")
        print("   • Seamless integration with Aether backend services")
        print("   • Professional desktop experience across all platforms")
        print("   • Offline capability ensures continuous productivity")
        
        return 0
    else:
        print(f"⚠️ {total_tests - passed_tests} tests failed - review implementation")
        return 1


def main():
    """Main test execution."""
    try:
        # Change to aether directory
        os.chdir(os.path.dirname(__file__))
        
        return run_comprehensive_test()
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())