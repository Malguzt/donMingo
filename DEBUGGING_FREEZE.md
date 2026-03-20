# Debugging Guide: Application Freeze After Model Selection

## Problem Analysis

Your application freezes after selecting the model but before generating text. The log shows:
```
[DEBUG] Selected model: Qwen/Qwen2.5-1.5B-Instruct (Complexity: small, Specialty: chat)
```
Then it stops without any further output.

## Root Causes Identified

### 1. **Threading Lock Contention** 
- Two Guanaco workers run in parallel threads
- Both try to acquire `ModelsHandler._lock` to access GPU
- One thread gets the lock but then freezes
- The other thread waits indefinitely (timeout added: 5 seconds)
- **Location**: `src/infrastructure/transformers_engine/models_handler.py:155`

### 2. **Model Loading/Download Hang**
- Model download from Hugging Face Hub can hang without timeout
- Model loading with `device_map="auto"` can freeze on memory allocation
- **Location**: `get_model_and_tokenizer()` method

### 3. **Generation Timeout**
- `model.generate()` has no timeout and can hang indefinitely
- No granular logging to identify exact failure point
- **Location**: `generate_text()` method

## Solutions Applied

### ✅ Immediate Fixes (Already Applied)

1. **Added granular logging** throughout the generation pipeline:
   - After model loading
   - Before/after tokenization
   - Before model.generate() call
   - After decoding

2. **Improved lock mechanism**:
   - Added 5-second timeout on lock acquisition
   - Better error messages when lock times out
   - Explicit lock release in finally block

3. **Better error handling**:
   - Stack traces for exceptions
   - Fallback mechanisms for model loading
   - Connection error handling for downloads

### 🔧 What to Do Next

#### Step 1: Run with Enhanced Logging
The updated code now provides much more detailed logs. Run your application again:

```bash
make run
```

Watch for these new debug messages to identify the exact bottleneck:
- `[DEBUG] Model loaded successfully` - model loading completed
- `[DEBUG] Tokenization complete` - tokenizer works
- `[DEBUG] Calling model.generate...` - about to start generation
- `[DEBUG] Generation completed` - generation finished

#### Step 2: Analyze the Freeze Point

Based on where the logs stop, apply the appropriate solution:

**If it freezes at "Calling model.generate...":**
- Problem: Model generation is too slow
- Solutions:
  - Use a smaller model (e.g., `TinyLlama/TinyLlama-1.1B`)
  - Reduce `max_new_tokens` (currently 64 for small models)
  - Enable 4-bit quantization via BitsAndBytes
  - Use `num_beams=1` (faster but lower quality)

**If it freezes at "Attempting to load model...":**
- Problem: Model file not cached, downloading from Hub is slow/frozen
- Solutions:
  - Pre-download models with: 
    ```python
    from huggingface_hub import snapshot_download
    snapshot_download("Qwen/Qwen2.5-1.5B-Instruct")
    ```
  - Use smaller models that download faster
  - Check your internet connection

**If it freezes trying to acquire GPU lock:**
- Problem: Other process using GPU
- Solutions:
  - Increase sleep time between worker iterations
  - Use sequential processing instead of parallel

#### Step 3: Long-term Architecture Improvements

**Recommended changes**:

1. **Implement queue-based processing** instead of parallel threads:
```python
# Instead of all guanacos.work() in parallel,
# use a job queue processed sequentially
```

2. **Add timeouts to model.generate()**:
```python
outputs = model.generate(
    **inputs,
    max_new_tokens=max_tokens,
    do_sample=True,
    temperature=0.7,
    pad_token_id=pad_token_id,
    # Add these:
    early_stopping=True,  # Stop as soon as valid sequence generated
    num_return_sequences=1,
)
```

3. **Pre-load models on startup**:
```python
def preload_models(self):
    """Load all models before workers start"""
    for model_def in self.catalog.get_all_models():
        self.get_model_and_tokenizer(model_def.huggingface_id, model_def.complexity)
```

4. **Separate GPU lock by complexity level**:
```python
# Instead of one lock, use multiple:
self._locks = {
    ModelComplexity.SMALL: threading.Lock(),
    ModelComplexity.MEDIUM: threading.Lock(),
    ModelComplexity.LARGE: threading.RLock(),  # Reentrant
}
```

## Testing the Fix

1. Run the application and capture logs:
```bash
make run > debug.log 2>&1 &
```

2. Send one message to one bot and monitor where it freezes

3. Share the log output if it still freezes - the granular logging will clearly show the bottleneck

## Quick Workarounds (Immediate Relief)

If you need the app running while debugging:

1. **Increase worker sleep time** in [src/main.py](src/main.py):
   - Change `sleep_time=10` to `sleep_time=30` (more spacing between polls)

2. **Reduce max_tokens** in [models_handler.py](src/infrastructure/transformers_engine/models_handler.py#L195):
   - Change `max_tokens = 256` to `max_tokens = 32`

3. **Use a simpler model** in [model_catalog.py](src/infrastructure/transformers_engine/model_catalog.py):
   - Change Qwen2.5-1.5B to TinyLlama-1.1B (much faster)

