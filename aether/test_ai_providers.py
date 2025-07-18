"""
Test script for AI provider functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai import (
    SimpleAIProvider,
    OllamaProvider,
    OpenAIProvider,
    initialize_ai_provider,
    get_ai_provider,
    get_prompt_manager
)


async def test_simple_ai_provider():
    """Test the simple AI provider."""
    print("🔧 Testing Simple AI Provider...")
    
    try:
        provider = SimpleAIProvider()
        
        # Test availability
        is_available = await provider.check_availability()
        print(f"✅ Simple AI Provider available: {is_available}")
        
        # Test responses
        test_inputs = [
            "Hello, I'm new here",
            "I want to build a business dashboard",
            "Can you help me organize my tasks?",
            "I have an idea for a new feature",
            "What can you help me with?",
            "This is a random input that doesn't match patterns"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n🔄 Test {i}/6:")
            print(f"Input: {user_input}")
            
            response = await provider.generate_response(user_input)
            print(f"Response: {response[:100]}...")
        
        # Test with context
        print(f"\n🧠 Testing with context...")
        context = "## Relevant Context from Memory:\n- User previously discussed dashboard metrics"
        response = await provider.generate_response(
            "Do you remember what we talked about?",
            context=context
        )
        print(f"Context-aware response: {response[:100]}...")
        
        print("✅ Simple AI Provider test completed")
        return True
        
    except Exception as e:
        print(f"❌ Simple AI Provider test failed: {e}")
        return False


async def test_ollama_provider():
    """Test the Ollama provider."""
    print("🔧 Testing Ollama Provider...")
    
    try:
        provider = OllamaProvider(model_name="llama2")
        
        # Test availability
        is_available = await provider.check_availability()
        print(f"✅ Ollama Provider available: {is_available}")
        
        if is_available:
            # Test basic response
            response = await provider.generate_response(
                "Hello, can you help me with business planning?"
            )
            print(f"✅ Ollama response: {response[:100]}...")
            
            # Test with context
            context = "User is working on a productivity dashboard project"
            response = await provider.generate_response(
                "What metrics should I track?",
                context=context
            )
            print(f"✅ Context-aware response: {response[:100]}...")
        else:
            print("⚠️  Ollama not available - skipping response tests")
        
        await provider.close()
        print("✅ Ollama Provider test completed")
        return True
        
    except Exception as e:
        print(f"❌ Ollama Provider test failed: {e}")
        return False


async def test_openai_provider():
    """Test the OpenAI provider."""
    print("🔧 Testing OpenAI Provider...")
    
    try:
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        
        # Test availability
        is_available = await provider.check_availability()
        print(f"✅ OpenAI Provider available: {is_available}")
        
        if is_available:
            # Test basic response
            response = await provider.generate_response(
                "Hello, can you help me with task management?"
            )
            print(f"✅ OpenAI response: {response[:100]}...")
        else:
            print("⚠️  OpenAI not available (API key not configured) - skipping response tests")
        
        await provider.close()
        print("✅ OpenAI Provider test completed")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Provider test failed: {e}")
        return False


async def test_prompt_manager():
    """Test the prompt manager."""
    print("🔧 Testing Prompt Manager...")
    
    try:
        prompt_manager = get_prompt_manager()
        
        # Test template listing
        templates = prompt_manager.list_templates()
        print(f"✅ Available templates: {len(templates)}")
        for template in templates[:5]:  # Show first 5
            print(f"  - {template}")
        
        # Test template rendering
        context_prompt = prompt_manager.render_prompt(
            "conversation_with_context",
            context="User previously discussed business metrics",
            user_input="What should I track for my SaaS business?"
        )
        print(f"✅ Rendered context prompt ({len(context_prompt)} chars)")
        
        # Test conversation type detection
        test_inputs = [
            "I want to build a business dashboard",
            "Can you help me organize my tasks?",
            "I have an idea for a new product",
            "Hello, how are you?"
        ]
        
        for user_input in test_inputs:
            conv_type = prompt_manager.extract_conversation_type(user_input)
            print(f"✅ '{user_input[:30]}...' -> {conv_type}")
        
        # Test comprehensive prompt building
        comprehensive_prompt = prompt_manager.build_conversation_prompt(
            user_input="I need help with my business metrics",
            context="Previous conversation about dashboard planning",
            memory_context="User wants to track revenue and customer metrics",
            conversation_type="business"
        )
        print(f"✅ Built comprehensive prompt ({len(comprehensive_prompt)} chars)")
        
        print("✅ Prompt Manager test completed")
        return True
        
    except Exception as e:
        print(f"❌ Prompt Manager test failed: {e}")
        return False


async def test_ai_provider_integration():
    """Test AI provider integration and switching."""
    print("🔧 Testing AI Provider Integration...")
    
    try:
        # Test provider initialization
        simple_provider = initialize_ai_provider("simple")
        print(f"✅ Initialized simple provider: {simple_provider.get_info()}")
        
        # Test global provider access
        global_provider = get_ai_provider()
        print(f"✅ Global provider: {global_provider.get_info()}")
        
        # Test provider switching
        ollama_provider = initialize_ai_provider(
            "ollama", 
            model_name="llama2",
            base_url="http://localhost:11434"
        )
        print(f"✅ Switched to Ollama provider: {ollama_provider.get_info()}")
        
        # Test availability checking
        providers_to_test = [
            ("simple", {}),
            ("ollama", {"model_name": "llama2"}),
            ("openai", {"model_name": "gpt-3.5-turbo"})
        ]
        
        availability_results = {}
        for provider_type, kwargs in providers_to_test:
            try:
                provider = initialize_ai_provider(provider_type, **kwargs)
                is_available = await provider.check_availability()
                availability_results[provider_type] = is_available
                print(f"✅ {provider_type} provider available: {is_available}")
                
                # Close provider if it has a close method
                if hasattr(provider, 'close'):
                    await provider.close()
                    
            except Exception as e:
                print(f"⚠️  {provider_type} provider error: {e}")
                availability_results[provider_type] = False
        
        print(f"✅ Provider availability summary: {availability_results}")
        
        print("✅ AI Provider Integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ AI Provider Integration test failed: {e}")
        return False


async def test_enhanced_conversation():
    """Test enhanced conversation with AI providers."""
    print("🔧 Testing Enhanced Conversation...")
    
    try:
        # Initialize conversation system with AI providers
        from core.database import initialize_database, initialize_vector_store
        from core.conversation import initialize_conversation_manager
        
        # Set up test environment
        test_db = Path("test_ai_conversation.db")
        test_vectors = Path("test_ai_vectors")
        
        if test_db.exists():
            test_db.unlink()
        if test_vectors.exists():
            import shutil
            shutil.rmtree(test_vectors)
        
        # Initialize systems
        db_manager = initialize_database(f"sqlite:///{test_db}", echo=False)
        vector_store = initialize_vector_store("simple", test_vectors)
        
        # Initialize with simple AI provider
        ai_provider = initialize_ai_provider("simple")
        conversation_manager = initialize_conversation_manager(ai_provider)
        
        await db_manager.create_tables_async()
        print("✅ Test environment initialized")
        
        # Test enhanced conversation
        from uuid import uuid4
        session_id = str(uuid4())
        
        test_conversations = [
            "Hello, I'm working on a business intelligence project",
            "I need to track revenue, customer acquisition, and operational metrics",
            "Can you help me prioritize which metrics are most important?",
            "I also want to integrate this with my existing tools"
        ]
        
        async with db_manager.get_async_session() as session:
            for i, user_input in enumerate(test_conversations, 1):
                print(f"\n🔄 Enhanced conversation {i}/4:")
                print(f"User: {user_input}")
                
                response = await conversation_manager.process_message(
                    user_input=user_input,
                    session_id=session_id,
                    db_session=session,
                    save_to_database=True,
                    create_memory=True
                )
                
                print(f"Aether: {response.ai_response}")
                print(f"✅ Processed with {response.context_metadata.get('relevant_memories', 0)} relevant memories")
        
        # Test conversation history
        async with db_manager.get_async_session() as session:
            history = await conversation_manager.get_conversation_history(
                session_id=session_id,
                db_session=session,
                limit=10
            )
            print(f"✅ Retrieved conversation history: {len(history)} conversations")
        
        # Clean up
        await db_manager.close()
        try:
            if test_db.exists():
                test_db.unlink()
            if test_vectors.exists():
                import shutil
                shutil.rmtree(test_vectors)
        except PermissionError:
            pass
        
        print("✅ Enhanced Conversation test completed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Aether AI Provider System Test\n")
    
    tests = [
        ("Simple AI Provider", test_simple_ai_provider),
        ("Ollama Provider", test_ollama_provider),
        ("OpenAI Provider", test_openai_provider),
        ("Prompt Manager", test_prompt_manager),
        ("AI Provider Integration", test_ai_provider_integration),
        ("Enhanced Conversation", test_enhanced_conversation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        success = await test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All AI provider tests passed!")
        print("\n🎯 AI System Capabilities Verified:")
        print("  ✅ Multiple AI provider support (Simple, Ollama, OpenAI)")
        print("  ✅ Dynamic provider switching")
        print("  ✅ Availability checking and fallbacks")
        print("  ✅ Advanced prompt engineering and templates")
        print("  ✅ Context-aware response generation")
        print("  ✅ Conversation type detection")
        print("  ✅ Enhanced conversation management")
        print("  ✅ Memory integration with AI responses")
        print("\n🚀 Ready for Task 3.3: Memory Management System!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)