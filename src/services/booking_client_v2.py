"""
Updated BookingClient using localStorage token + requests.

This version:
1. Uses Selenium ONLY for initial login to get the token
2. Extracts the Bearer token from localStorage
3. Uses requests for ALL subsequent API calls

Much faster and more efficient than clicking through the UI!
"""

import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta

# Selenium imports (only for login)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class BookingClient:
    """Client for interacting with TU Delft X booking system using HTTP API."""
    
    BASE_URL = "https://x.tudelft.nl"
    API_BASE_URL = "https://backbone-web-api.production.delft.delcom.nl"
    
    # University/Institution options for OIDC login
    INSTITUTIONS = {
        'tudelft': {
            'name': 'Delft University of Technology',
            'selector': '[data-title="Delft University of Technology"]',
            'text_match': 'TU Delft'
        },
        'inholland': {
            'name': 'Inholland University of Applied Sciences',
            'selector': '[data-title="Inholland University of Applied Sciences"]',
            'text_match': 'Inholland'
        },
        'thuas': {
            'name': 'The Hague University of Applied Sciences (THUAS)',
            'selector': '[data-title="The Hague University of Applied Sciences (THUAS)"]',
            'text_match': 'THUAS'
        }
    }
    
    # Location/Product mappings
    LOCATIONS = {
        'Fitness': {
            'product_id': 20061,
        },
        'X1': {
            'product_id': 20045,
            'resources': {'A': 4, 'B': 5}
        },
        'X3': {
            'product_id': 20047,
            'resources': {'A': 16534, 'B': 16535}
        }
    }
    
    def __init__(self, institution: str = 'tudelft'):
        """
        Initialize the booking client.
        
        Args:
            institution: Which university to use ('tudelft', 'inholland', or 'thuas')
        """
        if institution not in self.INSTITUTIONS:
            raise ValueError(f"Institution must be one of: {', '.join(self.INSTITUTIONS.keys())}")
        
        self.institution = institution
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.access_token = None
        self.token_expires_at = None
        self.user_data = None
    
    def login_and_get_token(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login using Selenium to get the Bearer token from localStorage.
        
        Args:
            username: University NetID/username
            password: TU Delft password
            
        Returns:
            dict with 'success', 'message', and 'token' keys
        """
        driver = None
        try:
            # Setup Selenium
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # Uncomment for headless mode:
            # options.add_argument('--headless')
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            
            # Navigate to X
            print("🌐 Navigating to X booking system...")
            driver.get(f'{self.BASE_URL}/')
            
            # Click OIDC login button
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="oidc-login-button"]'))
            )
            login_button.click()
            print("✅ Clicked OIDC login button")
            
            # Select institution (TU Delft, Inholland, or THUAS)
            institution_config = self.INSTITUTIONS[self.institution]
            
            # Try multiple selectors
            institution_button = None
            wait = WebDriverWait(driver, 10)
            
            # Try CSS selector first
            try:
                institution_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, institution_config['selector']))
                )
            except:
                # Fallback: try XPath with text match
                try:
                    institution_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{institution_config['text_match']}')]"))
                    )
                except:
                    pass
            
            if not institution_button:
                return {'success': False, 'message': f'Could not find {institution_config["name"]} button'}
            
            institution_button.click()
            print(f"✅ Selected {institution_config['name']}")
            
            # Enter credentials
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            password_field = driver.find_element(By.ID, 'password')
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            submit_button = driver.find_element(By.ID, 'submit_button')
            submit_button.click()
            print("✅ Submitted credentials")
            
            # Wait for redirect back to x.tudelft.nl (avoid SURFconext pages)
            WebDriverWait(driver, 30).until(
                lambda d: 'x.tudelft.nl' in d.current_url and 'surf' not in d.current_url.lower()
            )
            print("✅ Redirected back to X")
            
            # Give Angular app time to set localStorage
            import time
            time.sleep(3)
            
            # Extract token from localStorage
            auth_data_str = driver.execute_script("return window.localStorage.getItem('delcom_auth');")
            
            if not auth_data_str:
                return {
                    'success': False,
                    'message': 'No auth data found in localStorage'
                }
            
            auth_data = json.loads(auth_data_str)
            
            # Extract token
            if 'tokenResponse' in auth_data and 'accessToken' in auth_data['tokenResponse']:
                self.access_token = auth_data['tokenResponse']['accessToken']
                self.token_expires_at = auth_data['tokenResponse'].get('issuedAt', 0) + auth_data['tokenResponse'].get('expiresIn', 86400)
                self.user_data = auth_data.get('member', {})
                
                # Set Authorization header for all requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                print(f"✅ Got Bearer token (expires in {auth_data['tokenResponse'].get('expiresIn', 0)}s)")
                print(f"✅ Logged in as: {self.user_data.get('firstName')} {self.user_data.get('lastName')}")
                
                return {
                    'success': True,
                    'message': 'Successfully authenticated',
                    'token': self.access_token,
                    'user': self.user_data
                }
            else:
                return {
                    'success': False,
                    'message': 'Token not found in auth data'
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Login failed: {str(e)}'
            }
        finally:
            if driver:
                driver.quit()
    
    def is_logged_in(self) -> bool:
        """Check if we have a valid token."""
        if not self.access_token:
            return False
        
        # Check if token expired
        if self.token_expires_at:
            current_time = datetime.now().timestamp()
            if current_time >= self.token_expires_at:
                return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        return self.user_data if self.is_logged_in() else None
    
    def get_available_slots(self, location: str, date: str, sub_location: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available booking slots.
        
        Args:
            location: 'Fitness', 'X1', or 'X3'
            date: Date in YYYY-MM-DD format
            sub_location: For X1/X3, specify 'A' or 'B'
            
        Returns:
            dict with 'success', 'slots', and 'message' keys
        """
        if not self.is_logged_in():
            return {'success': False, 'message': 'Not logged in'}
        
        # Get product ID
        if location not in self.LOCATIONS:
            return {'success': False, 'message': f'Unknown location: {location}'}
        
        product_id = self.LOCATIONS[location]['product_id']
        
        # Real endpoint: GET /bookable-slots
        # s={"startDate":"...","endDate":"...","tagIds":{"$in":[...]},"productIds":{"$in":[...]},"availableFromDate":{"$gt":"..."},"availableTillDate":{"$gte":"..."}}
        url = f'{self.API_BASE_URL}/bookable-slots'
        
        # Parse date and create date range (full day)
        target_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        now = datetime.utcnow()
        
        # Build search query
        search_query = {
            'startDate': start_date.isoformat() + 'Z',
            'endDate': end_date.isoformat() + 'Z',
            'productIds': {'$in': [product_id]},
            'availableFromDate': {'$gt': now.isoformat() + 'Z'},
            'availableTillDate': {'$gte': start_date.isoformat() + 'Z'}
        }
        
        # Add resource filter if sub_location specified
        if sub_location and 'resources' in self.LOCATIONS[location]:
            resource_id = self.LOCATIONS[location]['resources'].get(sub_location)
            if resource_id:
                search_query['resourceIds'] = {'$in': [resource_id]}
        
        params = {
            's': json.dumps(search_query),
            'join': ['linkedProduct', 'linkedProduct.translations', 'product', 'product.translations']
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle paginated response - slots are in 'data' key
            if isinstance(data, dict) and 'data' in data:
                slots = data['data']
            else:
                slots = data if isinstance(data, list) else []
            
            return {
                'success': True,
                'slots': slots,
                'count': len(slots) if isinstance(slots, list) else 0,
                'message': 'Retrieved available slots'
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'message': f'API error: {e.response.status_code}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Request failed: {str(e)}'
            }
    
    def get_current_bookings(self, include_past: bool = False) -> Dict[str, Any]:
        """
        Get user's current bookings.
        
        Args:
            include_past: Whether to include past bookings
            
        Returns:
            dict with 'success', 'bookings', 'count', and 'message' keys
        """
        if not self.is_logged_in():
            return {'success': False, 'message': 'Not logged in'}
        
        # Correct endpoint: /participations (not /bookings)
        # This is discovered via network inspection - returns participations with joined booking data
        url = f'{self.API_BASE_URL}/participations'
        
        user_id = self.user_data.get('id')
        if not user_id:
            return {'success': False, 'message': 'User ID not available'}
        
        # Calculate date range for filter
        today = datetime.now(timezone.utc)
        range_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = (today + timedelta(days=28)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Build MongoDB query filter matching network inspection
        # $or matches participations where user is memberId OR invitedMemberId
        filter_query = {
            "$or": [
                {"memberId": user_id},
                {"invitedMemberId": user_id}
            ],
            "booking.startDate": {"$gte": range_start.isoformat()},
            "booking.endDate": {"$lte": range_end.isoformat()}
        }
        
        params = {
            's': json.dumps(filter_query),
            'join': 'booking',
            'sort': 'booking.startDate,ASC',
            'fetchOptimizedCustomerDashboard': 'true',
            'fetchTicket': 'false'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # The API returns a nested structure with multiple categories under 'data' key
            # Structure: {data: {bookings: [], participations: [], products: [], ...}, count: X, total: X, ...}
            # We need to extract just the bookings from this structure
            if isinstance(result, dict) and 'data' in result:
                data = result.get('data', {})
                
                # Extract bookings from the nested structure
                if isinstance(data, dict) and 'bookings' in data:
                    # Nested structure with bookings array
                    bookings = data.get('bookings', [])
                    count = len(bookings)
                else:
                    # Fallback: might be direct list structure or empty
                    bookings = data if isinstance(data, list) else []
                    count = len(bookings)
            else:
                # Old-style paginated response (shouldn't happen now)
                bookings = result if isinstance(result, list) else []
                count = len(bookings)
            
            return {
                'success': True,
                'bookings': bookings,
                'count': count,
                'message': 'Retrieved bookings'
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'message': f'API error: {e.response.status_code}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Request failed: {str(e)}'
            }
    
    def create_booking(self, slot_id: int, product_id: int, resource_id: Optional[int] = None,
                       start_time: Optional[str] = None, end_time: Optional[str] = None,
                       linked_product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new booking (participation).
        
        Args:
            slot_id: The bookable slot ID (the bookingId from the slot)
            product_id: Main product ID (bookableProductId)
            resource_id: Optional resource ID (for X1/X3 sub-locations)
            start_time: Start time in ISO format (e.g., "2025-11-17T14:00:00.000Z")
            end_time: End time in ISO format (e.g., "2025-11-17T14:59:00.000Z")
            linked_product_id: Optional linked product ID (bookableLinkedProductId)
            
        Returns:
            dict with 'success', 'booking_id', and 'message' keys
        """
        if not self.is_logged_in():
            return {'success': False, 'message': 'Not logged in'}
        
        # Real endpoint: POST /participations
        url = f'{self.API_BASE_URL}/participations'
        
        # Get user ID for memberId
        user_id = self.user_data.get('id')
        if not user_id:
            return {'success': False, 'message': 'User ID not available'}
        
        # Build params nested object with times
        params = {
            'startDate': start_time,
            'endDate': end_time,
            'bookableProductId': product_id,
            'invitedMemberEmails': [],
            'invitedGuests': [],
            'invitedOthers': [],
            'primaryPurchaseMessage': None,
            'secondaryPurchaseMessage': None,
            'clickedOnBook': True
        }
        
        # Add linked product if provided
        if linked_product_id:
            params['bookableLinkedProductId'] = linked_product_id
        
        # Build main payload - CRITICAL: bookingId must be in the main payload, not in params!
        payload = {
            'organizationId': None,
            'memberId': user_id,  # Integer, not string
            'bookingId': slot_id,  # The bookingId from the slot - REQUIRED!
            'primaryPurchaseMessage': None,
            'secondaryPurchaseMessage': None,
            'params': params,
            'dateOfRegistration': None
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'booking_id': result.get('id'),
                'message': 'Booking created successfully',
                'data': result
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                return {
                    'success': False,
                    'message': 'Slot already booked'
                }
            return {
                'success': False,
                'message': f'API error: {e.response.status_code}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Request failed: {str(e)}'
            }
    
    def cancel_booking(self, booking_id: int) -> Dict[str, Any]:
        """
        Cancel a booking (participation).
        
        Args:
            booking_id: The participation ID to cancel
            
        Returns:
            dict with 'success' and 'message' keys
        """
        if not self.is_logged_in():
            return {'success': False, 'message': 'Not logged in'}
        
        # Real endpoint: DELETE /participations/{id}
        url = f'{self.API_BASE_URL}/participations/{booking_id}'
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Booking cancelled successfully'
            }
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'message': f'API error: {e.response.status_code}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Request failed: {str(e)}'
            }
    
    def logout(self) -> Dict[str, Any]:
        """Clear session and token."""
        self.access_token = None
        self.token_expires_at = None
        self.user_data = None
        self.session.headers.pop('Authorization', None)
