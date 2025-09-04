#!/usr/bin/env python3
"""Health check script for the local LLM stack."""

import asyncio
import json
import sys
import time
from typing import Dict, Any
import httpx


class HealthChecker:
    """Health checker for all services."""
    
    def __init__(self):
        self.services = {
            "vllm": "http://localhost:8000",
            "embeddings": "http://localhost:8081", 
            "qdrant": "http://localhost:6333",
            "langfuse": "http://localhost:3000",
            "orchestrator": "http://localhost:8001"
        }
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def check_vllm(self) -> Dict[str, Any]:
        """Check vLLM service health."""
        try:
            response = await self.client.get(f"{self.services['vllm']}/v1/models")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "models": len(data.get("data", [])),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_embeddings(self) -> Dict[str, Any]:
        """Check embeddings service health."""
        try:
            response = await self.client.get(f"{self.services['embeddings']}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "details": data
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant service health."""
        try:
            response = await self.client.get(f"{self.services['qdrant']}/collections")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "collections": len(data.get("collections", [])),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_langfuse(self) -> Dict[str, Any]:
        """Check Langfuse service health."""
        try:
            response = await self.client.get(f"{self.services['langfuse']}/api/public/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "details": data
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_orchestrator(self) -> Dict[str, Any]:
        """Check orchestrator service health."""
        try:
            response = await self.client.get(f"{self.services['orchestrator']}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "components": data.get("components", {})
                }
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        print("🔍 Running health check...")
        
        checks = {
            "vllm": self.check_vllm(),
            "embeddings": self.check_embeddings(),
            "qdrant": self.check_qdrant(),
            "langfuse": self.check_langfuse(),
            "orchestrator": self.check_orchestrator()
        }
        
        results = {}
        for service, check_coro in checks.items():
            print(f"  Checking {service}...", end=" ")
            result = await check_coro
            results[service] = result
            
            if result["status"] == "healthy":
                print("✅")
            else:
                print(f"❌ ({result.get('error', 'Unknown error')})")
        
        # Overall status
        all_healthy = all(r["status"] == "healthy" for r in results.values())
        results["overall"] = {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": time.time()
        }
        
        return results
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main function."""
    checker = HealthChecker()
    
    try:
        results = await checker.run_health_check()
        
        print("\n📊 Health Check Summary:")
        print("=" * 50)
        
        for service, result in results.items():
            if service == "overall":
                continue
                
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            print(f"{status_icon} {service.upper()}: {result['status']}")
            
            if result["status"] == "healthy" and "response_time" in result:
                print(f"   Response time: {result['response_time']:.3f}s")
            elif result["status"] == "unhealthy":
                print(f"   Error: {result.get('error', 'Unknown')}")
        
        print(f"\n🎯 Overall Status: {results['overall']['status'].upper()}")
        
        # Exit with appropriate code
        if results["overall"]["status"] == "healthy":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Health check failed: {e}")
        sys.exit(1)
    finally:
        await checker.close()


if __name__ == "__main__":
    asyncio.run(main())

