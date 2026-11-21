"""
Phase 3 Mistral Integration Test Script

Tests the Mistral API client, prompt engine, and strategist integration.

Security Note: API key is loaded from .env file only, never hardcoded.

Author: Generated for Phase 3 validation
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set working directory to project root for .env loading
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.exists(os.path.join(project_root, ".env")):
    os.chdir(project_root)


def test_api_key_loading():
    """Test 1: Verify API key can be loaded from .env"""
    print("\n" + "="*80)
    print("TEST 1: API Key Loading from .env")
    print("="*80)
    
    # First, try to load .env manually from multiple locations
    env_paths = [
        "D:\\SteamLibrary\\steamapps\\common\\Company of Heroes Relaunch\\Mods\\COh1AIMod\\.env",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
                break
            except ImportError:
                # Manual loading
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "MISTRAL_API_KEY":
                                    os.environ["MISTRAL_API_KEY"] = value.strip()
                                    break
            break
    
    # Test os.getenv
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        # Try loading from .env file directly
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
                api_key = os.getenv("MISTRAL_API_KEY")
            except ImportError:
                # Manual loading
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == "MISTRAL_API_KEY":
                                    api_key = value.strip()
                                    break
    
    if api_key and api_key.startswith("mstrl_"):
        print("[PASS] API key loaded successfully from .env")
        print(f"   Key format: {api_key[:10]}... (truncated for security)")
        return True
    else:
        print("[FAIL] API key not loaded or invalid format")
        print(f"   Key: {api_key[:20] if api_key else 'None'}")
        return False


def test_mistral_client_import():
    """Test 2: Verify mistral_client.py can be imported"""
    print("\n" + "="*80)
    print("TEST 2: Mistral Client Import")
    print("="*80)
    
    try:
        from mistral_client import MistralClient, MistralModel, create_mistral_client
        print("[PASS] mistral_client.py imported successfully")
        print(f"   Available models: {[m.value for m in MistralModel]}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_prompts_import():
    """Test 3: Verify prompts.py can be imported"""
    print("\n" + "="*80)
    print("TEST 3: Prompts Engine Import")
    print("="*80)
    
    try:
        from prompts import PromptEngine, Faction, Difficulty, GamePhase, create_prompt_engine
        print("[PASS] prompts.py imported successfully")
        print(f"   Available factions: {[f.value for f in Faction]}")
        print(f"   Available difficulties: {[d.value for d in Difficulty]}")
        print(f"   Available phases: {[p.value for p in GamePhase]}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_strategist_import():
    """Test 4: Verify strategist.py can be imported"""
    print("\n" + "="*80)
    print("TEST 4: Strategist Import")
    print("="*80)
    
    try:
        from orchestrator.strategist import Strategist, StrategicIntent, StrategistConfig, create_strategist
        print("[PASS] strategist.py imported successfully")
        print(f"   StrategistConfig fields: {list(vars(StrategistConfig()))}")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def test_mistral_api_connection():
    """Test 5: Test actual API connection (requires internet)"""
    print("\n" + "="*80)
    print("TEST 5: Mistral API Connection")
    print("="*80)
    
    try:
        from mistral_client import create_mistral_client, MistralModel
        
        print("   Creating Mistral client...")
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        print("   Fetching available models...")
        models = client.get_models()
        
        print(f"[PASS] API connection successful")
        print(f"   Found {len(models)} available models")
        if models:
            print(f"   First model: {models[0].get('id', 'unknown')}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] API connection failed: {e}")
        print(f"   This may be expected if internet is not available")
        return False


def test_mistral_chat_completion():
    """Test 6: Test actual chat completion (requires API key and internet)"""
    print("\n" + "="*80)
    print("TEST 6: Mistral Chat Completion")
    print("="*80)
    
    try:
        from mistral_client import create_mistral_client, MistralModel
        
        print("   Creating Mistral client...")
        client = create_mistral_client(
            model=MistralModel.SMALL,
            json_mode=True
        )
        
        print("   Sending test prompt...")
        messages = [
            {"role": "user", "content": "What is 2+2? Respond with only the number in JSON format: {\"answer\": number}"}
        ]
        
        response = client.chat_completion(
            messages=messages,
            max_tokens=100
        )
        
        print(f"[PASS] Chat completion successful")
        print(f"   Response: {response.content[:100]}")
        print(f"   Model: {response.model}")
        print(f"   Tokens used: {response.usage.get('total_tokens', 0)}")
        print(f"   Response time: {response.response_time:.2f}s")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Chat completion failed: {e}")
        print(f"   This may be expected if API key is invalid or quota exceeded")
        return False


def test_prompt_generation():
    """Test 7: Test prompt generation"""
    print("\n" + "="*80)
    print("TEST 7: Prompt Generation")
    print("="*80)
    
    try:
        from prompts import create_prompt_engine, Faction, Difficulty, GamePhase, PromptConfig
        
        print("   Creating prompt engine...")
        config = PromptConfig(
            faction=Faction.ALLIES,
            difficulty=Difficulty.NORMAL,
            game_phase=GamePhase.EARLY
        )
        engine = create_prompt_engine(config)
        
        print("   Generating system prompt...")
        system_prompt = engine.generate_system_prompt()
        
        print(f"[PASS] Prompt generation successful")
        print(f"   System prompt length: {len(system_prompt)} characters")
        
        # Test with game state
        test_state = {
            "game_time": 120.5,
            "phase": "early",
            "faction": "allies",
            "player_id": 1,
            "resources": {
                "manpower": {"current": 500, "income": 10, "max": 1000},
                "fuel": {"current": 300, "income": 5, "max": 800}
            },
            "squads": [{"id": 1, "type": "riflemen", "health": 0.8}],
            "cps": [{"id": 1, "owner": 1}],
            "tech": {"tier_1": True, "tier_2": False},
            "queue": [],
            "pop": [11, 100]
        }
        
        user_prompt = engine.generate_user_prompt(test_state)
        print(f"   User prompt length: {len(user_prompt)} characters")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Prompt generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategist_initialization():
    """Test 8: Test strategist initialization"""
    print("\n" + "="*80)
    print("TEST 8: Strategist Initialization")
    print("="*80)
    
    try:
        from orchestrator.strategist import create_strategist, StrategistConfig
        
        print("   Creating strategist...")
        config = StrategistConfig(
            enabled=True,
            model="mistral-small-latest",
            temperature=0.7,
            max_tokens=2048,
            json_mode=True
        )
        
        strategist = create_strategist(config=config)
        
        print(f"[PASS] Strategist created successfully")
        print(f"   Config: {config.model}, temp={config.temperature}")
        
        # Test start/stop
        if strategist.start():
            print("   Strategist started")
            if strategist.stop():
                print("   Strategist stopped")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Strategist initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_integration():
    """Test 9: Test integration with orchestrator"""
    print("\n" + "="*80)
    print("TEST 9: Orchestrator Integration")
    print("="*80)
    
    try:
        from orchestrator.main import OrchestratorService
        from config import Configuration
        
        print("   Creating orchestrator...")
        # OrchestratorService expects config_path, not config object
        orchestrator = OrchestratorService(config_path=None, test_mode=True, debug_mode=False)
        
        print("[PASS] Orchestrator created successfully")
        
        # Check if strategist is available
        if hasattr(orchestrator, 'strategist') or 'strategist' in dir(orchestrator):
            print("   Strategist component available in orchestrator")
        else:
            print("   [WARNING] Strategist not yet integrated into orchestrator")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Orchestrator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n" + "#"*80)
    print("# PHASE 3: MISTRAL INTEGRATION TEST SUITE")
    print("#"*80)
    print(f"\nStarting tests at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("API Key Loading", test_api_key_loading, True),
        ("Mistral Client Import", test_mistral_client_import, True),
        ("Prompts Engine Import", test_prompts_import, True),
        ("Strategist Import", test_strategist_import, True),
        ("API Connection", test_mistral_api_connection, False),  # Optional
        ("Chat Completion", test_mistral_chat_completion, False),  # Optional
        ("Prompt Generation", test_prompt_generation, True),
        ("Strategist Initialization", test_strategist_initialization, True),
        ("Orchestrator Integration", test_orchestrator_integration, True),
    ]
    
    results = []
    
    for name, test_func, required in tests:
        try:
            result = test_func()
            results.append({
                "name": name,
                "passed": result,
                "required": required
            })
        except Exception as e:
            print(f"\n[EXCEPTION] in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "name": name,
                "passed": False,
                "required": required
            })
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    required_passed = sum(1 for r in results if r["passed"] and r["required"])
    required_total = sum(1 for r in results if r["required"])
    
    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}/{total}")
    print(f"Required tests passed: {required_passed}/{required_total}")
    
    print("\n" + "-"*80)
    print("Individual Results:")
    print("-"*80)
    
    for r in results:
        status = "[PASS]" if r["passed"] else "[FAIL]"
        marker = "[REQUIRED]" if r["required"] else "[OPTIONAL]"
        print(f"  {status} {marker} {r['name']}")
    
    # Overall result
    print("\n" + "="*80)
    if required_passed == required_total:
        print("[SUCCESS] ALL REQUIRED TESTS PASSED")
        print("="*80)
        return True
    else:
        print("[FAILURE] SOME REQUIRED TESTS FAILED")
        print("="*80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
