#!/usr/bin/env python3
"""
Test script to verify conversation API functionality
"""

import requests
import json
import time

def test_conversation_api():
    base_url = 'http://127.0.0.1:3000'  # Backend API

    print("🧠 Testing Conversation API...")

    try:
        # Test 1: Create conversation session
        print("\n1. Creating conversation session...")
        create_response = requests.post(f'{base_url}/api/ai/conversation/create', json={
            'title': '测试对话会话',
            'documentId': None
        })

        if create_response.status_code == 200:
            session_data = create_response.json()
            session_id = session_data['sessionId']
            print(f"✅ Session created: {session_id}")

            # Test 2: Send a message
            print("\n2. Sending test message...")
            message_response = requests.post(f'{base_url}/api/ai/conversation/{session_id}/message', json={
                'content': '你好，这是一个测试消息，请介绍一下你自己。',
                'messageType': 'text'
            })

            if message_response.status_code == 200:
                msg_data = message_response.json()
                print("✅ Message sent successfully")
                print(f"   User: {msg_data['userMessage']['content'][:50]}...")
                print(f"   AI: {msg_data['aiResponse']['content'][:50]}...")

                # Test 3: Get conversation messages
                print("\n3. Retrieving conversation messages...")
                messages_response = requests.get(f'{base_url}/api/ai/conversation/{session_id}/messages')

                if messages_response.status_code == 200:
                    messages_data = messages_response.json()
                    print(f"✅ Retrieved {len(messages_data['messages'])} messages")

                    # Test 4: Get conversation sessions
                    print("\n4. Retrieving conversation sessions...")
                    sessions_response = requests.get(f'{base_url}/api/ai/conversation/sessions')

                    if sessions_response.status_code == 200:
                        sessions_data = sessions_response.json()
                        print(f"✅ Retrieved {len(sessions_data['sessions'])} sessions")
                        print("🎉 All conversation API tests passed!")
                        return True
                    else:
                        print(f"❌ Failed to get sessions: {sessions_response.status_code}")
                else:
                    print(f"❌ Failed to get messages: {messages_response.status_code}")
            else:
                print(f"❌ Failed to send message: {message_response.status_code}")
                print(f"Response: {message_response.text}")
        else:
            print(f"❌ Failed to create session: {create_response.status_code}")
            print(f"Response: {create_response.text}")

    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

    return False

if __name__ == "__main__":
    success = test_conversation_api()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
