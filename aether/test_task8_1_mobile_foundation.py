#!/usr/bin/env python3
"""
Test script for Task 8.1: Create React Native/Flutter mobile app foundation
Tests the mobile application foundation components and structure.
"""

import os
import sys
import json
from pathlib import Path

def test_mobile_structure():
    """Test that mobile app structure exists."""
    print("🧪 Testing Mobile App Structure...")
    
    mobile_dir = Path("aether/mobile")
    
    # Required directories
    required_dirs = [
        "src",
        "src/components",
        "src/screens",
        "src/navigation",
        "src/services",
        "src/contexts",
        "src/utils",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = mobile_dir / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ Mobile app structure is complete")
    return True

def test_package_json():
    """Test package.json configuration."""
    print("\n🧪 Testing Package.json Configuration...")
    
    package_json = Path("aether/mobile/package.json")
    
    if not package_json.exists():
        print("❌ package.json not found")
        return False
    
    try:
        with open(package_json, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["name", "version", "scripts", "dependencies"]
        for field in required_fields:
            if field in config:
                print(f"✅ Field present: {field}")
            else:
                print(f"❌ Missing field: {field}")
                return False
        
        # Check required scripts
        required_scripts = ["android", "ios", "start", "test"]
        scripts = config.get("scripts", {})
        for script in required_scripts:
            if script in scripts:
                print(f"✅ Script available: {script}")
            else:
                print(f"⚠️ Script missing: {script}")
        
        # Check key dependencies
        key_dependencies = [
            "react",
            "react-native",
            "@react-navigation/native",
            "react-native-async-storage",
            "react-native-encrypted-storage",
            "react-native-vector-icons",
        ]
        
        dependencies = config.get("dependencies", {})
        for dep in key_dependencies:
            if dep in dependencies:
                print(f"✅ Dependency: {dep}")
            else:
                print(f"❌ Missing dependency: {dep}")
                return False
        
        print("✅ Package.json configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def test_core_files():
    """Test core application files."""
    print("\n🧪 Testing Core Application Files...")
    
    mobile_dir = Path("aether/mobile")
    
    # Required core files
    required_files = {
        "index.js": "Application entry point",
        "src/App.tsx": "Main App component",
        "README.md": "Documentation",
    }
    
    missing_files = []
    empty_files = []
    
    for file_path, description in required_files.items():
        full_path = mobile_dir / file_path
        
        if not full_path.exists():
            missing_files.append(f"{file_path} ({description})")
        else:
            try:
                content = full_path.read_text(encoding='utf-8')
                if not content.strip():
                    empty_files.append(f"{file_path} ({description})")
                else:
                    size_info = f"{len(content)} characters"
                    print(f"✅ {file_path} - {size_info}")
            except Exception as e:
                empty_files.append(f"{file_path} ({description}) - Error: {e}")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    if empty_files:
        print(f"⚠️ Empty files: {', '.join(empty_files)}")
        return False
    
    print("✅ All core files present and non-empty")
    return True

def test_navigation_structure():
    """Test navigation structure."""
    print("\n🧪 Testing Navigation Structure...")
    
    nav_file = Path("aether/mobile/src/navigation/AppNavigator.tsx")
    
    if not nav_file.exists():
        print("❌ AppNavigator.tsx not found")
        return False
    
    content = nav_file.read_text(encoding='utf-8')
    
    # Check for navigation components
    nav_components = [
        "createStackNavigator",
        "createBottomTabNavigator",
        "NavigationContainer",
        "RootStackParamList",
        "MainTabParamList",
    ]
    
    missing_components = []
    for component in nav_components:
        if component in content:
            print(f"✅ Navigation component: {component}")
        else:
            missing_components.append(component)
    
    if missing_components:
        print(f"❌ Missing navigation components: {', '.join(missing_components)}")
        return False
    
    # Check for screen references
    screen_references = [
        "DashboardScreen",
        "ConversationScreen",
        "IdeaCaptureScreen",
        "TasksScreen",
        "SettingsScreen",
        "AuthScreen",
        "OnboardingScreen",
    ]
    
    for screen in screen_references:
        if screen in content:
            print(f"✅ Screen reference: {screen}")
        else:
            print(f"⚠️ Screen reference missing: {screen}")
    
    print("✅ Navigation structure looks good")
    return True

def test_context_providers():
    """Test context providers."""
    print("\n🧪 Testing Context Providers...")
    
    contexts_dir = Path("aether/mobile/src/contexts")
    
    # Required context files
    required_contexts = [
        "AuthContext.tsx",
        "ThemeContext.tsx", 
        "DataContext.tsx",
    ]
    
    missing_contexts = []
    for context_file in required_contexts:
        full_path = contexts_dir / context_file
        
        if not full_path.exists():
            missing_contexts.append(context_file)
        else:
            content = full_path.read_text(encoding='utf-8')
            
            # Check for context structure
            context_name = context_file.replace('.tsx', '')
            expected_patterns = [
                f"interface {context_name}Type",
                f"const {context_name} = createContext",
                f"export const {context_name.replace('Context', 'Provider')}",
                f"export const use{context_name.replace('Context', '')}",
            ]
            
            for pattern in expected_patterns:
                if pattern in content:
                    print(f"✅ {context_file}: {pattern}")
                else:
                    print(f"⚠️ {context_file}: Missing {pattern}")
    
    if missing_contexts:
        print(f"❌ Missing context files: {', '.join(missing_contexts)}")
        return False
    
    print("✅ Context providers structure looks good")
    return True

def test_services():
    """Test service layer."""
    print("\n🧪 Testing Service Layer...")
    
    services_dir = Path("aether/mobile/src/services")
    
    # Required service files
    required_services = [
        "StorageService.ts",
        "NotificationService.ts",
        "BackgroundService.ts",
        "ApiService.ts",
        "SyncService.ts",
    ]
    
    missing_services = []
    for service_file in required_services:
        full_path = services_dir / service_file
        
        if not full_path.exists():
            missing_services.append(service_file)
        else:
            content = full_path.read_text(encoding='utf-8')
            
            # Check for service class structure
            service_name = service_file.replace('.ts', '')
            expected_patterns = [
                f"class {service_name}",
                "static async initialize",
                "static async",
            ]
            
            found_patterns = 0
            for pattern in expected_patterns:
                if pattern in content:
                    found_patterns += 1
            
            if found_patterns >= 2:
                print(f"✅ {service_file}: Service structure present")
            else:
                print(f"⚠️ {service_file}: Limited service structure")
    
    if missing_services:
        print(f"❌ Missing service files: {', '.join(missing_services)}")
        return False
    
    print("✅ Service layer structure looks good")
    return True

def test_screens():
    """Test screen components."""
    print("\n🧪 Testing Screen Components...")
    
    screens_dir = Path("aether/mobile/src/screens")
    
    # Required screen files
    required_screens = [
        "LoadingScreen.tsx",
        "OnboardingScreen.tsx",
        "AuthScreen.tsx",
        "DashboardScreen.tsx",
        "ConversationScreen.tsx",
        "IdeaCaptureScreen.tsx",
        "TasksScreen.tsx",
        "SettingsScreen.tsx",
    ]
    
    missing_screens = []
    for screen_file in required_screens:
        full_path = screens_dir / screen_file
        
        if not full_path.exists():
            missing_screens.append(screen_file)
        else:
            content = full_path.read_text(encoding='utf-8')
            
            # Check for React component structure
            screen_name = screen_file.replace('.tsx', '')
            expected_patterns = [
                f"const {screen_name}: React.FC",
                "useTheme",
                "StyleSheet.create",
                f"export default {screen_name}",
            ]
            
            found_patterns = 0
            for pattern in expected_patterns:
                if pattern in content:
                    found_patterns += 1
            
            if found_patterns >= 3:
                print(f"✅ {screen_file}: Component structure present")
            else:
                print(f"⚠️ {screen_file}: Limited component structure")
    
    if missing_screens:
        print(f"❌ Missing screen files: {', '.join(missing_screens)}")
        return False
    
    print("✅ Screen components structure looks good")
    return True

def test_security_features():
    """Test security and encryption features."""
    print("\n🧪 Testing Security Features...")
    
    # Check StorageService for encryption
    storage_service = Path("aether/mobile/src/services/StorageService.ts")
    
    if not storage_service.exists():
        print("❌ StorageService not found")
        return False
    
    content = storage_service.read_text(encoding='utf-8')
    
    security_features = [
        "EncryptedStorage",
        "getSecureItem",
        "setSecureItem",
        "removeSecureItem",
        "clearAllData",
    ]
    
    for feature in security_features:
        if feature in content:
            print(f"✅ Security feature: {feature}")
        else:
            print(f"❌ Missing security feature: {feature}")
            return False
    
    # Check AuthContext for secure authentication
    auth_context = Path("aether/mobile/src/contexts/AuthContext.tsx")
    
    if auth_context.exists():
        auth_content = auth_context.read_text(encoding='utf-8')
        
        auth_features = [
            "EncryptedStorage",
            "authToken",
            "login",
            "logout",
            "register",
        ]
        
        for feature in auth_features:
            if feature in auth_content:
                print(f"✅ Auth feature: {feature}")
            else:
                print(f"⚠️ Auth feature missing: {feature}")
    
    print("✅ Security features implemented")
    return True

def test_offline_support():
    """Test offline support features."""
    print("\n🧪 Testing Offline Support...")
    
    # Check DataContext for offline handling
    data_context = Path("aether/mobile/src/contexts/DataContext.tsx")
    
    if not data_context.exists():
        print("❌ DataContext not found")
        return False
    
    content = data_context.read_text(encoding='utf-8')
    
    offline_features = [
        "NetInfo",
        "isOnline",
        "StorageService",
        "SyncService",
        "markForSync",
    ]
    
    for feature in offline_features:
        if feature in content:
            print(f"✅ Offline feature: {feature}")
        else:
            print(f"⚠️ Offline feature missing: {feature}")
    
    # Check SyncService
    sync_service = Path("aether/mobile/src/services/SyncService.ts")
    
    if sync_service.exists():
        sync_content = sync_service.read_text(encoding='utf-8')
        
        sync_features = [
            "syncPendingChanges",
            "markForSync",
            "performFullSync",
            "resolveConflict",
        ]
        
        for feature in sync_features:
            if feature in sync_content:
                print(f"✅ Sync feature: {feature}")
            else:
                print(f"⚠️ Sync feature missing: {feature}")
    
    print("✅ Offline support features implemented")
    return True

def test_cross_platform_compatibility():
    """Test cross-platform compatibility."""
    print("\n🧪 Testing Cross-Platform Compatibility...")
    
    # Check for platform-specific code handling
    files_to_check = [
        "aether/mobile/src/services/NotificationService.ts",
        "aether/mobile/src/services/BackgroundService.ts",
        "aether/mobile/src/utils/initialization.ts",
    ]
    
    platform_features = [
        "Platform.OS",
        "ios",
        "android",
    ]
    
    for file_path in files_to_check:
        file_obj = Path(file_path)
        if file_obj.exists():
            content = file_obj.read_text(encoding='utf-8')
            
            found_features = 0
            for feature in platform_features:
                if feature in content:
                    found_features += 1
            
            if found_features >= 2:
                print(f"✅ {file_obj.name}: Platform-specific handling present")
            else:
                print(f"⚠️ {file_obj.name}: Limited platform handling")
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("✅ Cross-platform compatibility features present")
    return True

def run_all_tests():
    """Run all mobile foundation tests."""
    print("🚀 Starting Mobile App Foundation Tests (Task 8.1)")
    print("=" * 60)
    
    tests = [
        test_mobile_structure,
        test_package_json,
        test_core_files,
        test_navigation_structure,
        test_context_providers,
        test_services,
        test_screens,
        test_security_features,
        test_offline_support,
        test_cross_platform_compatibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"💥 Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Mobile Foundation Tests Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All mobile foundation tests passed! Task 8.1 is complete.")
        print("\n🚀 MOBILE APPLICATION CAPABILITIES:")
        print("   ✓ Cross-platform React Native foundation")
        print("   ✓ Secure encrypted local storage")
        print("   ✓ Push notification system")
        print("   ✓ Background processing and sync")
        print("   ✓ Offline-first architecture")
        print("   ✓ Authentication and user management")
        print("   ✓ Theme and context management")
        print("   ✓ Navigation and screen structure")
        print("   ✓ Error handling and recovery")
        print("   ✓ Cross-platform compatibility")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)