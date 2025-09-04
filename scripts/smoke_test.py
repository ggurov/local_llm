#!/usr/bin/env python3
"""Smoke test script for the local LLM stack."""

import asyncio
import json
import sys
import time
from typing import Dict, Any
import httpx


class SmokeTester:
    """Smoke tester for the local LLM stack."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.tests = []
    
    async def test_vllm_basic(self) -> Dict[str, Any]:
        """Test basic vLLM functionality."""
        print("🧪 Testing vLLM basic functionality...")
        
        try:
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
                "messages": [{"role": "user", "content": "Hello, respond with just 'ping'"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = await self.client.post(
                "http://localhost:8000/v1/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                return {
                    "status": "passed",
                    "response": content,
                    "response_time": response.elapsed.total_seconds(),
                    "tokens": data.get("usage", {}).get("total_tokens", 0)
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def test_embeddings(self) -> Dict[str, Any]:
        """Test embeddings service."""
        print("🧪 Testing embeddings service...")
        
        try:
            payload = {
                "inputs": ["This is a test sentence for embeddings."]
            }
            
            response = await self.client.post(
                "http://localhost:8081/embed",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                return {
                    "status": "passed",
                    "embedding_size": len(embedding),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def test_qdrant(self) -> Dict[str, Any]:
        """Test Qdrant vector database."""
        print("🧪 Testing Qdrant...")
        
        try:
            # Test collections endpoint
            response = await self.client.get("http://localhost:6333/collections")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "passed",
                    "collections": len(data.get("collections", [])),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def test_orchestrator_chat(self) -> Dict[str, Any]:
        """Test orchestrator chat functionality."""
        print("🧪 Testing orchestrator chat...")
        
        try:
            payload = {
                "message": "Hello, can you help me test the system?"
            }
            
            response = await self.client.post(
                "http://localhost:8001/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "passed",
                    "response": data.get("response", "")[:100] + "..." if len(data.get("response", "")) > 100 else data.get("response", ""),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def test_tool_execution(self) -> Dict[str, Any]:
        """Test tool execution through orchestrator."""
        print("🧪 Testing tool execution...")
        
        try:
            payload = {
                "tool_name": "get_map",
                "arguments": {"key": "boost_target"}
            }
            
            response = await self.client.post(
                "http://localhost:8001/tools/execute",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "passed",
                    "result": data.get("result", {}),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def test_end_to_end(self) -> Dict[str, Any]:
        """Test end-to-end workflow with tool calling."""
        print("🧪 Testing end-to-end workflow...")
        
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": "Can you get the boost_target map data and summarize any anomalies?"}
                ],
                "model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
                "temperature": 0.7
            }
            
            response = await self.client.post(
                "http://localhost:8001/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return {
                    "status": "passed",
                    "response": content[:200] + "..." if len(content) > 200 else content,
                    "response_time": response.elapsed.total_seconds(),
                    "has_tool_calls": "tool_calls" in data["choices"][0]["message"]
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def run_smoke_tests(self) -> Dict[str, Any]:
        """Run all smoke tests."""
        print("🚀 Starting smoke tests...")
        print("=" * 50)
        
        tests = [
            ("vllm_basic", self.test_vllm_basic()),
            ("embeddings", self.test_embeddings()),
            ("qdrant", self.test_qdrant()),
            ("orchestrator_chat", self.test_orchestrator_chat()),
            ("tool_execution", self.test_tool_execution()),
            ("end_to_end", self.test_end_to_end())
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_coro in tests:
            print(f"\n📋 Running {test_name}...")
            result = await test_coro
            results[test_name] = result
            
            if result["status"] == "passed":
                passed += 1
                print(f"✅ {test_name}: PASSED")
                if "response_time" in result:
                    print(f"   Response time: {result['response_time']:.3f}s")
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Smoke Test Summary:")
        print(f"   Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! System is ready.")
            results["overall"] = {"status": "passed", "passed": passed, "total": total}
        else:
            print("⚠️  Some tests failed. Check the logs above.")
            results["overall"] = {"status": "failed", "passed": passed, "total": total}
        
        return results
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main function."""
    tester = SmokeTester()
    
    try:
        results = await tester.run_smoke_tests()
        
        # Exit with appropriate code
        if results["overall"]["status"] == "passed":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Smoke tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Smoke tests failed: {e}")
        sys.exit(1)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())

