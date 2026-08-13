"""
Unit tests for ModelLoader singleton pattern.
Validates: Requirements 4.1, 4.2, 4.3
"""
import threading
import time
from model import ModelLoader


def test_singleton_pattern():
    """Test that get_instance returns the same object on multiple calls"""
    print("Testing singleton pattern...")
    instance1 = ModelLoader.get_instance()
    instance2 = ModelLoader.get_instance()
    
    assert instance1 is instance2, "Singleton pattern failed: different instances returned"
    print("✓ Singleton pattern verified: same instance returned")


def test_is_loaded():
    """Test that is_loaded returns correct status"""
    print("\nTesting is_loaded status...")
    
    # After get_instance is called, should be loaded
    assert ModelLoader.is_loaded(), "is_loaded should return True after model is loaded"
    print("✓ is_loaded returns True after loading")


def test_thread_safety():
    """Test thread-safe concurrent access to get_instance"""
    print("\nTesting thread safety...")
    
    instances = []
    errors = []
    
    def get_model_instance():
        try:
            instance = ModelLoader.get_instance()
            instances.append(instance)
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads that simultaneously call get_instance
    threads = []
    num_threads = 10
    
    for _ in range(num_threads):
        thread = threading.Thread(target=get_model_instance)
        threads.append(thread)
    
    # Start all threads at roughly the same time
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred during concurrent access: {errors}"
    
    # Verify all threads got the same instance
    assert len(instances) == num_threads, f"Expected {num_threads} instances, got {len(instances)}"
    first_instance = instances[0]
    for instance in instances:
        assert instance is first_instance, "Thread safety failed: different instances in different threads"
    
    print(f"✓ Thread safety verified: {num_threads} concurrent threads got same instance")


def test_model_properties():
    """Test that loaded model has expected properties"""
    print("\nTesting model properties...")
    
    model = ModelLoader.get_instance()
    
    # Verify model is an EncoderClassifier instance
    from speechbrain.inference import EncoderClassifier
    assert isinstance(model, EncoderClassifier), "Model should be EncoderClassifier instance"
    print("✓ Model is correct type (EncoderClassifier)")
    
    # Verify model has encode_batch method (required for embedding extraction)
    assert hasattr(model, 'encode_batch'), "Model should have encode_batch method"
    print("✓ Model has encode_batch method")


if __name__ == "__main__":
    print("=" * 60)
    print("ModelLoader Unit Tests")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        test_singleton_pattern()
        test_is_loaded()
        test_thread_safety()
        test_model_properties()
        
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"✅ All tests passed! ({elapsed:.2f} seconds)")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
