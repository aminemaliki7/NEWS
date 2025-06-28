import os
from dotenv import load_dotenv

def verify_production_environment():
    """Verify all required environment variables are set"""
    load_dotenv()
    
    required_vars = {
        'GEMINI_API_KEY': 'AIzaSyCFS-xORFSlZgvpjMRIfcu1LoRG24tv3ks',
        'GNEWS_API_KEY_1': 'bd064fab15e685656dfeac9704782222',
        'GNEWS_API_KEY_2': 'a5c492d42571ea2fd5ea17857005a604',
        'GNEWS_API_KEY_3': '722fcfc089454e173e1431434f7f7600',
        'GNEWS_API_KEY_4': 'e31ef3d65105ab5690cd52f0badb5f7d',
        'GNEWS_API_KEY_5': 'f8cb0b3a70bde173f07add91864a3059',
        'GNEWS_API_KEY_6': '960cc1e8bb7e2092fcd4a9fbd98b34fd',
        'GNEWS_API_KEY_7': '0f2f077606c504ef0f1b559d6b7e1805',
        'GNEWS_API_KEY_8': '39c5f97dbfa20c995c92b5f9c654dafd',
        'FIREBASE_API_KEY': 'AIzaSyDpVK1DyxtMcCir7jHO5nnm2AQBQatUuxQ',
        'FIREBASE_PROJECT_ID': 'newsnap-2d169',
        'FIREBASE_AUTH_DOMAIN': 'newsnap-2d169.firebaseapp.com',
        'FIREBASE_STORAGE_BUCKET': 'newsnap-2d169.firebasestorage.app',
        'FIREBASE_MESSAGING_SENDER_ID': '497848051101',
        'FIREBASE_APP_ID': '1:497848051101:web:cf9fef588e3b5610dd7b74',
        'FIREBASE_MEASUREMENT_ID': 'G-KSBP29N04K',
        'REDIS_URL': 'redis://red-d1en7g7fte5s73eleqp0:6379'
    }
    
    print("🔍 Verifying Production Environment...")
    print("=" * 50)
    
    missing_vars = []
    for var_name, expected_value in required_vars.items():
        actual_value = os.getenv(var_name)
        if actual_value:
            # Only show first 10 chars for security
            display_value = actual_value[:10] + "..." if len(actual_value) > 10 else actual_value
            print(f"✅ {var_name}: {display_value}")
        else:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: NOT SET")
    
    print("=" * 50)
    
    if missing_vars:
        print(f"🚨 {len(missing_vars)} environment variables are missing!")
        print("Missing variables:", ", ".join(missing_vars))
        return False
    else:
        print("🎉 All environment variables are properly configured!")
        print(f"📊 Total API Keys: {len([k for k in required_vars if 'API_KEY' in k])}")
        print("🚀 Ready for production deployment!")
        return True

if __name__ == "__main__":
    verify_production_environment()