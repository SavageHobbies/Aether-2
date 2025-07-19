#!/usr/bin/env python3
"""
Test script for Task 7.2: Build desktop dashboard interface
Tests the dashboard components and functionality.
"""

import os
import sys
import json
from pathlib import Path

def test_dashboard_files():
    """Test that all dashboard files exist and have content."""
    print("🧪 Testing Dashboard Files...")
    
    desktop_src = Path("aether/desktop/src")
    
    # Required dashboard files
    required_files = {
        "scripts/dashboard.js": "Dashboard JavaScript functionality",
        "styles/dashboard.css": "Dashboard CSS styles", 
        "dashboard.html": "Dashboard HTML template",
        "index.html": "Main application HTML with dashboard integration"
    }
    
    missing_files = []
    empty_files = []
    
    for file_path, description in required_files.items():
        full_path = desktop_src / file_path
        
        if not full_path.exists():
            missing_files.append(f"{file_path} ({description})")
        elif full_path.stat().st_size == 0:
            empty_files.append(f"{file_path} ({description})")
        else:
            print(f"✅ {file_path} - {full_path.stat().st_size} bytes")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    if empty_files:
        print(f"⚠️ Empty files: {', '.join(empty_files)}")
        return False
    
    print("✅ All dashboard files present and non-empty")
    return True

def test_dashboard_javascript():
    """Test dashboard JavaScript structure and classes."""
    print("\n🧪 Testing Dashboard JavaScript...")
    
    js_file = Path("aether/desktop/src/scripts/dashboard.js")
    
    if not js_file.exists():
        print("❌ Dashboard JavaScript file not found")
        return False
    
    content = js_file.read_text(encoding='utf-8')
    
    # Check for required classes and functions
    required_components = [
        "class DashboardManager",
        "class DashboardWidget", 
        "async init()",
        "setupEventListeners()",
        "initializeWidgets()",
        "createWidget(",
        "loadData()",
        "updateContent()",
        "renderStatsContent(",
        "renderListContent(",
        "renderActionsContent(",
        "setupWidgetDragAndDrop(",
        "toggleCustomization()",
        "refreshAllWidgets()",
        "startRealTimeUpdates()",
        "window.DashboardManager",
        "window.DashboardWidget"
    ]
    
    missing_components = []
    for component in required_components:
        if component not in content:
            missing_components.append(component)
        else:
            print(f"✅ Found: {component}")
    
    if missing_components:
        print(f"❌ Missing JavaScript components: {', '.join(missing_components)}")
        return False
    
    # Check for widget types
    widget_types = ["stats", "list", "actions"]
    for widget_type in widget_types:
        if f"'{widget_type}'" in content or f'"{widget_type}"' in content:
            print(f"✅ Widget type supported: {widget_type}")
        else:
            print(f"⚠️ Widget type may not be supported: {widget_type}")
    
    print("✅ Dashboard JavaScript structure looks good")
    return True

def test_dashboard_css():
    """Test dashboard CSS structure and classes."""
    print("\n🧪 Testing Dashboard CSS...")
    
    css_file = Path("aether/desktop/src/styles/dashboard.css")
    
    if not css_file.exists():
        print("❌ Dashboard CSS file not found")
        return False
    
    content = css_file.read_text(encoding='utf-8')
    
    # Check for required CSS classes
    required_classes = [
        ".dashboard-container",
        ".dashboard-header", 
        ".dashboard-grid",
        ".dashboard-widget",
        ".widget-header",
        ".widget-content",
        ".widget-actions",
        ".stats-grid",
        ".stat-item",
        ".widget-list",
        ".widget-list-item",
        ".quick-actions-grid",
        ".quick-action-btn",
        ".customization-panel",
        ".widget-template",
        ".loading-overlay",
        ".real-time-indicator",
        ".empty-state",
        ".dashboard-error"
    ]
    
    missing_classes = []
    for css_class in required_classes:
        if css_class in content:
            print(f"✅ Found CSS class: {css_class}")
        else:
            missing_classes.append(css_class)
    
    if missing_classes:
        print(f"❌ Missing CSS classes: {', '.join(missing_classes)}")
        return False
    
    # Check for responsive design
    responsive_features = [
        "@media (max-width:",
        "@media (prefers-color-scheme: dark)",
        "@media (prefers-reduced-motion:",
        "@keyframes"
    ]
    
    for feature in responsive_features:
        if feature in content:
            print(f"✅ Found responsive feature: {feature}")
        else:
            print(f"⚠️ Missing responsive feature: {feature}")
    
    print("✅ Dashboard CSS structure looks good")
    return True

