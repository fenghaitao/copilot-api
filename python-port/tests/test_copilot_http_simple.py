#!/usr/bin/env python3
"""
Simple GitHub Copilot Responses API Validator (no LiteLLM required)

This script directly tests the GitHub Copilot Responses API to validate
prompt caching support for Claude Sonnet and other models.

Requirements:
    pip install requests

Usage:
    python validate_copilot_simple.py
    
This script reads the GitHub token from ~/.config/copilot-api/github_token
and exchanges it for a Copilot token using the copilot-api framework.
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests is not installed. Install it with: pip install requests")
    sys.exit(1)

# Add the src directory to Python path to import copilot_api
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from copilot_api.services.github.get_copilot_token import get_copilot_token
    from copilot_api.services.get_vscode_version import get_vscode_version
    from copilot_api.lib.state import State
except ImportError as e:
    print(f"Error: Failed to import copilot_api modules: {e}")
    print("Make sure you're running this from the python-port directory")
    sys.exit(1)


async def get_copilot_api_key() -> tuple[str, str]:
    """Get Copilot API key from GitHub token using copilot-api framework"""
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY")
    
    if not github_token:
        config_path = os.path.expanduser("~/.config/copilot-api/github_token")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    github_token = f.read().strip()
            except Exception as e:
                print(f"Warning: Failed to read token from {config_path}: {e}")
    
    if not github_token:
        print("Error: GitHub token not found.")
        print("Please set GITHUB_TOKEN environment variable or")
        print("ensure token exists at: ~/.config/copilot-api/github_token")
        sys.exit(1)
    
    # Import state and set tokens
    from copilot_api.lib.state import state
    
    # Set GitHub token in state
    state.github_token = github_token
    state.vscode_version = await get_vscode_version()
    
    # Exchange GitHub token for Copilot token using the state-aware function
    try:
        result = await get_copilot_token()
        copilot_token = result["token"]
        return copilot_token, state.vscode_version
    except Exception as e:
        print(f"Error: Failed to get Copilot token: {e}")
        sys.exit(1)


def list_models(api_key: str, vscode_version: str) -> list:
    """List available GitHub Copilot models"""
    print("\n" + "="*80)
    print("FETCHING AVAILABLE MODELS")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "copilot-integration-id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    try:
        response = requests.get(
            "https://api.githubcopilot.com/models",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])

            print(f"\n✓ Found {len(models)} models\n")

            for model in models:
                model_id = model.get("id", "unknown")
                model_name = model.get("name", "unknown")
                family = model.get("capabilities", {}).get("family", "unknown")
                supported_endpoints = model.get("supported_endpoints", [])

                print(f"• {model_id}")
                print(f"  Name: {model_name}")
                print(f"  Family: {family}")

                if "/responses" in supported_endpoints:
                    print(f"  ✓ Supports Responses API (caching available)")
                elif "/chat/completions" in supported_endpoints:
                    print(f"  ⚠ Only Chat Completions API (no caching)")
                else:
                    print(f"  Endpoints: {', '.join(supported_endpoints)}")
                print()

            return models
        else:
            print(f"✗ Failed to fetch models: HTTP {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def test_responses_api(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Responses API with caching using prompt_cache_key"""
    print("\n" + "="*80)
    print(f"TESTING RESPONSES API WITH prompt_cache_key: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    # Create a long system message that should be cached
    long_system_message = (
        "You are a helpful AI assistant. " +
        "This is a long system prompt designed to test prompt caching. " * 50
    )

    # Use consistent session identifiers for caching (TypeScript approach)
    session_id = f"test_session_{int(time.time())}"
    user_id = "test_user_123"

    # First request - establish context
    payload1 = {
        "model": model,
        "instructions": long_system_message,  # System prompt goes here!
        "input": [
            {
                "type": "message",  # Must include type!
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Say 'Hello' in exactly one word."
                    }
                ]
            }
        ],
        "max_output_tokens": 20,
        "stream": False,
        "safety_identifier": user_id,
        "prompt_cache_key": session_id
    }

    print("\n→ Request 1: Initial request (building cache)")
    print(f"  System message length: {len(long_system_message)} chars")
    print(f"  Using safety_identifier: {user_id}")
    print(f"  Using prompt_cache_key: {session_id}")

    try:
        start1 = time.time()
        response1 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload1,
            timeout=30
        )
        elapsed1 = time.time() - start1

        if response1.status_code != 200:
            print(f"\n✗ Request failed: HTTP {response1.status_code}")
            print(f"Response: {response1.text[:500]}")
            return {"success": False, "error": response1.text[:500]}

        data1 = response1.json()
        response_id_1 = data1.get("id")  # Save for next request!
        usage1 = data1.get("usage", {})

        input_tokens1 = usage1.get("input_tokens", 0)
        output_tokens1 = usage1.get("output_tokens", 0)
        cached_tokens1 = usage1.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 1 successful")
        print(f"  Response ID: {response_id_1}")
        print(f"  Input tokens: {input_tokens1}")
        print(f"  Output tokens: {output_tokens1}")
        print(f"  Cached tokens: {cached_tokens1}")
        print(f"  Time: {elapsed1:.2f}s")

        # Extract response text
        output1 = data1.get("output", [])
        if output1:
            first_output = output1[0]
            if first_output.get("type") == "message":
                content = first_output.get("content", [])
                if content and content[0].get("type") == "output_text":
                    print(f"  Response: {content[0].get('text', '')}")

        # Second request using same session identifiers for caching
        # This is the TypeScript approach!
        payload2 = {
            "model": model,
            "instructions": long_system_message,  # Same system prompt (should be cached!)
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Now say 'World' in exactly one word."
                        }
                    ]
                }
            ],
            "max_output_tokens": 20,
            "stream": False,
            "safety_identifier": user_id,  # Same user
            "prompt_cache_key": session_id  # Same session (enables caching)
        }

        # Wait a moment for cache to settle
        print("\n→ Waiting 2 seconds for cache to settle...")
        time.sleep(2)

        print("\n→ Request 2: Using same session (cache expected)")
        print(f"  safety_identifier: {user_id}")
        print(f"  prompt_cache_key: {session_id}")

        start2 = time.time()
        response2 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload2,
            timeout=30
        )
        elapsed2 = time.time() - start2

        if response2.status_code != 200:
            print(f"\n✗ Request 2 failed: HTTP {response2.status_code}")
            print(f"Response: {response2.text[:500]}")
            return {
                "success": True,
                "request1": {"cached_tokens": cached_tokens1, "time": elapsed1},
                "request2": {"success": False, "error": response2.text[:500]}
            }

        data2 = response2.json()
        usage2 = data2.get("usage", {})

        input_tokens2 = usage2.get("input_tokens", 0)
        output_tokens2 = usage2.get("output_tokens", 0)
        cached_tokens2 = usage2.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 2 successful")
        print(f"  Response ID: {data2.get('id')}")
        print(f"  Input tokens: {input_tokens2}")
        print(f"  Output tokens: {output_tokens2}")
        print(f"  Cached tokens: {cached_tokens2}")
        print(f"  Time: {elapsed2:.2f}s")

        # Extract response text
        output2 = data2.get("output", [])
        if output2:
            first_output = output2[0]
            if first_output.get("type") == "message":
                content = first_output.get("content", [])
                if content and content[0].get("type") == "output_text":
                    print(f"  Response: {content[0].get('text', '')}")

        # Analyze caching
        print("\n" + "-"*80)
        print("CACHING ANALYSIS")
        print("-"*80)

        if cached_tokens2 > 0:
            print(f"✓✓ PROMPT CACHING IS WORKING!")
            print(f"   {cached_tokens2} tokens were served from cache")
            print(f"   Time saved: {elapsed1 - elapsed2:.2f}s ({((elapsed1 - elapsed2) / elapsed1 * 100):.1f}%)")
            cache_status = "WORKING"
        else:
            print(f"⚠ No cached tokens detected")
            print(f"  This could mean:")
            print(f"  - Model doesn't support caching with prompt_cache_key")
            print(f"  - Cache hasn't been populated yet (needs more time)")
            print(f"  - Caching only works with reasoning models or specific account types")
            cache_status = "NOT_DETECTED"

        return {
            "success": True,
            "model": model,
            "cache_status": cache_status,
            "request1": {
                "input_tokens": input_tokens1,
                "output_tokens": output_tokens1,
                "cached_tokens": cached_tokens1,
                "time": elapsed1
            },
            "request2": {
                "input_tokens": input_tokens2,
                "output_tokens": output_tokens2,
                "cached_tokens": cached_tokens2,
                "time": elapsed2
            }
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"success": False, "error": str(e)}


