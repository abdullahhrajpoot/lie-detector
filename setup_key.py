import os, sys
key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
if key:
    with open('.env', 'w') as f:
        f.write(f'GEMINI_API_KEY={key}\n')
    print("Key saved to .env")
    print("Run: python -c \"import dotenv; dotenv.load_dotenv()\" to load it")
    print("Or set it manually: set GEMINI_API_KEY=your_key (Windows)")
    print("Or: export GEMINI_API_KEY=your_key (Mac/Linux)")
else:
    print("Skipped. App will run in rule-based mode only.")