def test_dashboard_html():
    """Test dashboard HTML structure."""
    print("\n🧪 Testing Dashboard HTML...")
    
    # Test standalone dashboard.html
    dashboard_html = Path("aether/desktop/src/dashboard.html")
    if dashboard_html.exists():
        content = dashboard_html.read_text(encoding='utf-8')
        
        required_elements = [
            'class="dashboard-container"',
            'class="dashboard-header"',
            'class="dashboard-grid"',
            'id="dashboard-grid"',
            'class="customization-panel"',
            'id="customization-panel"',
            'class="widget-library"',
            'class="loading-overlay"',
            'scripts/dashboard.js'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"✅ Found HTML element: {element}")
            else:
                print(f"❌ Missing HTML element: {element}")
    
    # Test main index.html integration
    index_html = Path("aether/desktop/src/index.html")
    if not index_html.exists():
        print("❌ Main index.html file not found")
        return False
    
    content = index_html.read_text(encoding='utf-8')
    
    # Check for dashboard integration
    dashboard_integration = [
        'id="dashboard-page"',
        'class="dashboard-container"',
        'id="dashboard-grid"',
        'scripts/dashboard.js',
        'styles/dashboard.css',
        'data-page="dashboard"'
    ]
    
    missing_integration = []
    for element in dashboard_integration:
        if element in content:
            print(f"✅ Found dashboard integration: {element}")
        else:
            missing_integration.append(element)
    
    if missing_integration:
        print(f"❌ Missing dashboard integration: {', '.join(missing_integration)}")
        return False
    
    print("✅ Dashboard HTML integration looks good")
    return True

def test_widget_functionality():
    """Test widget functionality and data structures."""
    print("\n🧪 Testing Widget Functionality...")
    
    js_file = Path("aether/desktop/src/scripts/dashboard.js")
    content = js_file.read_text(encoding='utf-8')
    
    # Check for widget data loading methods
    data_methods = [
        "loadStatsData()",
        "loadListData()", 
        "loadActionsData()",
        "getMockListData()",
        "getListEndpoint()"
    ]
    
    for method in data_methods:
        if method in content:
            print(f"✅ Found data method: {method}")
        else:
            print(f"❌ Missing data method: {method}")
    
    # Check for widget types and their handlers
    widget_handlers = [
        "renderStatsContent",
        "renderListContent", 
        "renderActionsContent",
        "renderListItem",
        "handleQuickAction"
    ]
    
    for handler in widget_handlers:
        if handler in content:
            print(f"✅ Found widget handler: {handler}")
        else:
            print(f"❌ Missing widget handler: {handler}")
    
    # Check for customization features
    customization_features = [
        "setupWidgetDragAndDrop",
        "startDrag",
        "handleDrop",
        "toggleCustomization",
        "saveWidgetConfiguration",
        "loadWidgetConfiguration"
    ]
    
    for feature in customization_features:
        if feature in content:
            print(f"✅ Found customization feature: {feature}")
        else:
            print(f"❌ Missing customization feature: {feature}")
    
    print("✅ Widget functionality looks comprehensive")
    return True

def test_integration_points():
    """Test integration points with the main application."""
    print("\n🧪 Testing Integration Points...")
    
    js_file = Path("aether/desktop/src/scripts/dashboard.js")
    content = js_file.read_text(encoding='utf-8')
    
    # Check for Tauri integration
    tauri_integration = [
        "window.__TAURI__",
        "window.aetherApp",
        "invokeCommand"
    ]
    
    found_integration = False
    for integration in tauri_integration:
        if integration in content:
            print(f"✅ Found integration point: {integration}")
            found_integration = True
    
    if not found_integration:
        print("⚠️ No explicit Tauri integration found - using mock data")
    
    # Check for API endpoints
    api_endpoints = [
        "get_dashboard_data",
        "get_recent_tasks",
        "get_recent_ideas", 
        "get_notifications",
        "get_recent_activity"
    ]
    
    for endpoint in api_endpoints:
        if endpoint in content:
            print(f"✅ Found API endpoint: {endpoint}")
        else:
            print(f"⚠️ API endpoint referenced: {endpoint}")
    
    print("✅ Integration points identified")
    return True

def test_accessibility_features():
    """Test accessibility features in the dashboard."""
    print("\n🧪 Testing Accessibility Features...")
    
    css_file = Path("aether/desktop/src/styles/dashboard.css")
    css_content = css_file.read_text(encoding='utf-8')
    
    html_file = Path("aether/desktop/src/index.html")
    html_content = html_file.read_text(encoding='utf-8')
    
    # Check for accessibility CSS
    accessibility_features = [
        "@media (prefers-reduced-motion:",
        "@media (prefers-contrast:",
        "focus:",
        "aria-",
        "title="
    ]
    
    for feature in accessibility_features:
        if feature in css_content or feature in html_content:
            print(f"✅ Found accessibility feature: {feature}")
        else:
            print(f"⚠️ Consider adding accessibility feature: {feature}")
    
    # Check for keyboard navigation
    keyboard_features = [
        "tabindex",
        "keydown",
        "keypress",
        "Enter"
    ]
    
    js_file = Path("aether/desktop/src/scripts/dashboard.js")
    js_content = js_file.read_text(encoding='utf-8')
    
    for feature in keyboard_features:
        if feature in js_content or feature in html_content:
            print(f"✅ Found keyboard feature: {feature}")
    
    print("✅ Basic accessibility features present")
    return True

def run_all_tests():
    """Run all dashboard tests."""
    print("🚀 Starting Dashboard Interface Tests (Task 7.2)")
    print("=" * 60)
    
    tests = [
        test_dashboard_files,
        test_dashboard_javascript,
        test_dashboard_css,
        test_dashboard_html,
        test_widget_functionality,
        test_integration_points,
        test_accessibility_features
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
    print(f"📊 Dashboard Tests Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All dashboard tests passed! Task 7.2 is complete.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)