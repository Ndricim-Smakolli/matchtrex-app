#!/usr/bin/env python3
"""
Test script to verify all environment variables are properly loaded
"""
import os

def test_environment_variables():
    """Test if all required environment variables are accessible"""

    print("🔧 Testing Environment Variables...\n")

    # Required environment variables
    env_vars = {
        "MISTRAL_API_KEY": "Mistral AI API Key",
        "TWOCAPTCHA_KEY": "2captcha API Key",
        "EMAIL_USER": "Email User",
        "EMAIL_PASS": "Email Password",
        "SMTP_SERVER": "SMTP Server",
        "SMTP_PORT": "SMTP Port",
        "GOOGLE_SHEETS_ID": "Google Sheets ID",
        "GOOGLE_SHEETS_CREDENTIALS_PATH": "Google Credentials Path",
        "HOST": "Server Host",
        "PORT": "Server Port",
        "DATA_SOURCE": "Data Source"
    }

    print("Environment Variables Status:")
    print("-" * 50)

    all_good = True
    for var_name, description in env_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive data
            if "KEY" in var_name or "PASS" in var_name:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var_name:<30} = {display_value}")
        else:
            print(f"❌ {var_name:<30} = NOT SET")
            all_good = False

    print("-" * 50)
    if all_good:
        print("🎉 All environment variables are properly set!")
    else:
        print("⚠️  Some environment variables are missing. The app will use fallback values.")

    print(f"\n📂 Current working directory: {os.getcwd()}")
    print(f"🐍 Python executable: {os.sys.executable}")

    return all_good

if __name__ == "__main__":
    test_environment_variables()