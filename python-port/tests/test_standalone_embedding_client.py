"""
Test cases for the standalone GitHub Copilot Embeddings Client.

These tests verify all functionality of the embedding client without requiring a server.
"""

import pytest
import asyncio
from typing import List

from copilot_api.embedding_client import (
    CopilotEmbeddingClient, 
    embed_text, 
    embed_texts, 
    find_similar,
    EmbeddingResult
)


class TestBasicEmbedding:
    """Test basic embedding functionality."""
    
    @pytest.mark.asyncio
    async def test_single_text_embedding(self):
        """Test embedding a single text string."""
        text = "Python is a powerful programming language"
        result = await embed_text(text)
        
        assert isinstance(result, list)
        assert len(result) == 1536  # Standard embedding dimensions
        assert all(isinstance(x, float) for x in result)
    
    @pytest.mark.asyncio
    async def test_client_basic_embedding(self):
        """Test basic embedding with client class."""
        client = CopilotEmbeddingClient()
        text = "Hello, world! This is a test."
        
        result = await client.embed(text)
        
        assert isinstance(result, EmbeddingResult)
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 1536
        assert result.model == "text-embedding-3-small"
        assert "total_tokens" in result.usage
        assert result.texts == [text]


class TestBatchEmbedding:
    """Test batch embedding functionality."""
    
    @pytest.mark.asyncio
    async def test_multiple_texts_embedding(self):
        """Test embedding multiple texts."""
        texts = [
            "Machine learning is transforming technology",
            "Python programming for data science",
            "Natural language processing applications",
            "The weather is nice today"
        ]
        
        embeddings = await embed_texts(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == 1536 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_client_batch_embedding(self):
        """Test batch embedding with client class."""
        client = CopilotEmbeddingClient()
        texts = [
            "Python programming",
            "JavaScript development", 
            "Machine learning",
            "Web development"
        ]
        
        result = await client.embed(texts)
        
        assert len(result.embeddings) == len(texts)
        assert result.model == "text-embedding-3-small"
        assert result.usage["total_tokens"] > 0
        assert result.texts == texts
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self):
        """Test processing large batches with chunking."""
        client = CopilotEmbeddingClient()
        
        # Create 25 texts (will be processed in chunks)
        texts = [f"Sample text number {i} for testing." for i in range(25)]
        
        result = await client.embed_batch(texts, batch_size=10)
        
        assert len(result.embeddings) == 25
        assert result.usage["total_tokens"] > 0
        assert len(result.texts) == 25


