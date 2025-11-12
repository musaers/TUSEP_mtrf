#!/usr/bin/env python3
"""
Backend API Testing Suite for Healthcare Maintenance System
Tests the removal of device code field and filtering functionality
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://healthmaint-app-1.preview.emergentagent.com/api"

# Test credentials - using correct credentials from review request
TEST_USERS = {
    "manager": {"email": "manager@hospital.com", "password": "password123"},
    "technician": {"email": "tech@hospital.com", "password": "password123"},
    "health_staff": {"email": "staff@hospital.com", "password": "password123"}
}

class BackendTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        self.devices = []
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details and not success:
            print(f"   Details: {details}")
        print()

    def authenticate_users(self):
        """Authenticate all test users"""
        print("🔐 Authenticating test users...")
        
        for role, credentials in TEST_USERS.items():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json=credentials,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.log_result(
                        f"Authentication - {role}",
                        True,
                        f"Successfully authenticated as {role}"
                    )
                else:
                    self.log_result(
                        f"Authentication - {role}",
                        False,
                        f"Failed to authenticate: {response.status_code}",
                        response.text
                    )
                    return False
                    
            except Exception as e:
                self.log_result(
                    f"Authentication - {role}",
                    False,
                    f"Authentication error: {str(e)}"
                )
                return False
        
        return True

    def get_auth_headers(self, role):
        """Get authorization headers for a role"""
        if role not in self.tokens:
            return {}
        return {"Authorization": f"Bearer {self.tokens[role]}"}

    def test_device_creation_without_code(self):
        """Test POST /api/devices - Device creation without code field"""
        print("📱 Testing device creation without code field...")
        
        test_device = {
            "type": "MRI Scanner",
            "location": "Radiology Department",
            "total_operating_hours": 8760.0
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/devices",
                json=test_device,
                headers={
                    **self.get_auth_headers("manager"),
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                device_data = response.json()
                
                # Check that response doesn't include code field
                if "code" in device_data:
                    self.log_result(
                        "Device Creation - No Code Field",
                        False,
                        "Response still contains 'code' field",
                        device_data
                    )
                else:
                    # Verify required fields are present
                    required_fields = ["id", "type", "location"]
                    missing_fields = [f for f in required_fields if f not in device_data]
                    
                    if missing_fields:
                        self.log_result(
                            "Device Creation - Required Fields",
                            False,
                            f"Missing required fields: {missing_fields}",
                            device_data
                        )
                    else:
                        self.devices.append(device_data)
                        self.log_result(
                            "Device Creation - Success",
                            True,
                            f"Device created successfully with ID: {device_data['id']}"
                        )
            else:
                self.log_result(
                    "Device Creation - API Call",
                    False,
                    f"Failed to create device: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Creation - Exception",
                False,
                f"Error creating device: {str(e)}"
            )

    def test_device_listing_without_filters(self):
        """Test GET /api/devices without filters"""
        print("📋 Testing device listing without filters...")
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/devices",
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                devices = response.json()
                
                if not isinstance(devices, list):
                    self.log_result(
                        "Device Listing - Response Type",
                        False,
                        "Response is not a list",
                        devices
                    )
                    return
                
                # Check that no device has code field
                devices_with_code = [d for d in devices if "code" in d]
                
                if devices_with_code:
                    self.log_result(
                        "Device Listing - No Code Field",
                        False,
                        f"Found {len(devices_with_code)} devices with 'code' field",
                        devices_with_code[:3]  # Show first 3 examples
                    )
                else:
                    self.devices.extend(devices)
                    self.log_result(
                        "Device Listing - Success",
                        True,
                        f"Retrieved {len(devices)} devices without 'code' field"
                    )
                    
            else:
                self.log_result(
                    "Device Listing - API Call",
                    False,
                    f"Failed to get devices: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Listing - Exception",
                False,
                f"Error getting devices: {str(e)}"
            )

    def test_device_filtering(self):
        """Test GET /api/devices with filters"""
        print("🔍 Testing device filtering functionality...")
        
        if not self.devices:
            self.log_result(
                "Device Filtering - Prerequisites",
                False,
                "No devices available for filtering tests"
            )
            return
        
        # Test device_id filter
        test_device = self.devices[0]
        device_id = test_device["id"]
        
        try:
            # Test partial device_id filter
            partial_id = device_id[:8]  # Use first 8 characters
            response = requests.get(
                f"{BACKEND_URL}/devices",
                params={"device_id": partial_id},
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                filtered_devices = response.json()
                
                # Check if our device is in the results
                found_device = any(d["id"] == device_id for d in filtered_devices)
                
                if found_device:
                    self.log_result(
                        "Device Filtering - device_id",
                        True,
                        f"Successfully filtered by device_id: {partial_id}"
                    )
                else:
                    self.log_result(
                        "Device Filtering - device_id",
                        False,
                        f"Device not found in filtered results for ID: {partial_id}",
                        filtered_devices
                    )
            else:
                self.log_result(
                    "Device Filtering - device_id API",
                    False,
                    f"Failed to filter by device_id: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Filtering - device_id Exception",
                False,
                f"Error filtering by device_id: {str(e)}"
            )
        
        # Test type filter
        try:
            device_type = test_device["type"]
            response = requests.get(
                f"{BACKEND_URL}/devices",
                params={"type": device_type},
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                filtered_devices = response.json()
                
                # Check if all returned devices have the correct type
                wrong_type_devices = [d for d in filtered_devices if device_type.lower() not in d["type"].lower()]
                
                if not wrong_type_devices:
                    self.log_result(
                        "Device Filtering - type",
                        True,
                        f"Successfully filtered by type: {device_type}"
                    )
                else:
                    self.log_result(
                        "Device Filtering - type",
                        False,
                        f"Found devices with wrong type in results",
                        wrong_type_devices[:3]
                    )
            else:
                self.log_result(
                    "Device Filtering - type API",
                    False,
                    f"Failed to filter by type: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Filtering - type Exception",
                False,
                f"Error filtering by type: {str(e)}"
            )
        
        # Test location filter
        try:
            device_location = test_device["location"]
            response = requests.get(
                f"{BACKEND_URL}/devices",
                params={"location": device_location},
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                filtered_devices = response.json()
                
                # Check if all returned devices have the correct location
                wrong_location_devices = [d for d in filtered_devices if device_location.lower() not in d["location"].lower()]
                
                if not wrong_location_devices:
                    self.log_result(
                        "Device Filtering - location",
                        True,
                        f"Successfully filtered by location: {device_location}"
                    )
                else:
                    self.log_result(
                        "Device Filtering - location",
                        False,
                        f"Found devices with wrong location in results",
                        wrong_location_devices[:3]
                    )
            else:
                self.log_result(
                    "Device Filtering - location API",
                    False,
                    f"Failed to filter by location: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Filtering - location Exception",
                False,
                f"Error filtering by location: {str(e)}"
            )
        
        # Test combined filters
        try:
            response = requests.get(
                f"{BACKEND_URL}/devices",
                params={
                    "type": test_device["type"],
                    "location": test_device["location"]
                },
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                filtered_devices = response.json()
                
                # Check if our device is in the results
                found_device = any(d["id"] == device_id for d in filtered_devices)
                
                if found_device:
                    self.log_result(
                        "Device Filtering - combined",
                        True,
                        f"Successfully filtered by type and location"
                    )
                else:
                    self.log_result(
                        "Device Filtering - combined",
                        False,
                        f"Device not found in combined filter results",
                        filtered_devices
                    )
            else:
                self.log_result(
                    "Device Filtering - combined API",
                    False,
                    f"Failed to filter with combined params: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Device Filtering - combined Exception",
                False,
                f"Error with combined filtering: {str(e)}"
            )

    def test_fault_creation_without_device_code(self):
        """Test POST /api/faults - Fault creation without device_code"""
        print("🔧 Testing fault creation without device_code...")
        
        if not self.devices:
            self.log_result(
                "Fault Creation - Prerequisites",
                False,
                "No devices available for fault creation test"
            )
            return
        
        test_device = self.devices[0]
        fault_data = {
            "device_id": test_device["id"],
            "description": "Test fault for device without code field - equipment malfunction detected during routine inspection"
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/faults",
                json=fault_data,
                headers={
                    **self.get_auth_headers("health_staff"),
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                fault_response = response.json()
                
                # Check that response doesn't include device_code field
                if "device_code" in fault_response:
                    self.log_result(
                        "Fault Creation - No device_code Field",
                        False,
                        "Response still contains 'device_code' field",
                        fault_response
                    )
                else:
                    # Verify required fields are present
                    required_fields = ["id", "device_id", "description", "status"]
                    missing_fields = [f for f in required_fields if f not in fault_response]
                    
                    if missing_fields:
                        self.log_result(
                            "Fault Creation - Required Fields",
                            False,
                            f"Missing required fields: {missing_fields}",
                            fault_response
                        )
                    else:
                        self.log_result(
                            "Fault Creation - Success",
                            True,
                            f"Fault created successfully with ID: {fault_response['id']}"
                        )
            else:
                self.log_result(
                    "Fault Creation - API Call",
                    False,
                    f"Failed to create fault: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Fault Creation - Exception",
                False,
                f"Error creating fault: {str(e)}"
            )

    def test_individual_device_retrieval(self):
        """Test GET /api/devices/{device_id} - Individual device retrieval"""
        print("🔍 Testing individual device retrieval...")
        
        if not self.devices:
            self.log_result(
                "Individual Device Retrieval - Prerequisites",
                False,
                "No devices available for individual retrieval test"
            )
            return
        
        test_device = self.devices[0]
        device_id = test_device["id"]
        
        try:
            response = requests.get(
                f"{BACKEND_URL}/devices/{device_id}",
                headers=self.get_auth_headers("manager")
            )
            
            if response.status_code == 200:
                device_data = response.json()
                
                # Check that response doesn't include code field
                if "code" in device_data:
                    self.log_result(
                        "Individual Device Retrieval - No Code Field",
                        False,
                        "Response still contains 'code' field",
                        device_data
                    )
                else:
                    # Verify required fields are present and correct
                    if device_data.get("id") == device_id:
                        self.log_result(
                            "Individual Device Retrieval - Success",
                            True,
                            f"Device retrieved successfully with ID: {device_id}"
                        )
                    else:
                        self.log_result(
                            "Individual Device Retrieval - ID Mismatch",
                            False,
                            f"Retrieved device ID doesn't match requested ID",
                            device_data
                        )
            elif response.status_code == 404:
                self.log_result(
                    "Individual Device Retrieval - Not Found",
                    False,
                    f"Device not found: {device_id}",
                    response.text
                )
            else:
                self.log_result(
                    "Individual Device Retrieval - API Call",
                    False,
                    f"Failed to retrieve device: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Individual Device Retrieval - Exception",
                False,
                f"Error retrieving device: {str(e)}"
            )

    def test_transfer_creation_without_device_code(self):
        """Test POST /api/transfers - Transfer creation without device_code"""
        print("🚚 Testing transfer creation without device_code...")
        
        if not self.devices:
            self.log_result(
                "Transfer Creation - Prerequisites",
                False,
                "No devices available for transfer creation test"
            )
            return
        
        test_device = self.devices[0]
        transfer_data = {
            "device_id": test_device["id"],
            "to_location": "Emergency Department",
            "reason": "Urgent need for equipment in emergency department due to increased patient load"
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/transfers",
                json=transfer_data,
                headers={
                    **self.get_auth_headers("manager"),
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                transfer_response = response.json()
                
                # Check that response doesn't include device_code field
                if "device_code" in transfer_response:
                    self.log_result(
                        "Transfer Creation - No device_code Field",
                        False,
                        "Response still contains 'device_code' field",
                        transfer_response
                    )
                else:
                    # Verify required fields are present
                    required_fields = ["id", "device_id", "to_location", "reason", "status"]
                    missing_fields = [f for f in required_fields if f not in transfer_response]
                    
                    if missing_fields:
                        self.log_result(
                            "Transfer Creation - Required Fields",
                            False,
                            f"Missing required fields: {missing_fields}",
                            transfer_response
                        )
                    else:
                        self.log_result(
                            "Transfer Creation - Success",
                            True,
                            f"Transfer created successfully with ID: {transfer_response['id']}"
                        )
            else:
                self.log_result(
                    "Transfer Creation - API Call",
                    False,
                    f"Failed to create transfer: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            self.log_result(
                "Transfer Creation - Exception",
                False,
                f"Error creating transfer: {str(e)}"
            )

    def test_api_responses_no_code_field(self):
        """Test that all API responses don't include code field"""
        print("🔍 Testing all API responses for absence of code field...")
        
        endpoints_to_test = [
            ("/devices", "manager"),
            ("/faults", "manager"),
            ("/transfers", "manager"),
            ("/dashboard/stats", "manager")
        ]
        
        for endpoint, role in endpoints_to_test:
            try:
                response = requests.get(
                    f"{BACKEND_URL}{endpoint}",
                    headers=self.get_auth_headers(role)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for code field in response
                    code_found = False
                    if isinstance(data, list):
                        code_found = any("code" in item for item in data if isinstance(item, dict))
                    elif isinstance(data, dict):
                        code_found = "code" in data or any(
                            "code" in item for item in data.values() 
                            if isinstance(item, (list, dict))
                        )
                    
                    if code_found:
                        self.log_result(
                            f"API Response Check - {endpoint}",
                            False,
                            f"Found 'code' field in response from {endpoint}"
                        )
                    else:
                        self.log_result(
                            f"API Response Check - {endpoint}",
                            True,
                            f"No 'code' field found in {endpoint} response"
                        )
                else:
                    self.log_result(
                        f"API Response Check - {endpoint}",
                        False,
                        f"Failed to get response from {endpoint}: {response.status_code}",
                        response.text
                    )
                    
            except Exception as e:
                self.log_result(
                    f"API Response Check - {endpoint}",
                    False,
                    f"Error checking {endpoint}: {str(e)}"
                )

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests")
        print("=" * 50)
        
        # Authenticate users first
        if not self.authenticate_users():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        self.test_device_listing_without_filters()
        self.test_device_creation_without_code()
        self.test_individual_device_retrieval()
        self.test_device_filtering()
        self.test_fault_creation_without_device_code()
        self.test_transfer_creation_without_device_code()
        self.test_api_responses_no_code_field()
        
        # Print summary
        self.print_summary()
        
        return self.get_overall_success()

    def print_summary(self):
        """Print test summary"""
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 50)

    def get_overall_success(self):
        """Get overall test success status"""
        return all(result["success"] for result in self.test_results)

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()