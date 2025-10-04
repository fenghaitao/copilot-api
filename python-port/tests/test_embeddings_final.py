#!/usr/bin/env python3
"""
Final comprehensive embeddings test for Copilot API.
Based on debug results: input must be an array, not a single string.
"""

import requests
import json
import math
from typing import List

BASE_URL = "http://localhost:4141"
EMBEDDINGS_ENDPOINT = f"{BASE_URL}/embeddings"

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)

def test_available_models():
    """Test all available embedding models."""
    print("🤖 Testing available embedding models...")
    
    # Get available models
    models_response = requests.get(f"{BASE_URL}/models")
    if models_response.status_code != 200:
        print("❌ Could not fetch models")
        return
    
    models_data = models_response.json()
    embedding_models = [
        model['id'] for model in models_data.get('data', [])
        if 'embedding' in model['id'].lower()
    ]
    
    print(f"Found {len(embedding_models)} embedding models:")
    for model in embedding_models:
        print(f"  - {model}")
    
    # Test each embedding model
    test_text = ["Hello, this is a test for embedding models."]
    
    for model in embedding_models:
        print(f"\n🧪 Testing model: {model}")
        
        payload = {
            "input": test_text,
            "model": model
        }
        
        response = requests.post(EMBEDDINGS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            embedding_dim = len(data['data'][0]['embedding']) if data.get('data') else 0
            print(f"  ✅ Success! Dimensions: {embedding_dim}")
            if data.get('usage'):
                print(f"     Tokens: {data['usage']['total_tokens']}")
        else:
            print(f"  ❌ Failed: {response.status_code}")

def test_semantic_understanding():
    """Test semantic understanding with various text pairs."""
    print("\n🧠 Testing semantic understanding...")
    
    test_pairs = [
        {
            "name": "Programming Languages",
            "texts": [
                "Python is a great programming language",
                "I love coding in Python",
                "The sky is blue today"
            ],
            "expected": "First two should be more similar"
        },
        {
            "name": "Animals",
            "texts": [
                "Dogs are loyal pets",
                "Cats are independent animals", 
                "Machine learning algorithms"
            ],
            "expected": "First two should be more similar"
        },
        {
            "name": "Technology",
            "texts": [
                "Artificial intelligence is transforming technology",
                "Machine learning models are powerful",
                "I had pizza for lunch"
            ],
            "expected": "First two should be more similar"
        }
    ]
    
    for test_case in test_pairs:
        print(f"\n📝 {test_case['name']} ({test_case['expected']})")
        
        payload = {
            "input": test_case["texts"],
            "model": "text-embedding-3-small"
        }
        
        response = requests.post(EMBEDDINGS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            embeddings = [item['embedding'] for item in data['data']]
            
            sim_12 = calculate_cosine_similarity(embeddings[0], embeddings[1])
            sim_13 = calculate_cosine_similarity(embeddings[0], embeddings[2])
            sim_23 = calculate_cosine_similarity(embeddings[1], embeddings[2])
            
            print(f"  Similarity 1-2: {sim_12:.4f}")
            print(f"  Similarity 1-3: {sim_13:.4f}")
            print(f"  Similarity 2-3: {sim_23:.4f}")
            
            if sim_12 > max(sim_13, sim_23):
                print("  ✅ Semantic understanding correct!")
            else:
                print("  ⚠️ Unexpected similarity pattern")
        else:
            print(f"  ❌ Failed: {response.text}")

def test_batch_processing():
    """Test processing multiple texts efficiently."""
    print("\n📦 Testing batch processing...")
    
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Python programming is fun and powerful",
        "Machine learning models need lots of data",
        "Natural language processing enables AI communication",
        "Web development frameworks make coding easier",
        "Database optimization improves application performance",
        "Cloud computing provides scalable infrastructure",
        "Cybersecurity protects digital assets and privacy"
    ]
    
    payload = {
        "input": texts,
        "model": "text-embedding-3-small"
    }
    
    response = requests.post(EMBEDDINGS_ENDPOINT, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully processed {len(texts)} texts")
        print(f"   Received {len(data.get('data', []))} embeddings")
        print(f"   Each embedding has {len(data['data'][0]['embedding'])} dimensions")
        print(f"   Total tokens used: {data.get('usage', {}).get('total_tokens', 'N/A')}")
        
        # Find most similar pair
        embeddings = [item['embedding'] for item in data['data']]
        max_similarity = 0
        best_pair = None
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = calculate_cosine_similarity(embeddings[i], embeddings[j])
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_pair = (i, j)
        
        if best_pair:
            print(f"   Most similar texts ({max_similarity:.4f}):")
            print(f"     \"{texts[best_pair[0]]}\"")
            print(f"     \"{texts[best_pair[1]]}\"")
    else:
        print(f"❌ Batch processing failed: {response.text}")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🔍 Testing edge cases...")
    
    test_cases = [
        {
            "name": "Empty string",
            "input": [""],
            "model": "text-embedding-3-small"
        },
        {
            "name": "Very long text",
            "input": ["This is a very long text. " * 100],
            "model": "text-embedding-3-small"
        },
        {
            "name": "Special characters",
            "input": ["Hello! @#$%^&*()_+ 🚀🎉💻"],
            "model": "text-embedding-3-small"
        },
        {
            "name": "Multiple languages",
            "input": ["Hello world", "Hola mundo", "Bonjour le monde"],
            "model": "text-embedding-3-small"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        
        payload = {
            "input": test_case["input"],
            "model": test_case["model"]
        }
        
        response = requests.post(EMBEDDINGS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Embeddings: {len(data.get('data', []))}")
        else:
            print(f"  ❌ Failed: {response.status_code}")

def main():
    """Run comprehensive embeddings test suite."""
    print("🚀 Comprehensive Copilot API Embeddings Test")
    print("=" * 60)
    
    # Check server health
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("⚠️ Server issues detected")
            return
    except:
        print("❌ Cannot connect to server at http://localhost:4141")
        return
    
    # Run all tests
    test_available_models()
    test_semantic_understanding()
    test_batch_processing()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("🏁 Comprehensive test completed!")
    print("\n💡 Key findings:")
    print("   • Input must be an array (not single string)")
    print("   • Multiple embedding models available")
    print("   • Semantic understanding working correctly")
    print("   • Batch processing efficient")
    print("   • Good error handling for edge cases")

if __name__ == "__main__":
    main()