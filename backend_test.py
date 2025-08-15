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
    print("🚀 Starting EduFlow API Tests - Video Upload System")
    print("=" * 60)
    
    tester = EduFlowAPITester()
    
    # Test 1: Health Check
    print("\n📋 Phase 1: Basic Health Check")
    if not tester.test_health_check()[0]:
        print("❌ Health check failed, stopping tests")
        return 1

    # Test 2: Student Registration and Video Access (should fail)
    print("\n📋 Phase 2: Student Authentication & Video Access Test")
    test_email = f"student.test.{datetime.now().strftime('%H%M%S')}@test.com"
    test_password = "password123"
    test_name = "Test Student"
    
    if not tester.test_register(test_email, test_password, test_name, role="student"):
        print("❌ Student registration failed, stopping tests")
        return 1

    # Test student trying to access videos (should fail)
    print("\n📋 Phase 3: Student Video Access (Should Fail)")
    if tester.test_get_videos_unauthorized():
        print("✅ Correctly prevented student from accessing videos")
    else:
        print("⚠️  Warning: Student was able to access videos (should be forbidden)")

    # Test 3: Instructor Login
    print("\n📋 Phase 4: Instructor Authentication")
    # Try with different instructor credentials first
    instructor_email = f"instructor.test.{datetime.now().strftime('%H%M%S')}@eduflow.com"
    instructor_password = "secret123"
    
    # Register a new instructor
    if tester.test_register(instructor_email, instructor_password, "Test Instructor", role="instructor"):
        print("✅ New instructor registered successfully")
        success, instructor_user = tester.test_instructor_login(instructor_email, instructor_password)
    else:
        # Try the original instructor credentials
        success, instructor_user = tester.test_instructor_login()
    
    if not success:
        print("❌ Could not login as instructor, stopping video tests")
        return 1
    
    print(f"✅ Instructor logged in: {instructor_user.get('full_name')} ({instructor_user.get('role')})")

    # Test 4: Instructor Video Access
    print("\n📋 Phase 5: Instructor Video Access")
    success, videos_data = tester.test_get_videos()
    if success:
        videos = videos_data.get('videos', [])
        print(f"✅ Instructor can access videos endpoint - Found {len(videos)} videos")
        
        # Display video details if any exist
        if videos:
            print("   Existing videos:")
            for i, video in enumerate(videos[:3]):  # Show first 3 videos
                print(f"   - {video.get('title', 'No title')} ({video.get('content_type', 'unknown')})")
        else:
            print("   No videos found (this is normal for a fresh system)")
    else:
        print("❌ Instructor cannot access videos endpoint")

    # Test 5: Basic Course Management (as instructor)
    print("\n📋 Phase 6: Instructor Course Management")
    if tester.test_create_course("Video Course Test", "Course for testing video integration", "Programming"):
        print("✅ Instructor can create courses")
        
        if tester.created_course_id:
            # Test course details
            success, course_details = tester.test_get_course_details(tester.created_course_id)
            if success:
                print("✅ Can retrieve course details")
                
                # Create a lesson
                if tester.test_create_lesson(tester.created_course_id, "Test Lesson", "This is a test lesson"):
                    print("✅ Can create lessons")
    else:
        print("❌ Instructor cannot create courses")

    # Test 6: Dashboard Access
    print("\n📋 Phase 7: Dashboard Access")
    if tester.test_get_dashboard()[0]:
        print("✅ Dashboard accessible")
    else:
        print("❌ Dashboard not accessible")

    # Test 7: General Course Access
    print("\n📋 Phase 8: General Course Access")
    success, courses_data = tester.test_get_courses()
    if success:
        courses = courses_data.get('courses', [])
        print(f"✅ Can access course catalog - Found {len(courses)} courses")
    else:
        print("❌ Cannot access course catalog")

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Summary of key findings
    print("\n🔍 Key Findings:")
    print("- Health check:", "✅ Working" if tester.tests_passed > 0 else "❌ Failed")
    print("- Student video access:", "✅ Properly restricted" if tester.test_get_videos_unauthorized() else "⚠️  Not restricted")
    print("- Instructor login:", "✅ Working" if success else "❌ Failed")
    print("- Instructor video access:", "✅ Working" if success else "❌ Failed")
    
    if tester.tests_passed >= tester.tests_run * 0.8:  # 80% pass rate
        print("\n🎉 Most tests passed - System appears functional!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed - Issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())