def test_responses_api_with_reasoning(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Responses API with reasoning blocks and caching using prompt_cache_key"""
    print("\n" + "="*80)
    print(f"TESTING RESPONSES API WITH REASONING AND prompt_cache_key: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    long_system_message = (
        "You are a helpful AI assistant with deep reasoning capabilities. " +
        "Think carefully about each question. " * 30
    )

    # Use consistent session identifiers for caching (TypeScript approach)
    session_id = f"test_session_reasoning_{int(time.time())}"
    user_id = "test_user_123"

    # Request 1: Initial request with reasoning enabled
    payload1 = {
        "model": model,
        "instructions": long_system_message,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "What is 2+2? Think step by step."
                    }
                ]
            }
        ],
        "reasoning": {
            "effort": "high",
            "summary": "detailed"
        },
        "include": ["reasoning.encrypted_content"],
        "max_output_tokens": 500,
        "stream": False,
        "safety_identifier": user_id,
        "prompt_cache_key": session_id
    }

    print("\n→ Request 1: Initial request with reasoning enabled")
    print(f"  Reasoning: enabled (effort=high)")
    print(f"  Using safety_identifier: {user_id}")
    print(f"  Using prompt_cache_key: {session_id}")

    try:
        start1 = time.time()
        response1 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload1,
            timeout=60
        )
        elapsed1 = time.time() - start1

        if response1.status_code != 200:
            print(f"\n✗ Request failed: HTTP {response1.status_code}")
            print(f"Response: {response1.text[:500]}")
            return {"success": False, "error": response1.text[:500]}

        data1 = response1.json()
        response_id_1 = data1.get('id')  # Save for next request!
        usage1 = data1.get("usage", {})

        input_tokens1 = usage1.get("input_tokens", 0)
        output_tokens1 = usage1.get("output_tokens", 0)
        cached_tokens1 = usage1.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 1 successful")
        print(f"  Response ID: {response_id_1}")
        print(f"  Input tokens: {input_tokens1}")
        print(f"  Output tokens: {output_tokens1}")
        print(f"  Cached tokens: {cached_tokens1}")
        print(f"  Time: {elapsed1:.2f}s")

        # Extract reasoning and message from output
        output1 = data1.get("output", [])
        reasoning_block = None
        assistant_message = None
        assistant_content = []

        for item in output1:
            if item.get("type") == "reasoning":
                reasoning_block = item
                print(f"\n  ✓ Reasoning block found:")
                print(f"    ID: {item.get('id', 'NO ID!')}")
                print(f"    Encrypted content: {item.get('encrypted_content', '')[:50]}...")
                if item.get("summary"):
                    summary_text = item["summary"][0].get("text", "")[:100]
                    print(f"    Summary: {summary_text}...")
            elif item.get("type") == "message":
                assistant_message = item
                content = item.get("content", [])
                if content:
                    assistant_content = content
                    if content[0].get("type") == "output_text":
                        print(f"  Response: {content[0].get('text', '')[:100]}...")

        if not reasoning_block:
            print("\n  ⚠ No reasoning block in response - caching won't work!")
            return {
                "success": True,
                "has_reasoning": False,
                "message": "Model doesn't generate reasoning blocks"
            }

        reasoning_id = reasoning_block.get("id")
        if not reasoning_id:
            print("\n  ⚠ Reasoning block has no ID - caching won't work!")
            return {
                "success": True,
                "has_reasoning": True,
                "has_reasoning_id": False,
                "message": "Reasoning block missing ID"
            }

        # Request 2: Include previous reasoning WITH ID
        print("\n→ Waiting 2 seconds for cache to settle...")
        time.sleep(2)

        # Build input with previous reasoning and message
        input_with_history = [
            {
                "id": reasoning_id,  # ← CRITICAL FOR CACHING!
                "type": "reasoning",
                "encrypted_content": reasoning_block.get("encrypted_content"),
                "summary": reasoning_block.get("summary", [])
            }
        ]
        
        # Add assistant message if we have content
        if assistant_content:
            input_with_history.append({
                "type": "message",
                "role": "assistant",
                "content": assistant_content
            })
        
        # Add new user message
        input_with_history.append({
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Now what is 3+3? Use similar reasoning."
                }
            ]
        })

        payload2 = {
            "model": model,
            "instructions": long_system_message,  # Same (should be cached)
            "input": input_with_history,
            "reasoning": {
                "effort": "high",
                "summary": "detailed"
            },
            "include": ["reasoning.encrypted_content"],
            "max_output_tokens": 500,
            "stream": False,
            "safety_identifier": user_id,  # Same user
            "prompt_cache_key": session_id  # Same session (enables caching)
        }

        print("\n→ Request 2: With previous reasoning ID (cache expected)")
        print(f"  safety_identifier: {user_id}")
        print(f"  prompt_cache_key: {session_id}")
        print(f"  Previous reasoning ID: {reasoning_id}")
        print(f"\n  DEBUG: Input history structure:")
        print(f"    - Reasoning block: type={input_with_history[0].get('type')}, has_id={bool(input_with_history[0].get('id'))}")
        print(f"    - Total items in input: {len(input_with_history)}")

        start2 = time.time()
        response2 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload2,
            timeout=60
        )
        elapsed2 = time.time() - start2

        if response2.status_code != 200:
            print(f"\n✗ Request 2 failed: HTTP {response2.status_code}")
            print(f"Response: {response2.text[:500]}")
            return {
                "success": True,
                "has_reasoning": True,
                "has_reasoning_id": True,
                "request1": {"cached_tokens": cached_tokens1, "time": elapsed1},
                "request2": {"success": False, "error": response2.text[:500]}
            }

        data2 = response2.json()
        usage2 = data2.get("usage", {})

        input_tokens2 = usage2.get("input_tokens", 0)
        output_tokens2 = usage2.get("output_tokens", 0)
        cached_tokens2 = usage2.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 2 successful")
        print(f"  Response ID: {data2.get('id')}")
        print(f"  Input tokens: {input_tokens2}")
        print(f"  Output tokens: {output_tokens2}")
        print(f"  Cached tokens: {cached_tokens2}")
        print(f"  Time: {elapsed2:.2f}s")

        # Analyze caching
        print("\n" + "-"*80)
        print("REASONING-BASED CACHING ANALYSIS")
        print("-"*80)

        if cached_tokens2 > 0:
            print(f"✓✓✓ REASONING CACHE IS WORKING!")
            print(f"   {cached_tokens2} tokens were served from cache")
            print(f"   This includes the previous reasoning block and system prompt!")
            print(f"   Time saved: {elapsed1 - elapsed2:.2f}s")
            cache_status = "WORKING"
        else:
            print(f"⚠ No cached tokens detected")
            print(f"  Possible reasons:")
            print(f"  - Model doesn't support caching with prompt_cache_key")
            print(f"  - Cache needs more time to populate")
            print(f"  - Caching only works with specific models or account types")
            print(f"  - Reasoning ID mechanism may not trigger caching alone")
            cache_status = "NOT_DETECTED"

        return {
            "success": True,
            "has_reasoning": True,
            "has_reasoning_id": True,
            "reasoning_id": reasoning_id,
            "cache_status": cache_status,
            "request1": {
                "input_tokens": input_tokens1,
                "output_tokens": output_tokens1,
                "cached_tokens": cached_tokens1,
                "time": elapsed1
            },
            "request2": {
                "input_tokens": input_tokens2,
                "output_tokens": output_tokens2,
                "cached_tokens": cached_tokens2,
                "time": elapsed2
            }
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_responses_api_large_prompt(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Responses API with large system prompt (like OpenAI test)"""
    print("\n" + "="*80)
    print(f"TESTING RESPONSES API WITH LARGE SYSTEM PROMPT: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    # Create a large system prompt (>2000 tokens) - same as OpenAI test
    LARGE_SYSTEM_PROMPT = """
You are an expert software engineer and technical advisor with deep knowledge across multiple domains.

# Your Expertise Areas:

## 1. Programming Languages
You are proficient in: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Swift, Kotlin, Ruby, PHP, Scala, R, MATLAB, Julia, Haskell, Erlang, Elixir, Clojure, F#, OCaml, Dart, Lua, Perl, Shell scripting (Bash, Zsh, PowerShell).

## 2. Web Development
- Frontend: React, Vue, Angular, Svelte, Next.js, Nuxt.js, Gatsby, Remix
- Backend: Node.js, Express, Fastify, NestJS, Django, Flask, FastAPI, Spring Boot, ASP.NET Core, Laravel, Ruby on Rails
- CSS Frameworks: Tailwind CSS, Bootstrap, Material-UI, Chakra UI, Ant Design
- State Management: Redux, Zustand, MobX, Recoil, Jotai, Pinia, Vuex
- GraphQL: Apollo, Relay, urql, GraphQL Yoga
- REST APIs: OpenAPI/Swagger, API design best practices

## 3. Cloud & Infrastructure
- AWS: EC2, S3, Lambda, ECS, EKS, RDS, DynamoDB, CloudFront, API Gateway, CloudFormation, CDK
- Azure: VMs, Blob Storage, Functions, AKS, Cosmos DB, Front Door, ARM templates
- GCP: Compute Engine, Cloud Storage, Cloud Functions, GKE, Cloud SQL, Cloud CDN, Deployment Manager
- Kubernetes: Deployments, Services, Ingress, ConfigMaps, Secrets, Helm, ArgoCD, Istio
- Docker: Containerization, multi-stage builds, Docker Compose, Docker Swarm
- Terraform: Infrastructure as Code, modules, state management, workspaces

## 4. Databases
- Relational: PostgreSQL, MySQL, SQL Server, Oracle, SQLite
- NoSQL: MongoDB, Redis, Cassandra, CouchDB, Neo4j
- Time-series: InfluxDB, TimescaleDB
- Vector: Pinecone, Weaviate, Qdrant, Milvus
- Search: Elasticsearch, Solr, Typesense, Meilisearch
- Query optimization, indexing strategies, sharding, replication

## 5. DevOps & CI/CD
- CI/CD: GitHub Actions, GitLab CI, Jenkins, CircleCI, Travis CI, Azure DevOps
- Monitoring: Prometheus, Grafana, DataDog, New Relic, Sentry, ELK Stack
- Version Control: Git workflows, branching strategies, monorepos
- Configuration Management: Ansible, Chef, Puppet, SaltStack
- Secret Management: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault

## 6. Machine Learning & AI
- Frameworks: TensorFlow, PyTorch, JAX, scikit-learn, XGBoost, LightGBM
- NLP: Transformers, Hugging Face, spaCy, NLTK, Gensim
- Computer Vision: OpenCV, YOLO, ResNet, Vision Transformers
- MLOps: MLflow, Kubeflow, SageMaker, Vertex AI
- Vector databases and embeddings
- RAG (Retrieval Augmented Generation) systems
- LLM fine-tuning and prompt engineering

## 7. Data Engineering
- ETL/ELT: Apache Airflow, Prefect, Dagster, Luigi
- Stream Processing: Apache Kafka, Apache Flink, Apache Spark Streaming, Pulsar
- Data Warehousing: Snowflake, BigQuery, Redshift, Databricks
- Data Lakes: Delta Lake, Apache Iceberg, Apache Hudi
- Workflow orchestration and data pipelines

## 8. Security
- OWASP Top 10 vulnerabilities
- Authentication: OAuth 2.0, OpenID Connect, SAML, JWT
- Encryption: TLS/SSL, AES, RSA, key management
- Security best practices: CORS, CSP, XSS prevention, SQL injection prevention
- Penetration testing and vulnerability scanning
- Compliance: GDPR, HIPAA, SOC 2, PCI DSS

## 9. Architecture & Design Patterns
- Microservices vs Monolithic architectures
- Event-driven architecture
- CQRS and Event Sourcing
- Domain-Driven Design (DDD)
- Clean Architecture, Hexagonal Architecture
- Design Patterns: Singleton, Factory, Observer, Strategy, Decorator, etc.
- API design: REST, GraphQL, gRPC, WebSockets
- Scalability patterns: Load balancing, caching, CDN, database sharding

## 10. Mobile Development
- iOS: Swift, SwiftUI, UIKit, Combine
- Android: Kotlin, Jetpack Compose, Coroutines, Flow
- Cross-platform: React Native, Flutter, Ionic, Xamarin
- Mobile-specific considerations: offline-first, push notifications, deep linking

# Your Response Guidelines:

1. **Be Precise and Technical**: Provide accurate, detailed technical information
2. **Show Code Examples**: When appropriate, include well-commented code snippets
3. **Explain Trade-offs**: Discuss pros/cons of different approaches
4. **Consider Context**: Ask clarifying questions when needed
5. **Best Practices**: Always recommend industry best practices and modern approaches
6. **Performance**: Consider performance implications in your recommendations
7. **Security**: Highlight security considerations when relevant
8. **Scalability**: Think about how solutions scale
9. **Maintainability**: Favor readable, maintainable solutions
10. **Testing**: Suggest appropriate testing strategies

# Code Style Preferences:

- Use clear, descriptive variable and function names
- Follow language-specific conventions (PEP 8 for Python, etc.)
- Include type hints/annotations where applicable
- Write self-documenting code with minimal but effective comments
- Prefer composition over inheritance
- Follow SOLID principles
- Use modern language features and idioms
- Avoid premature optimization

# Problem-Solving Approach:

1. Understand the problem thoroughly
2. Break down complex problems into smaller parts
3. Consider multiple solutions
4. Evaluate trade-offs
5. Recommend the best approach with justification
6. Provide implementation guidance
7. Suggest testing and validation approaches
8. Consider edge cases and error handling

# Communication Style:

- Start with a clear, concise answer
- Provide detailed explanations when needed
- Use analogies for complex concepts when helpful
- Structure responses with clear sections
- Use code blocks with proper syntax highlighting
- Include links to documentation when relevant
- Be honest about limitations or uncertainties

You are now ready to assist with any technical questions or problems. Please provide thoughtful, accurate, and helpful responses based on this extensive knowledge base and these guidelines.
"""

    print(f"\nSystem prompt size: ~{len(LARGE_SYSTEM_PROMPT)} characters")

    # Use consistent session identifiers for caching (TypeScript approach)
    session_id = f"test_session_{int(time.time())}"
    user_id = "test_user_123"
    
    # Request 1: First request with large system prompt
    print("\n📤 Request 1: Initial request with large system prompt")
    payload1 = {
        "model": model,
        "instructions": LARGE_SYSTEM_PROMPT,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "What is the capital of France?"
                    }
                ]
            }
        ],
        "max_output_tokens": 50,
        "stream": False,
        "safety_identifier": user_id,  # TypeScript approach
        "prompt_cache_key": session_id  # TypeScript approach
    }

    try:
        start1 = time.time()
        response1 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload1,
            timeout=30
        )
        elapsed1 = time.time() - start1

        if response1.status_code != 200:
            print(f"\n✗ Request 1 failed: HTTP {response1.status_code}")
            print(f"Response: {response1.text[:500]}")
            return {"success": False, "error": response1.text[:500]}

        data1 = response1.json()
        response_id_1 = data1.get("id")
        usage1 = data1.get("usage", {})

        input_tokens1 = usage1.get("input_tokens", 0)
        output_tokens1 = usage1.get("output_tokens", 0)
        cached_tokens1 = usage1.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"✅ Response ID: {response_id_1}")
        print(f"\n📊 Usage Stats:")
        print(f"  Input tokens: {input_tokens1}")
        print(f"  Output tokens: {output_tokens1}")
        print(f"  Cached tokens: {cached_tokens1}")
        print(f"  Total tokens: {usage1.get('total_tokens', 0)}")
        print(f"  Time: {elapsed1:.2f}s")

        # Request 2: Second request with same system prompt and session identifiers
        print(f"\n📤 Request 2: Follow-up with same session (should use cache)")
        print(f"  Using safety_identifier: {user_id}")
        print(f"  Using prompt_cache_key: {session_id}")
        
        time.sleep(2)  # Wait for cache to settle
        
        payload2 = {
            "model": model,
            "instructions": LARGE_SYSTEM_PROMPT,  # Same large system prompt (should be cached!)
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "What is 2 + 2?"
                        }
                    ]
                }
            ],
            "max_output_tokens": 50,
            "stream": False,
            "safety_identifier": user_id,  # Same user
            "prompt_cache_key": session_id  # Same session (enables caching)
        }

        start2 = time.time()
        response2 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload2,
            timeout=30
        )
        elapsed2 = time.time() - start2

        if response2.status_code != 200:
            print(f"\n✗ Request 2 failed: HTTP {response2.status_code}")
            print(f"Response: {response2.text[:500]}")
            return {
                "success": True,
                "request1": {"cached_tokens": cached_tokens1, "time": elapsed1},
                "request2": {"success": False, "error": response2.text[:500]}
            }

        data2 = response2.json()
        usage2 = data2.get("usage", {})

        input_tokens2 = usage2.get("input_tokens", 0)
        output_tokens2 = usage2.get("output_tokens", 0)
        cached_tokens2 = usage2.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"✅ Response ID: {data2.get('id')}")
        print(f"\n📊 Usage Stats:")
        print(f"  Input tokens: {input_tokens2}")
        print(f"  Output tokens: {output_tokens2}")
        print(f"  Cached tokens: {cached_tokens2} 🎯")
        print(f"  Total tokens: {usage2.get('total_tokens', 0)}")
        print(f"  Time: {elapsed2:.2f}s")

        # Request 3: Third request to further test caching
        print(f"\n📤 Request 3: Another follow-up (should also use cache)")
        
        payload3 = {
            "model": model,
            "instructions": LARGE_SYSTEM_PROMPT,  # Same large system prompt
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Explain Python list comprehensions in one sentence."
                        }
                    ]
                }
            ],
            "max_output_tokens": 100,
            "stream": False,
            "safety_identifier": user_id,  # Same user
            "prompt_cache_key": session_id  # Same session (enables caching)
        }

        start3 = time.time()
        response3 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload3,
            timeout=30
        )
        elapsed3 = time.time() - start3

        if response3.status_code != 200:
            print(f"\n✗ Request 3 failed: HTTP {response3.status_code}")
            print(f"Response: {response3.text[:500]}")
        else:
            data3 = response3.json()
            usage3 = data3.get("usage", {})

            input_tokens3 = usage3.get("input_tokens", 0)
            output_tokens3 = usage3.get("output_tokens", 0)
            cached_tokens3 = usage3.get("input_tokens_details", {}).get("cached_tokens", 0)

            print(f"✅ Response ID: {data3.get('id')}")
            print(f"\n📊 Usage Stats:")
            print(f"  Input tokens: {input_tokens3}")
            print(f"  Output tokens: {output_tokens3}")
            print(f"  Cached tokens: {cached_tokens3} 🎯")
            print(f"  Total tokens: {usage3.get('total_tokens', 0)}")
            print(f"  Time: {elapsed3:.2f}s")

        # Summary
        print("\n" + "="*80)
        print("📈 CACHING ANALYSIS (Large Prompt Test)")
        print("="*80)

        cached_total = cached_tokens2 + (cached_tokens3 if response3.status_code == 200 else 0)
        
        if cached_total > 0:
            print(f"✅ SUCCESS! Caching is working!")
            print(f"   Request 2 cached: {cached_tokens2} tokens")
            if response3.status_code == 200:
                print(f"   Request 3 cached: {cached_tokens3} tokens")
            print(f"   Total tokens cached: {cached_total}")
            
            total_input = input_tokens1 + input_tokens2 + (input_tokens3 if response3.status_code == 200 else 0)
            savings_pct = (cached_total / total_input * 100) if total_input > 0 else 0
            print(f"   Savings: {savings_pct:.1f}% of input tokens")
            cache_status = "WORKING"
        else:
            print(f"⚠️  No caching detected (cached_tokens = 0 for all requests)")
            print(f"\nPossible reasons:")
            print(f"  1. Model doesn't support prompt caching")
            print(f"  2. System prompt not large enough to trigger caching")
            print(f"  3. Caching requires specific model versions or account settings")
            print(f"  4. Caching happens internally but metrics not exposed")
            cache_status = "NOT_DETECTED"

        return {
            "success": True,
            "model": model,
            "cache_status": cache_status,
            "request1": {
                "input_tokens": input_tokens1,
                "output_tokens": output_tokens1,
                "cached_tokens": cached_tokens1,
                "time": elapsed1
            },
            "request2": {
                "input_tokens": input_tokens2,
                "output_tokens": output_tokens2,
                "cached_tokens": cached_tokens2,
                "time": elapsed2
            }
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_chat_completions_api(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Chat Completions API (for comparison)"""
    print("\n" + "="*80)
    print(f"TESTING CHAT COMPLETIONS API: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Chat Completions' in exactly 4 words."}
        ],
        "max_tokens": 20,
        "temperature": 0.7
    }

    try:
        start = time.time()
        response = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start

        if response.status_code != 200:
            print(f"\n✗ Request failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {"success": False, "error": response.text[:500]}

        data = response.json()
        usage = data.get("usage", {})

        print(f"\n✓ Request successful")
        print(f"  Model: {data.get('model')}")
        print(f"  Prompt tokens: {usage.get('prompt_tokens', 0)}")
        print(f"  Completion tokens: {usage.get('completion_tokens', 0)}")
        print(f"  Total tokens: {usage.get('total_tokens', 0)}")
        print(f"  Time: {elapsed:.2f}s")

        choices = data.get("choices", [])
        if choices:
            print(f"  Response: {choices[0].get('message', {}).get('content', '')}")

        return {"success": True, "usage": usage, "time": elapsed}

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"success": False, "error": str(e)}


async def async_main():
    """Main async function"""
    print("\n" + "="*80)
    print("GITHUB COPILOT RESPONSES API VALIDATOR")
    print("Simple version - Direct API calls only")
    print("="*80)

    # Get Copilot API key from GitHub token
    copilot_token, vscode_version = await get_copilot_api_key()
    print(f"\n✓ Successfully obtained Copilot token")
    print(f"  VS Code version: {vscode_version}")

    # List available models
    models = list_models(copilot_token, vscode_version)

    # Test models that support Responses API
    # Try gpt-5.1 which is a reasoning model and more likely to support caching
    test_models = ["gpt-5-mini"]

    print("\n" + "="*80)
    print("TESTING MODELS")
    print("="*80)

    results = {}

    for model in test_models:
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print('='*80)

        # Test Chat Completions API
        chat_result = test_chat_completions_api(copilot_token, vscode_version, model)

        # Test Responses API with large prompt (like OpenAI test)
        large_prompt_result = test_responses_api_large_prompt(copilot_token, vscode_version, model)

        # Test Responses API (simple)
        responses_result = test_responses_api(copilot_token, vscode_version, model)

        # Test Responses API with reasoning (the real caching test!)
        reasoning_result = test_responses_api_with_reasoning(copilot_token, vscode_version, model)

        results[model] = {
            "chat_completions": chat_result,
            "large_prompt_caching": large_prompt_result,
            "responses_api": responses_result,
            "responses_with_reasoning": reasoning_result
        }

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    for model, result in results.items():
        print(f"{model}:")

        # Chat Completions
        if result["chat_completions"].get("success"):
            print(f"  ✓ Chat Completions API: Working")
        else:
            print(f"  ✗ Chat Completions API: Failed")

        # Large Prompt Caching Test (like OpenAI)
        if result["large_prompt_caching"].get("success"):
            print(f"  ✓ Responses API (large prompt): Working")

            cache_status = result["large_prompt_caching"].get("cache_status")
            if cache_status == "WORKING":
                cached = result["large_prompt_caching"]["request2"]["cached_tokens"]
                print(f"    ✓✓ LARGE PROMPT CACHING: WORKING ({cached} tokens)!")
            else:
                print(f"    ⚠ Large Prompt Caching: Not detected")
        else:
            print(f"  ✗ Responses API (large prompt): Failed")

        # Responses API (simple)
        if result["responses_api"].get("success"):
            print(f"  ✓ Responses API (simple): Working")

            cache_status = result["responses_api"].get("cache_status")
            if cache_status == "WORKING":
                cached = result["responses_api"]["request2"]["cached_tokens"]
                print(f"    ✓✓ Simple Caching: WORKING ({cached} tokens)")
            else:
                print(f"    ⚠ Simple Caching: Not detected (expected)")
        else:
            print(f"  ✗ Responses API (simple): Failed")

        # Responses API with reasoning
        reasoning = result.get("responses_with_reasoning", {})
        if reasoning.get("success"):
            if reasoning.get("has_reasoning"):
                if reasoning.get("has_reasoning_id"):
                    print(f"  ✓ Responses API (reasoning): Working")
                    print(f"    Reasoning ID: {reasoning.get('reasoning_id', 'N/A')[:30]}...")
                    
                    cache_status = reasoning.get("cache_status")
                    if cache_status == "WORKING":
                        cached = reasoning["request2"]["cached_tokens"]
                        print(f"    ✓✓✓ REASONING CACHE: WORKING ({cached} tokens)!")
                    else:
                        print(f"    ⚠ Reasoning Cache: Not detected")
                else:
                    print(f"  ⚠ Reasoning blocks have no IDs (cache won't work)")
            else:
                print(f"  ⚠ Model doesn't generate reasoning blocks")
        else:
            error = reasoning.get("error", "Unknown error")
            print(f"  ✗ Responses API (reasoning): Failed - {error[:50]}")

        print()

    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")


def main():
    """Main function wrapper"""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
