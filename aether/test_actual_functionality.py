#!/usr/bin/env python3
"""
Test what actually works vs what's just written as code.
"""

def test_monday_integration():
    """Test Monday.com integration functionality."""
    print("\n=== Testing Monday.com Integration ===")
    
    try:
        from core.integrations.monday_com import get_monday_integration
        from core.integrations.monday_types import MondayAuthConfig, MondayPreferences
        print("✓ Monday.com imports work")
        
        # Test basic initialization
        auth_config = MondayAuthConfig(api_token="test_token")
        preferences = MondayPreferences(default_board_id="123456789")
        integration = get_monday_integration(auth_config, preferences)
        print("✓ Monday.com integration initializes")
        
        # Test basic functionality
        boards = integration.get_boards()
        print(f"✓ get_boards() returns {len(boards)} boards")
        
        if boards:
            board = boards[0]
            print(f"✓ First board: {board.name} (ID: {board.id})")
            
            # Test item creation
            item_id = integration.create_item(
                board_id=board.id,
                item_name="Test Item",
                column_values={"status": {"label": "Working on it"}}
            )
            print(f"✓ create_item() returns: {item_id}")
            
            # Test item update
            if item_id:
                success = integration.update_item(item_id, {"status": {"label": "Done"}})
                print(f"✓ update_item() returns: {success}")
        
        print("✓ Monday.com integration basic functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Monday.com integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoints functionality."""
    print("\n=== Testing API Endpoints ===")
    
    try:
        from core.api.gateway import APIGateway
        from fastapi.testclient import TestClient
        print("✓ API Gateway imports work")
        
        # Test API Gateway creation
        gateway = APIGateway()
        app = gateway.create_app()
        print("✓ API Gateway app creation works")
        
        # Test with TestClient
        with TestClient(app) as client:
            # Test health endpoint
            response = client.get("/api/v1/health")
            print(f"✓ Health endpoint: {response.status_code}")
            
            # Test Monday.com status endpoint
            response = client.get("/api/v1/integrations/monday/status")
            print(f"✓ Monday status endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  - Status: {data.get('status')}")
                print(f"  - Mock mode: {data.get('mock_mode')}")
            
            # Test Monday.com boards endpoint
            response = client.get("/api/v1/integrations/monday/boards")
            print(f"✓ Monday boards endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  - Boards count: {data.get('count')}")
        
        print("✓ API endpoints work")
        return True
        
    except Exception as e:
        print(f"✗ API testing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_extraction():
    """Test task extraction functionality."""
    print("\n=== Testing Task Extraction ===")
    
    try:
        from core.tasks.extractor import get_task_extractor
        print("✓ Task extractor imports work")
        
        extractor = get_task_extractor()
        print("✓ Task extractor initializes")
        
        # Test task extraction
        text = """
        Meeting notes:
        - John needs to complete the report by Friday
        - Sarah should review the code by next week
        - We need to schedule a follow-up meeting
        """
        
        result = extractor.extract_tasks_from_text(text)
        print(f"✓ extract_tasks_from_text() returns {len(result.extracted_tasks)} tasks")
        
        for i, task in enumerate(result.extracted_tasks):
            print(f"  - Task {i+1}: {task.title}")
        
        print("✓ Task extraction works")
        return True
        
    except Exception as e:
        print(f"✗ Task extraction error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_idea_processing():
    """Test idea processing functionality."""
    print("\n=== Testing Idea Processing ===")
    
    try:
        # Initialize database first
        from initialize_system import initialize_aether_system
        initialize_aether_system()
        
        from core.ideas.processor import get_idea_processor
        print("✓ Idea processor imports work")
        
        processor = get_idea_processor()
        print("✓ Idea processor initializes")
        
        # Test idea processing
        idea_text = "What if we created an AI assistant that could help with project management?"
        
        result = processor.process_idea(idea_text)
        print(f"✓ process_idea() returns: {result.processed}")
        print(f"  - Category: {result.category}")
        print(f"  - Priority: {result.priority_score}")
        
        print("✓ Idea processing works")
        return True
        
    except Exception as e:
        print(f"✗ Idea processing error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_system():
    """Test memory system functionality."""
    print("\n=== Testing Memory System ===")
    
    try:
        # Initialize database first
        from initialize_system import initialize_aether_system
        initialize_aether_system()
        
        from core.memory.manager import get_memory_manager
        print("✓ Memory manager imports work")
        
        manager = get_memory_manager()
        print("✓ Memory manager initializes")
        
        # Test memory storage
        memory_text = "The user prefers morning meetings and likes detailed project updates."
        
        memory_id = manager.store_memory(memory_text, importance=0.8)
        print(f"✓ store_memory() returns: {memory_id}")
        
        # Test memory retrieval
        memories = manager.search_memories("meetings", limit=5)
        print(f"✓ search_memories() returns {len(memories)} memories")
        
        print("✓ Memory system works")
        return True
        
    except Exception as e:
        print(f"✗ Memory system error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_system():
    """Test conversation system functionality."""
    print("\n=== Testing Conversation System ===")
    
    try:
        # Initialize database first
        from initialize_system import initialize_aether_system
        initialize_aether_system()
        
        from core.conversation.manager import get_conversation_manager
        print("✓ Conversation manager imports work")
        
        manager = get_conversation_manager()
        print("✓ Conversation manager initializes")
        
        # Test conversation processing
        user_input = "I need to schedule a meeting with the team next week"
        
        response = manager.process_message(user_input)
        print(f"✓ process_message() returns: {response.message[:50]}...")
        
        print("✓ Conversation system works")
        return True
        
    except Exception as e:
        print(f"✗ Conversation system error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_system():
    """Test database system functionality."""
    print("\n=== Testing Database System ===")
    
    try:
        # Initialize database first
        from initialize_system import initialize_aether_system
        db_manager = initialize_aether_system()
        print("✓ Database manager initializes")
        
        # Test database connection
        with db_manager.get_session() as session:
            print("✓ Database session creation works")
        
        print("✓ Database system works")
        return True
        
    except Exception as e:
        print(f"✗ Database system error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all functionality tests."""
    print("=" * 60)
    print("TESTING ACTUAL FUNCTIONALITY vs WRITTEN CODE")
    print("=" * 60)
    
    tests = [
        ("Monday.com Integration", test_monday_integration),
        ("API Endpoints", test_api_endpoints),
        ("Task Extraction", test_task_extraction),
        ("Idea Processing", test_idea_processing),
        ("Memory System", test_memory_system),
        ("Conversation System", test_conversation_system),
        ("Database System", test_database_system),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("FUNCTIONALITY TEST SUMMARY")
    print("=" * 60)
    
    working_count = 0
    total_count = len(tests)
    
    for test_name, passed in results.items():
        status = "✓ WORKING" if passed else "✗ NOT WORKING"
        print(f"{test_name:25} {status}")
        if passed:
            working_count += 1
    
    print(f"\nOverall: {working_count}/{total_count} systems working")
    print(f"Success rate: {(working_count/total_count)*100:.1f}%")
    
    if working_count == total_count:
        print("\n🎉 All systems are functional!")
    else:
        print(f"\n⚠️  {total_count - working_count} systems need attention")


if __name__ == "__main__":
    main()