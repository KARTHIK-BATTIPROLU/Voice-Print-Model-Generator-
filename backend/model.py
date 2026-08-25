"""
Model loader module for ECAPA-TDNN singleton instance.
Validates: Requirements 4.1, 4.2, 4.3
"""
import threading
import time
import logging
from typing import Optional
from speechbrain.inference import EncoderClassifier
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton model loader for SpeechBrain ECAPA-TDNN.
    
    Thread-safe lazy loading ensures only one model instance exists.
    Uses double-checked locking pattern for efficient concurrent access.
    
    Validates: Requirements 4.1 (singleton pattern), 4.2 (model loading), 4.3 (thread-safety)
    """
    
    _instance: Optional[EncoderClassifier] = None
    _lock: threading.Lock = threading.Lock()
    _loaded: bool = False
    
    @staticmethod
    def get_instance() -> EncoderClassifier:
        """
        Returns singleton model instance, loads if not already loaded.
        
        Uses double-checked locking pattern:
        1. Fast path: check if model exists without lock
        2. If not, acquire lock and check again
        3. Load model if still not loaded
        
        Returns:
            EncoderClassifier: Singleton ECAPA-TDNN model instance
            
        Validates: Requirements 4.1, 4.2, 4.3
        """
        # Fast path: model already loaded (no lock needed)
        if ModelLoader._loaded:
            return ModelLoader._instance
        
        # Slow path: need to load model (acquire lock)
        with ModelLoader._lock:
            # Double-check: another thread might have loaded while we waited
            if ModelLoader._loaded:
                return ModelLoader._instance
            
            # Load model
            logger.info(f"Loading ECAPA-TDNN model from {config.model_path}")
            start_time = time.time()
            
            try:
                ModelLoader._instance = EncoderClassifier.from_hparams(
                    source=config.model_path,
                    savedir="pretrained_models/spkrec-ecapa-voxceleb",
                    run_opts={"device": "cpu"}
                )
            except Exception as first_err:
                logger.warning(f"Remote model load failed ({first_err}), attempting local path fallback...")
                local_dir = "pretrained_models/spkrec-ecapa-voxceleb"
                ModelLoader._instance = EncoderClassifier.from_hparams(
                    source=local_dir,
                    savedir=local_dir,
                    run_opts={"device": "cpu"}
                )
                
            ModelLoader._loaded = True
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
            return ModelLoader._instance

    
    @staticmethod
    def is_loaded() -> bool:
        """
        Check if model is loaded and ready.
        
        Returns:
            bool: True if model is loaded, False otherwise
            
        Validates: Requirement 4.1 (singleton status check)
        """
        return ModelLoader._loaded
