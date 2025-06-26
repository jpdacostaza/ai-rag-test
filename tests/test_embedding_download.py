#!/usr/bin/env python3
"""
Test script to verify the embedding model download logic.
"""
import os
import sys
import asyncio
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def test_embedding_download():
    """Test the embedding model download and initialization."""
    try:
        print("🔧 Testing embedding model download logic...")

        # Import configuration
        from config import EMBEDDING_MODEL, EMBEDDING_PROVIDER, SENTENCE_TRANSFORMERS_HOME, AUTO_PULL_MODELS

        print(f"📋 Configuration:")
        print(f"   EMBEDDING_MODEL: {EMBEDDING_MODEL}")
        print(f"   EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
        print(f"   SENTENCE_TRANSFORMERS_HOME: {SENTENCE_TRANSFORMERS_HOME}")
        print(f"   AUTO_PULL_MODELS: {AUTO_PULL_MODELS}")

        # Create models directory if it doesn't exist
        os.makedirs(SENTENCE_TRANSFORMERS_HOME, exist_ok=True)
        print(f"📁 Models directory: {os.path.abspath(SENTENCE_TRANSFORMERS_HOME)}")

        # Check if model exists locally
        model_dir = os.path.join(SENTENCE_TRANSFORMERS_HOME, EMBEDDING_MODEL.replace("/", "_"))
        model_exists = os.path.exists(model_dir) and os.listdir(model_dir)
        print(f"🔍 Model directory exists: {model_exists}")
        print(f"   Model path: {model_dir}")

        if model_exists:
            print(f"📦 Model files found:")
            for file in os.listdir(model_dir):
                print(f"   - {file}")

        if EMBEDDING_PROVIDER.lower() == "huggingface":
            print("🤗 Testing HuggingFace model download...")

            # Set environment variable for cache
            os.environ["SENTENCE_TRANSFORMERS_HOME"] = SENTENCE_TRANSFORMERS_HOME

            if not model_exists and AUTO_PULL_MODELS:
                print(f"📥 Model '{EMBEDDING_MODEL}' not found locally. Downloading...")

                def download_model():
                    """TODO: Add proper docstring for download_model."""
                    try:
                        from sentence_transformers import SentenceTransformer

                        print(f"🔄 Starting download of {EMBEDDING_MODEL}...")
                        model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=SENTENCE_TRANSFORMERS_HOME)
                        print(f"✅ Model downloaded successfully!")
                        print(f"📊 Model dimensions: {model.get_sentence_embedding_dimension()}")
                        return model
                    except Exception as e:
                        print(f"❌ Failed to download model: {e}")
                        return None

                # Download the model
                model = await asyncio.to_thread(download_model)

                if model is not None:
                    print("🧪 Testing embedding generation...")

                    # Test embedding generation
                    test_text = "This is a test sentence for embedding generation."
                    if "e5-" in EMBEDDING_MODEL.lower():
                        prefixed_text = f"query: {test_text}"
                    else:
                        prefixed_text = test_text

                    def generate_embedding():
                        """TODO: Add proper docstring for generate_embedding."""
                        try:
                            embedding = model.encode([prefixed_text], normalize_embeddings=True)
                            return embedding[0].tolist() if len(embedding) > 0 else None
                        except Exception as e:
                            print(f"❌ Failed to generate embedding: {e}")
                            return None

                    embedding = await asyncio.to_thread(generate_embedding)

                    if embedding:
                        print(f"✅ Successfully generated embedding!")
                        print(f"📏 Embedding length: {len(embedding)}")
                        print(f"🔢 First 5 values: {embedding[:5]}")
                    else:
                        print("❌ Failed to generate embedding")

            elif model_exists:
                print(f"📁 Loading existing model from cache...")

                def load_existing_model():
                    """TODO: Add proper docstring for load_existing_model."""
                    try:
                        from sentence_transformers import SentenceTransformer

                        model = SentenceTransformer(EMBEDDING_MODEL, cache_folder=SENTENCE_TRANSFORMERS_HOME)
                        print(f"✅ Model loaded successfully!")
                        print(f"📊 Model dimensions: {model.get_sentence_embedding_dimension()}")
                        return model
                    except Exception as e:
                        print(f"❌ Failed to load cached model: {e}")
                        return None

                model = await asyncio.to_thread(load_existing_model)

                if model is not None:
                    print("🧪 Testing embedding generation with cached model...")

                    # Test embedding generation
                    test_text = "This is a test sentence for embedding generation."
                    if "e5-" in EMBEDDING_MODEL.lower():
                        prefixed_text = f"query: {test_text}"
                    else:
                        prefixed_text = test_text

                    def generate_embedding():
                        """TODO: Add proper docstring for generate_embedding."""
                        try:
                            embedding = model.encode([prefixed_text], normalize_embeddings=True)
                            return embedding[0].tolist() if len(embedding) > 0 else None
                        except Exception as e:
                            print(f"❌ Failed to generate embedding: {e}")
                            return None

                    embedding = await asyncio.to_thread(generate_embedding)

                    if embedding:
                        print(f"✅ Successfully generated embedding!")
                        print(f"📏 Embedding length: {len(embedding)}")
                        print(f"🔢 First 5 values: {embedding[:5]}")
                    else:
                        print("❌ Failed to generate embedding")

            else:
                print("⚠️  Model not found and AUTO_PULL_MODELS is disabled")
                print("💡 Enable AUTO_PULL_MODELS=true to download automatically")

        else:
            print(f"🚫 Provider '{EMBEDDING_PROVIDER}' not supported in this test")
            print("💡 This test only supports HuggingFace provider")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure sentence-transformers is installed: pip install sentence-transformers")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Embedding Model Download Test")
    print("=" * 50)
    asyncio.run(test_embedding_download())
    print("=" * 50)
    print("🏁 Test completed!")
