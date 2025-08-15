import requests
import sys
import json
from datetime import datetime

class EduFlowAPITester:
    def __init__(self, base_url="https://e-learning-hub-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_course_id = None
        self.created_lesson_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "api/health", 200)

    def test_register(self, email, password, full_name, role="student"):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/auth/register",
            200,
            data={
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['user_id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_login(self, email, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/auth/login",
            200,
            data={
                "email": email,
                "password": password
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['user_id']
            return True
        return False

    def test_get_profile(self):
        """Test get user profile"""
        return self.run_test("Get User Profile", "GET", "api/user/profile", 200)

    def test_get_courses(self):
        """Test get all courses"""
        success, response = self.run_test("Get All Courses", "GET", "api/courses", 200)
        if success:
            courses_count = len(response.get('courses', []))
            print(f"   Found {courses_count} courses")
        return success, response

    def test_create_course(self, title, description, category, level="beginner"):
        """Test create course (requires instructor role)"""
        success, response = self.run_test(
            "Create Course",
            "POST",
            "api/courses",
            200,
            data={
                "title": title,
                "description": description,
                "category": category,
                "level": level,
                "duration_hours": 2
            }
        )
        if success and 'course_id' in response:
            self.created_course_id = response['course_id']
            return True
        return False

    def test_get_course_details(self, course_id):
        """Test get course by ID"""
        return self.run_test("Get Course Details", "GET", f"api/courses/{course_id}", 200)

    def test_create_lesson(self, course_id, title, content, order=1):
        """Test create lesson"""
        success, response = self.run_test(
            "Create Lesson",
            "POST",
            f"api/courses/{course_id}/lessons",
            200,
            data={
                "course_id": course_id,
                "title": title,
                "content": content,
                "order": order
            }
        )
        if success and 'lesson_id' in response:
            self.created_lesson_id = response['lesson_id']
            return True
        return False

    def test_update_progress(self, lesson_id):
        """Test update lesson progress"""
        return self.run_test(
            "Update Progress",
            "POST",
            "api/progress",
            200,
            data={
                "lesson_id": lesson_id,
                "completed": True
            }
        )

    def test_get_progress(self, course_id):
        """Test get course progress"""
        return self.run_test("Get Course Progress", "GET", f"api/progress/{course_id}", 200)

    def test_get_dashboard(self):
        """Test get dashboard data"""
        return self.run_test("Get Dashboard", "GET", "api/dashboard", 200)

    def test_get_videos(self):
        """Test get videos (requires instructor role)"""
        return self.run_test("Get Videos", "GET", "api/videos", 200)

    def test_get_videos_unauthorized(self):
        """Test get videos as student (should fail)"""
        success, response = self.run_test("Get Videos (Unauthorized)", "GET", "api/videos", 403)
        return success

    def test_instructor_login(self, email="instructor@eduflow.com", password="secret"):
        """Test instructor login with specific credentials"""
        success, response = self.run_test(
            "Instructor Login",
            "POST",
            "api/auth/login",
            200,
            data={
                "email": email,
                "password": password
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['user_id']
            user_role = response['user'].get('role', 'unknown')
            print(f"   Logged in as: {user_role}")
            return True, response['user']
        return False, None

def main():
    print("🚀 Starting EduFlow API Tests")
    print("=" * 50)
    
    tester = EduFlowAPITester()
    
    # Test 1: Health Check
    print("\n📋 Phase 1: Basic Health Check")
    if not tester.test_health_check()[0]:
        print("❌ Health check failed, stopping tests")
        return 1

    # Test 2: User Registration
    print("\n📋 Phase 2: User Authentication")
    test_email = f"jean.dupont.test.{datetime.now().strftime('%H%M%S')}@test.com"
    test_password = "password123"
    test_name = "Jean Dupont"
    
    if not tester.test_register(test_email, test_password, test_name):
        print("❌ Registration failed, stopping tests")
        return 1

    # Test 3: Get Profile
    if not tester.test_get_profile()[0]:
        print("❌ Get profile failed")
        return 1

    # Test 4: Get Courses
    print("\n📋 Phase 3: Course Management")
    success, courses_data = tester.test_get_courses()
    if not success:
        print("❌ Get courses failed")
        return 1
    
    existing_courses = courses_data.get('courses', [])
    print(f"   Found {len(existing_courses)} existing courses")

    # Test 5: Dashboard
    print("\n📋 Phase 4: Dashboard")
    if not tester.test_get_dashboard()[0]:
        print("❌ Dashboard failed")
        return 1

    # Test 6: Try to create course as student (should fail)
    print("\n📋 Phase 5: Authorization Tests")
    success = tester.test_create_course("Test Course", "Test Description", "Programming")
    if success:
        print("⚠️  Warning: Student was able to create course (should be forbidden)")
    else:
        print("✅ Correctly prevented student from creating course")

    # Test 7: Test with existing course if available
    if existing_courses:
        print("\n📋 Phase 6: Course Interaction Tests")
        first_course = existing_courses[0]
        course_id = first_course['course_id']
        
        # Get course details
        success, course_details = tester.test_get_course_details(course_id)
        if success:
            lessons = course_details.get('lessons', [])
            print(f"   Course has {len(lessons)} lessons")
            
            # Test progress if lessons exist
            if lessons:
                first_lesson = lessons[0]
                lesson_id = first_lesson['lesson_id']
                
                # Update progress
                if tester.test_update_progress(lesson_id)[0]:
                    # Get progress
                    tester.test_get_progress(course_id)
                    
                    # Check dashboard again to see updated stats
                    print("\n📋 Phase 7: Updated Dashboard After Progress")
                    tester.test_get_dashboard()

    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())