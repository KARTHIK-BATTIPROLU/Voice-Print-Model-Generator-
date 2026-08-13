"""
Verify audio_utils.py syntax and structure using AST parsing.
This doesn't require PyTorch to be runnable.
"""
import ast


def parse_and_verify():
    """Parse audio_utils.py and verify all required functions exist."""
    print("\n" + "="*60)
    print("Audio Preprocessing Code Verification (AST Parser)")
    print("="*60 + "\n")
    
    try:
        with open("audio_utils.py", "r") as f:
            source_code = f.read()
        
        # Parse the source code
        tree = ast.parse(source_code)
        
        # Find all function definitions
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = {
                    'args': [arg.arg for arg in node.args.args],
                    'has_docstring': ast.get_docstring(node) is not None,
                    'line': node.lineno
                }
        
        # Required functions and their parameters
        required_functions = {
            'validate_wav': ['file_path'],
            'resample_audio': ['waveform', 'orig_sr', 'target_sr'],
            'convert_to_mono': ['waveform'],
            'estimate_snr': ['waveform', 'sample_rate'],
            'segment_audio': ['waveform', 'sample_rate', 'segment_length'],
            'load_and_preprocess': ['file_path']
        }
        
        print("Function Verification:")
        print("-" * 60)
        
        all_passed = True
        for func_name, expected_params in required_functions.items():
            if func_name in functions:
                func_info = functions[func_name]
                params = func_info['args']
                
                # Check if all expected parameters are present
                params_match = all(param in params for param in expected_params)
                
                status = "✅" if params_match and func_info['has_docstring'] else "⚠️"
                
                print(f"{status} {func_name}")
                print(f"   Line: {func_info['line']}")
                print(f"   Parameters: {', '.join(params)}")
                print(f"   Docstring: {'Yes' if func_info['has_docstring'] else 'No'}")
                
                if not params_match:
                    print(f"   ⚠️  Expected params: {', '.join(expected_params)}")
                    all_passed = False
                
                print()
            else:
                print(f"❌ {func_name} - NOT FOUND")
                all_passed = False
                print()
        
        print("="*60)
        
        # Check for imports
        print("\nImport Verification:")
        print("-" * 60)
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        
        required_imports = ['torch', 'torchaudio', 'config']
        for imp in required_imports:
            if imp in imports:
                print(f"✅ import {imp}")
            else:
                print(f"❌ import {imp} - NOT FOUND")
                all_passed = False
        
        print("\n" + "="*60)
        
        # Summary
        print("\nSummary:")
        print("-" * 60)
        print(f"Total functions found: {len(functions)}")
        print(f"Required functions: {len(required_functions)}")
        print(f"Functions with docstrings: {sum(1 for f in functions.values() if f['has_docstring'])}")
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL SYNTAX AND STRUCTURE CHECKS PASSED")
            print("\nAll required preprocessing functions are correctly defined:")
            print("  1. validate_wav - WAV file validation")
            print("  2. resample_audio - Audio resampling to 16kHz")
            print("  3. convert_to_mono - Stereo to mono conversion")
            print("  4. estimate_snr - SNR estimation in dB")
            print("  5. segment_audio - Long audio segmentation")
            print("  6. load_and_preprocess - Full preprocessing pipeline")
        else:
            print("❌ SOME CHECKS FAILED")
        print("="*60 + "\n")
        
        return all_passed
        
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = parse_and_verify()
    exit(0 if success else 1)