class TestSemanticUnderstanding:
    """Test semantic understanding and similarity."""
    
    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        client = CopilotEmbeddingClient()
        
        texts = [
            "Python programming language",
            "JavaScript web development",
            "Dog training tips"
        ]
        
        result = await client.embed(texts)
        
        # Test similarity calculations
        sim_prog = client.cosine_similarity(result.embeddings[0], result.embeddings[1])
        sim_unrelated = client.cosine_similarity(result.embeddings[0], result.embeddings[2])
        
        # Programming languages should be more similar than programming vs dogs
        assert sim_prog > sim_unrelated
        assert -1 <= sim_prog <= 1
        assert -1 <= sim_unrelated <= 1
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search functionality."""
        client = CopilotEmbeddingClient()
        
        documents = [
            "Python is a high-level programming language",
            "JavaScript is primarily used for web development",
            "Machine learning algorithms predict patterns",
            "React is a JavaScript library for UIs",
            "Django is a Python web framework"
        ]
        
        query = "Python web frameworks"
        similar_docs = await client.find_most_similar(query, documents, top_k=3)
        
        assert len(similar_docs) == 3
        assert all(isinstance(item, tuple) and len(item) == 2 for item in similar_docs)
        
        # Check that results are sorted by similarity (descending)
        similarities = [score for _, score in similar_docs]
        assert similarities == sorted(similarities, reverse=True)
        
        # Django should be most relevant to "Python web frameworks"
        top_result = similar_docs[0]
        assert "Django" in top_result[0] or "Python" in top_result[0]
    
    @pytest.mark.asyncio
    async def test_find_similar_convenience_function(self):
        """Test find_similar convenience function."""
        knowledge_base = [
            "Python programming guide",
            "JavaScript tutorial", 
            "Machine learning course",
            "Data science with Python"
        ]
        
        query = "Python coding"
        similar = await find_similar(query, knowledge_base, top_k=2)
        
        assert len(similar) == 2
        assert all(score > 0 for _, score in similar)
        
        # Python-related documents should be top results
        top_text = similar[0][0]
        assert "Python" in top_text


class TestModelComparison:
    """Test different embedding models."""
    
    @pytest.mark.asyncio
    async def test_different_models(self):
        """Test different embedding models."""
        client = CopilotEmbeddingClient()
        text = "Artificial intelligence and machine learning"
        
        models = [
            "text-embedding-ada-002",
            "text-embedding-3-small", 
            "text-embedding-3-small-inference"
        ]
        
        results = {}
        for model in models:
            try:
                result = await client.embed(text, model=model)
                results[model] = result
                
                # Basic checks
                assert len(result.embeddings[0]) == 1536
                assert result.model == model
                assert result.usage["total_tokens"] > 0
                
            except Exception as e:
                pytest.fail(f"Model {model} failed: {e}")
        
        # Should have results for all models
        assert len(results) == len(models)
    
    @pytest.mark.asyncio
    async def test_model_consistency(self):
        """Test that same text gives consistent results across calls."""
        client = CopilotEmbeddingClient()
        text = "Test consistency of embeddings"
        
        # Get embeddings twice
        result1 = await client.embed(text)
        result2 = await client.embed(text)
        
        # Should be identical (or very close due to floating point)
        similarity = client.cosine_similarity(result1.embeddings[0], result2.embeddings[0])
        assert similarity > 0.99  # Should be nearly identical


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self):
        """Test handling of empty or problematic inputs."""
        client = CopilotEmbeddingClient()
        
        # Test with very short text
        result = await client.embed(["a"])
        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 1536
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special characters."""
        client = CopilotEmbeddingClient()
        
        text = "Hello! @#$%^&*()_+ 🚀🎉💻"
        result = await client.embed(text)
        
        assert len(result.embeddings[0]) == 1536
        assert result.usage["total_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_multilingual_text(self):
        """Test handling of multilingual text."""
        client = CopilotEmbeddingClient()
        
        texts = [
            "Hello world",
            "Hola mundo", 
            "Bonjour le monde",
            "こんにちは世界"
        ]
        
        result = await client.embed(texts)
        
        assert len(result.embeddings) == len(texts)
        assert all(len(emb) == 1536 for emb in result.embeddings)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_embed_text_function(self):
        """Test embed_text convenience function."""
        embedding = await embed_text("Test single embedding")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_texts_function(self):
        """Test embed_texts convenience function."""
        texts = ["First text", "Second text", "Third text"]
        embeddings = await embed_texts(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == 1536 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_find_similar_function(self):
        """Test find_similar convenience function."""
        docs = [
            "Python programming",
            "JavaScript coding",
            "Dog training",
            "Python development"
        ]
        
        similar = await find_similar("Python coding", docs, top_k=2)
        
        assert len(similar) == 2
        assert all(isinstance(item, tuple) for item in similar)
        assert all(len(item) == 2 for item in similar)
        
        # Results should be sorted by similarity
        assert similar[0][1] >= similar[1][1]


class TestEmbeddingResult:
    """Test EmbeddingResult data class."""
    
    @pytest.mark.asyncio
    async def test_embedding_result_interface(self):
        """Test EmbeddingResult methods and properties."""
        client = CopilotEmbeddingClient()
        texts = ["First", "Second", "Third"]
        
        result = await client.embed(texts)
        
        # Test length
        assert len(result) == 3
        
        # Test indexing
        first_embedding = result[0]
        assert len(first_embedding) == 1536
        
        # Test properties
        assert result.model == "text-embedding-3-small"
        assert len(result.texts) == 3
        assert "total_tokens" in result.usage


# Integration test
class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_document_search_scenario(self):
        """Test a realistic document search scenario."""
        client = CopilotEmbeddingClient()
        
        # Simulate a knowledge base
        knowledge_base = [
            "Python web development with Django and Flask frameworks",
            "JavaScript frontend development with React and Vue",
            "Machine learning with scikit-learn and TensorFlow",
            "Database optimization and SQL query performance",
            "Cloud computing with AWS and Azure services",
            "Mobile app development with React Native",
            "Data science and analytics with Pandas and NumPy",
            "API development and REST service design"
        ]
        
        # Multiple search queries
        queries = [
            "Python web frameworks",
            "frontend JavaScript development", 
            "machine learning libraries"
        ]
        
        for query in queries:
            results = await client.find_most_similar(query, knowledge_base, top_k=3)
            
            assert len(results) == 3
            assert all(score > 0 for _, score in results)
            
            # Verify relevance for each query
            if "Python" in query:
                assert any("Python" in text or "Django" in text for text, _ in results[:2])
            elif "JavaScript" in query:
                assert any("JavaScript" in text or "React" in text for text, _ in results[:2])
            elif "machine learning" in query:
                assert any("learning" in text or "TensorFlow" in text for text, _ in results[:2])
    
    @pytest.mark.asyncio
    async def test_clustering_scenario(self):
        """Test a text clustering scenario."""
        client = CopilotEmbeddingClient()
        
        # Mixed category texts
        texts = [
            "Python programming language",
            "Golden retriever dog breed",
            "JavaScript web development",
            "Labrador puppy training", 
            "React frontend framework",
            "Cat behavior and care"
        ]
        
        result = await client.embed(texts)
        
        # Calculate similarity matrix
        programming_indices = [0, 2, 4]  # Python, JS, React
        pet_indices = [1, 3, 5]  # Dogs and cats
        
        # Programming texts should be more similar to each other
        prog_similarities = []
        for i in programming_indices:
            for j in programming_indices:
                if i != j:
                    sim = client.cosine_similarity(result.embeddings[i], result.embeddings[j])
                    prog_similarities.append(sim)
        
        # Pet texts should be more similar to each other  
        pet_similarities = []
        for i in pet_indices:
            for j in pet_indices:
                if i != j:
                    sim = client.cosine_similarity(result.embeddings[i], result.embeddings[j])
                    pet_similarities.append(sim)
        
        # Cross-category similarities
        cross_similarities = []
        for i in programming_indices:
            for j in pet_indices:
                sim = client.cosine_similarity(result.embeddings[i], result.embeddings[j])
                cross_similarities.append(sim)
        
        # Within-category similarities should be higher than cross-category
        avg_prog_sim = sum(prog_similarities) / len(prog_similarities)
        avg_pet_sim = sum(pet_similarities) / len(pet_similarities)
        avg_cross_sim = sum(cross_similarities) / len(cross_similarities)
        
        assert avg_prog_sim > avg_cross_sim
        assert avg_pet_sim > avg_cross_sim


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])