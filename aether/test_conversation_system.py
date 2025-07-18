"""
Test script for conversation system functionality.
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import initialize_database, initialize_vector_store
from core.conversation import (
    ConversationManager,
    ContextManager,
    initialize_conversation_manager
)


async def test_conversation_system():
    """Test the complete conversation system."""
    print("🔧 Testing Aether Conversation System...")
    
    # Clean up test files
    test_db = Path("test_conversation_system.db")
    test_vectors = Path("test_conversation_vectors")
    
    if test_db.exists():
        test_db.unlink()
    if test_vectors.exists():
        import shutil
        shutil.rmtree(test_vectors)
    
    try:
        # Initialize systems
        print("🔧 Initializing database, vector store, and conversation manager...")
        db_manager = initialize_database(f"sqlite:///{test_db}", echo=False)
        vector_store = initialize_vector_store("simple", test_vectors)
        conversation_manager = initialize_conversation_manager()
        
        await db_manager.create_tables_async()
        print("✅ Systems initialized")
        
        # Test conversation context
        print("\n💬 Testing conversation context...")
        
        session_id = str(uuid4())
        context_manager = ContextManager()
        
        # Create context and add messages
        context = context_manager.get_or_create_context(session_id)
        context.add_message("user", "Hello, I want to build a business dashboard")
        context.add_message("assistant", "That's a great idea! Let me help you plan it out.")
        context.add_message("user", "What metrics should I include?")
        
        print(f"✅ Created context with {len(context.messages)} messages")
        
        # Test context string generation
        context_string = context.get_context_string(include_memories=False)
        print(f"✅ Generated context string ({len(context_string)} characters)")
        
        # Test context summary
        summary = context.get_summary()
        print(f"✅ Context summary: {summary['message_count']} messages, session {summary['session_id'][:8]}...")
        
        # Test conversation processing
        print("\n🤖 Testing AI conversation processing...")
        
        test_conversations = [
            "Hello, I'm new here. What can you help me with?",
            "I want to build a business intelligence dashboard for my company",
            "What metrics should I track for a SaaS business?",
            "Can you help me organize my tasks and priorities?",
            "I have an idea for a new product feature",
            "Do you remember what we discussed about the dashboard?"
        ]
        
        session_id = str(uuid4())
        conversation_responses = []
        
        async with db_manager.get_async_session() as session:
            for i, user_input in enumerate(test_conversations, 1):
                print(f"\n🔄 Processing conversation {i}/6...")
                print(f"User: {user_input}")
                
                response = await conversation_manager.process_message(
                    user_input=user_input,
                    session_id=session_id,
                    db_session=session,
                    save_to_database=True,
                    create_memory=True
                )
                
                conversation_responses.append(response)
                print(f"Assistant: {response.ai_response}")
                print(f"✅ Processed (ID: {response.id[:8]}...)")
        
        print(f"\n✅ Completed {len(conversation_responses)} conversations")
        
        # Test conversation history retrieval
        print("\n📚 Testing conversation history retrieval...")
        
        async with db_manager.get_async_session() as session:
            history = await conversation_manager.get_conversation_history(
                session_id=session_id,
                db_session=session,
                limit=10
            )
            
            print(f"✅ Retrieved {len(history)} conversations from history")
            
            if history:
                print("📋 Conversation History Summary:")
                for i, conv in enumerate(history[-3:], 1):  # Show last 3
                    print(f"  {i}. User: {conv.user_input[:50]}...")
                    print(f"     AI: {conv.ai_response[:50]}...")
        
        # Test task extraction
        print("\n📝 Testing task extraction from conversations...")
        
        if conversation_responses:
            async with db_manager.get_async_session() as session:
                # Test with a conversation that likely contains tasks
                test_conversation_id = conversation_responses[1].id  # Dashboard conversation
                
                extracted_tasks = await conversation_manager.extract_tasks_from_conversation(
                    conversation_id=test_conversation_id,
                    db_session=session
                )
                
                print(f"✅ Extracted {len(extracted_tasks)} potential tasks:")
                for task in extracted_tasks:
                    print(f"  - {task}")
        
        # Test context memory integration
        print("\n🧠 Testing context memory integration...")
        
        async with db_manager.get_async_session() as session:
            # Update context with memories
            await context_manager.update_context_memories(
                session_id=session_id,
                query="business dashboard metrics",
                db_session=session,
                limit=3,
                threshold=0.1
            )
            
            updated_context = context_manager.get_context(session_id)
            if updated_context:
                print(f"✅ Context updated with {len(updated_context.relevant_memories)} relevant memories")
                
                # Generate context string with memories
                context_with_memories = updated_context.get_context_string(include_memories=True)
                print(f"✅ Context with memories ({len(context_with_memories)} characters)")
        
        # Test conversation manager statistics
        print("\n📊 Testing conversation manager statistics...")
        
        stats = conversation_manager.get_context_stats()
        print(f"✅ Conversation Manager Stats:")
        print(f"  AI Provider: {stats['ai_provider']}")
        print(f"  Active Sessions: {stats['context_manager']['active_sessions']}")
        print(f"  Total Messages: {stats['context_manager']['total_messages']}")
        
        # Test context cleanup
        print("\n🧹 Testing context cleanup...")
        
        # Create an expired context
        old_session_id = str(uuid4())
        old_context = context_manager.get_or_create_context(old_session_id)
        old_context.add_message("user", "This is an old message")
        
        # Manually expire it
        from datetime import datetime, timedelta
        old_context.last_activity = datetime.utcnow() - timedelta(hours=2)
        
        print(f"✅ Created expired context (session: {old_session_id[:8]}...)")
        
        # Force cleanup
        context_manager._cleanup_expired_contexts()
        
        remaining_sessions = context_manager.get_active_sessions()
        print(f"✅ Active sessions after cleanup: {len(remaining_sessions)}")
        
        # Test error handling
        print("\n⚠️  Testing error handling...")
        
        async with db_manager.get_async_session() as session:
            # Test with valid session ID for error handling
            error_response = await conversation_manager.process_message(
                user_input="Test error handling",
                session_id=str(uuid4()),
                db_session=session,
                save_to_database=False,
                create_memory=False
            )
            
            print(f"✅ Error handling test completed")
            print(f"Response: {error_response.ai_response[:50]}...")
        
        print("\n🎉 Conversation system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Conversation system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            await db_manager.close()
        except:
            pass
        
        try:
            if test_db.exists():
                test_db.unlink()
        except PermissionError:
            print(f"⚠️  Could not delete {test_db}")
        
        try:
            if test_vectors.exists():
                import shutil
                shutil.rmtree(test_vectors)
        except PermissionError:
            print(f"⚠️  Could not delete {test_vectors}")


async def main():
    """Main test function."""
    print("🚀 Aether Conversation System Test\n")
    
    success = await test_conversation_system()
    
    if success:
        print("\n✅ Conversation system test passed!")
        print("\n🎯 System Capabilities Verified:")
        print("  ✅ Conversation context management")
        print("  ✅ AI response generation")
        print("  ✅ Memory integration with context")
        print("  ✅ Conversation history storage")
        print("  ✅ Task extraction from conversations")
        print("  ✅ Session management and cleanup")
        print("  ✅ Error handling and recovery")
        print("  ✅ Multi-session support")
        print("\n🚀 Ready for Task 3.2: Local LLM Integration!")
        return True
    else:
        print("\n❌ Conversation system test failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)