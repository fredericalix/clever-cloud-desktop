#!/usr/bin/env python3
"""
Test script to verify applications and add-ons loading for each organization.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clever_desktop.api.client import CleverCloudClient
import keyring

async def test_apps_and_addons():
    """Test loading applications and add-ons for each organization."""
    
    # Check if we have a stored token
    try:
        token = keyring.get_password("clever-desktop", "api-token")
        if not token:
            print("❌ No stored token found. Please run the main application first to authenticate.")
            return
    except Exception as e:
        print(f"❌ Failed to get stored token: {e}")
        return
    
    print("✅ Authentication token found")
    
    # Create API client (it will automatically use the stored token)
    api_client = CleverCloudClient()
    
    try:
        # Authenticate with stored credentials
        if not await api_client.authenticate_with_stored_credentials():
            print("❌ Failed to authenticate with stored credentials")
            return
        
        print("✅ Authentication successful")
        
        # Get user info and organizations
        print("\n📋 Loading user info and organizations...")
        user_info = await api_client.get_user_info()
        organizations = await api_client.get_organizations()
        
        print(f"👤 User: {user_info.get('name', 'Unknown')}")
        print(f"🏢 Found {len(organizations)} organizations:")
        
        for org in organizations:
            print(f"  - {org.get('name', 'Unknown')} ({org.get('id', 'no-id')})")
        
        # Test applications and add-ons for each organization
        for org in organizations:
            org_id = org.get('id')
            org_name = org.get('name', 'Unknown')
            
            print(f"\n🔍 Testing organization: {org_name}")
            print(f"   ID: {org_id}")
            
            # Test applications
            try:
                print("   📱 Loading applications...")
                applications = await api_client.get_applications(org_id)
                print(f"   ✅ Found {len(applications)} applications")
                
                for app in applications[:3]:  # Show first 3 apps
                    app_name = app.get('name', 'Unknown')
                    app_state = app.get('state', 'unknown')
                    print(f"      - {app_name} ({app_state})")
                
                if len(applications) > 3:
                    print(f"      ... and {len(applications) - 3} more")
                    
            except Exception as e:
                print(f"   ❌ Failed to load applications: {e}")
            
            # Test add-ons
            try:
                print("   🔌 Loading add-ons...")
                addons = await api_client.get_addons(org_id)
                print(f"   ✅ Found {len(addons)} add-ons")
                
                for addon in addons[:3]:  # Show first 3 add-ons
                    addon_name = addon.get('name', 'Unknown')
                    provider = addon.get('provider', {}).get('name', 'Unknown')
                    print(f"      - {addon_name} ({provider})")
                
                if len(addons) > 3:
                    print(f"      ... and {len(addons) - 3} more")
                    
            except Exception as e:
                print(f"   ❌ Failed to load add-ons: {e}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the API client
        await api_client.close()

if __name__ == "__main__":
    asyncio.run(test_apps_and_addons()) 