#!/usr/bin/env python3
"""
Debug Authentication Credentials Issue
Focus: onebaldegg@gmail.com login failure
"""

import sys
import os
sys.path.append('/app')

from backend_test import BrandWatchAPITester

def main():
    print("🔍 AUTHENTICATION CREDENTIAL DEBUG SESSION")
    print("="*80)
    print("Target: onebaldegg@gmail.com authentication issue")
    print("Expected: Login should work with correct password")
    print("="*80)
    
    tester = BrandWatchAPITester()
    
    # Test basic connectivity first
    print("\n🔧 Testing Basic API Connectivity...")
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ Basic API connectivity failed. Cannot proceed with authentication debug.")
        return 1
    
    print("✅ Basic API connectivity working")
    
    # Run the comprehensive authentication debug
    auth_resolved = tester.debug_authentication_credentials()
    
    if auth_resolved:
        print("\n🎉 AUTHENTICATION ISSUE RESOLVED!")
        print("✅ Test account login is now working")
        
        # Test authenticated endpoints to confirm
        print("\n🔐 Testing Authenticated Endpoints...")
        
        profile_success, profile_response = tester.test_user_profile_authenticated()
        if profile_success:
            print("✅ User profile access working")
            user_tier = profile_response.get('subscription_tier', 'unknown')
            print(f"   Subscription tier: {user_tier}")
        
        sentiment_success, _ = tester.test_protected_sentiment_analysis()
        if sentiment_success:
            print("✅ Protected sentiment analysis working")
        
        return 0
    else:
        print("\n❌ AUTHENTICATION ISSUE NOT RESOLVED")
        print("The test account login is still failing")
        print("\nNext steps for main agent:")
        print("1. Check database user record for onebaldegg@gmail.com")
        print("2. Verify password hash matches expected BCrypt format")
        print("3. Consider recreating the test user with correct credentials")
        print("4. Check BCrypt password verification logic in backend")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())