import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Avatar, AvatarFallback } from './components/ui/avatar';
import { Textarea } from './components/ui/textarea';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './components/ui/alert-dialog';
import { 
  BookOpen, 
  GraduationCap, 
  Trophy, 
  Users, 
  Play, 
  Clock, 
  Star,
  ChevronRight,
  Award,
  Target,
  TrendingUp,
  Book,
  User,
  LogOut,
  Plus,
  Upload,
  Video,
  Trash2,
  FileVideo
} from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [courses, setCourses] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseProgress, setCourseProgress] = useState(null);
  const [videos, setVideos] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  // Auth forms state
  const [authMode, setAuthMode] = useState('login');
  const [authData, setAuthData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'student'
  });

  // Video upload state
  const [videoUpload, setVideoUpload] = useState({
    title: '',
    description: '',
    file: null
  });

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (activeTab === 'courses' && user) {
      loadCourses();
    }
    if (activeTab === 'videos' && user && user.role === 'instructor') {
      loadVideos();
    }
  }, [activeTab, user]);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/user/profile`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
        loadDashboard();
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = authMode === 'login' ? 'login' : 'register';
      const response = await axios.post(`${API_BASE_URL}/api/auth/${endpoint}`, authData);
      
      localStorage.setItem('token', response.data.access_token);
      setUser(response.data.user);
      loadDashboard();
    } catch (error) {
      alert(error.response?.data?.detail || 'Une erreur est survenue');
    }
  };

  const loadDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Erreur chargement dashboard:', error);
    }
  };

  const loadCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/courses`);
      setCourses(response.data.courses);
    } catch (error) {
      console.error('Erreur chargement cours:', error);
    }
  };

  const loadCourseDetails = async (courseId) => {
    try {
      const token = localStorage.getItem('token');
      const [courseResponse, progressResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/courses/${courseId}`),
        axios.get(`${API_BASE_URL}/api/progress/${courseId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setSelectedCourse(courseResponse.data);
      setCourseProgress(progressResponse.data);
    } catch (error) {
      console.error('Erreur chargement cours:', error);
    }
  };

  const markLessonComplete = async (lessonId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/api/progress`, 
        { lesson_id: lessonId, completed: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Reload progress
      if (selectedCourse) {
        loadCourseDetails(selectedCourse.course_id);
      }
      loadDashboard();
    } catch (error) {
      console.error('Erreur mise à jour progression:', error);
    }
  };

  const loadVideos = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/api/videos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVideos(response.data.videos);
    } catch (error) {
      console.error('Erreur chargement vidéos:', error);
    }
  };

  const handleVideoUpload = async (e) => {
    e.preventDefault();
    if (!videoUpload.file || !videoUpload.title) {
      alert('Veuillez sélectionner un fichier et saisir un titre');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', videoUpload.file);
    formData.append('title', videoUpload.title);
    if (videoUpload.description) {
      formData.append('description', videoUpload.description);
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/api/upload/video`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });

      alert('Vidéo uploadée avec succès !');
      setVideoUpload({ title: '', description: '', file: null });
      loadVideos();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de l\'upload');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const deleteVideo = async (videoId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_BASE_URL}/api/videos/${videoId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('Vidéo supprimée avec succès');
      loadVideos();
    } catch (error) {
      alert('Erreur lors de la suppression');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setDashboardData(null);
    setSelectedCourse(null);
    setCourseProgress(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-md mx-auto">
            <div className="text-center mb-8">
              <GraduationCap className="h-16 w-16 text-indigo-600 mx-auto mb-4" />
              <h1 className="text-4xl font-bold text-gray-900 mb-2">EduFlow</h1>
              <p className="text-gray-600">Plateforme d'apprentissage moderne</p>
            </div>

            <Card className="backdrop-blur-sm bg-white/90 shadow-xl">
              <CardHeader>
                <CardTitle>{authMode === 'login' ? 'Connexion' : 'Inscription'}</CardTitle>
                <CardDescription>
                  {authMode === 'login' ? 'Connectez-vous à votre compte' : 'Créez votre compte EduFlow'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAuth} className="space-y-4">
                  {authMode === 'register' && (
                    <>
                      <div>
                        <Label htmlFor="full_name">Nom complet</Label>
                        <Input
                          id="full_name"
                          type="text"
                          value={authData.full_name}
                          onChange={(e) => setAuthData({...authData, full_name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="role">Rôle</Label>
                        <select
                          id="role"
                          value={authData.role}
                          onChange={(e) => setAuthData({...authData, role: e.target.value})}
                          className="w-full p-2 border border-gray-300 rounded-md"
                        >
                          <option value="student">Étudiant</option>
                          <option value="instructor">Instructeur</option>
                        </select>
                      </div>
                    </>
                  )}
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={authData.email}
                      onChange={(e) => setAuthData({...authData, email: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Mot de passe</Label>
                    <Input
                      id="password"
                      type="password"
                      value={authData.password}
                      onChange={(e) => setAuthData({...authData, password: e.target.value})}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700">
                    {authMode === 'login' ? 'Se connecter' : "S'inscrire"}
                  </Button>
                </form>
                
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                    className="text-indigo-600 hover:text-indigo-800 text-sm"
                  >
                    {authMode === 'login' ? "Pas de compte ? S'inscrire" : 'Déjà un compte ? Se connecter'}
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <GraduationCap className="h-8 w-8 text-indigo-600" />
              <h1 className="text-2xl font-bold text-gray-900">EduFlow</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Avatar>
                  <AvatarFallback className="bg-indigo-100 text-indigo-600">
                    {user.full_name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
                  <p className="text-xs text-gray-500">Niveau {user.level} • {user.xp} XP</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className={`grid w-full ${user.role === 'instructor' ? 'grid-cols-4' : 'grid-cols-3'} mb-8`}>
            <TabsTrigger value="dashboard">Tableau de bord</TabsTrigger>
            <TabsTrigger value="courses">Cours</TabsTrigger>
            {user.role === 'instructor' && (
              <TabsTrigger value="videos">Mes Vidéos</TabsTrigger>
            )}
            <TabsTrigger value="profile">Profil</TabsTrigger>
          </TabsList>

          {/* Dashboard */}
          <TabsContent value="dashboard" className="space-y-6">
            {dashboardData && (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-blue-100 text-sm">Cours suivis</p>
                          <p className="text-3xl font-bold">{dashboardData.stats.total_courses}</p>
                        </div>
                        <BookOpen className="h-8 w-8 text-blue-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-green-100 text-sm">Cours terminés</p>
                          <p className="text-3xl font-bold">{dashboardData.stats.completed_courses}</p>
                        </div>
                        <Trophy className="h-8 w-8 text-green-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-purple-100 text-sm">Niveau actuel</p>
                          <p className="text-3xl font-bold">{dashboardData.stats.current_level}</p>
                        </div>
                        <Award className="h-8 w-8 text-purple-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-orange-100 text-sm">XP Total</p>
                          <p className="text-3xl font-bold">{dashboardData.stats.total_xp}</p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-orange-200" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Current Courses */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Target className="h-5 w-5" />
                      <span>Mes cours en cours</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {dashboardData.enrolled_courses.length > 0 ? (
                      <div className="space-y-4">
                        {dashboardData.enrolled_courses.map((course) => (
                          <div key={course.course_id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h3 className="font-semibold text-gray-900">{course.title}</h3>
                                <p className="text-sm text-gray-600">{course.instructor_name}</p>
                              </div>
                              <Badge variant="secondary">
                                {course.level}
                              </Badge>
                            </div>
                            <div className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span>Progression</span>
                                <span>{course.completion_percentage}%</span>
                              </div>
                              <Progress value={course.completion_percentage} className="h-2" />
                              <p className="text-xs text-gray-500">
                                {course.completed_lessons} / {course.total_lessons} leçons terminées
                              </p>
                            </div>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="mt-3"
                              onClick={() => {
                                setActiveTab('courses');
                                loadCourseDetails(course.course_id);
                              }}
                            >
                              Continuer <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">Aucun cours commencé</p>
                        <Button 
                          className="mt-4" 
                          onClick={() => {
                            setActiveTab('courses');
                            loadCourses();
                          }}
                        >
                          Découvrir les cours
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Courses */}
          <TabsContent value="courses" className="space-y-6">
            {selectedCourse ? (
              <div className="space-y-6">
                <Button 
                  variant="outline" 
                  onClick={() => setSelectedCourse(null)}
                  className="mb-4"
                >
                  ← Retour aux cours
                </Button>

                <Card>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-2xl">{selectedCourse.title}</CardTitle>
                        <CardDescription className="mt-2">
                          Par {selectedCourse.instructor_name} • {selectedCourse.level}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary">
                        {selectedCourse.category}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 mb-6">{selectedCourse.description}</p>
                    
                    {courseProgress && (
                      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">Votre progression</span>
                          <span className="text-sm font-semibold text-indigo-600">
                            {courseProgress.completion_percentage}%
                          </span>
                        </div>
                        <Progress value={courseProgress.completion_percentage} className="h-3" />
                        <p className="text-sm text-gray-600 mt-2">
                          {courseProgress.completed_lessons} / {courseProgress.total_lessons} leçons terminées
                        </p>
                      </div>
                    )}

                    <div className="space-y-3">
                      <h3 className="font-semibold text-lg">Leçons</h3>
                      {selectedCourse.lessons?.map((lesson, index) => {
                        const lessonProgress = courseProgress?.lessons.find(l => l.lesson_id === lesson.lesson_id);
                        const isCompleted = lessonProgress?.completed || false;
                        
                        return (
                          <div key={lesson.lesson_id} className="p-4 border rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                                  isCompleted 
                                    ? 'bg-green-100 text-green-700' 
                                    : 'bg-gray-100 text-gray-600'
                                }`}>
                                  {index + 1}
                                </div>
                                <div>
                                  <h4 className="font-medium">{lesson.title}</h4>
                                  {lesson.video_url && (
                                    <div className="flex items-center space-x-1 text-sm text-gray-500">
                                      <Play className="h-3 w-3" />
                                      <span>Vidéo</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                {isCompleted && (
                                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                                    Terminé
                                  </Badge>
                                )}
                                {!isCompleted && (
                                  <Button 
                                    size="sm"
                                    onClick={() => markLessonComplete(lesson.lesson_id)}
                                  >
                                    Marquer comme terminé
                                  </Button>
                                )}
                              </div>
                            </div>
                            {lesson.content && (
                              <div className="mt-3 pl-11">
                                <p className="text-sm text-gray-600">{lesson.content}</p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold">Catalogue des cours</h2>
                  <Button onClick={loadCourses}>
                    Actualiser
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {courses.map((course) => (
                    <Card key={course.course_id} className="hover:shadow-lg transition-shadow cursor-pointer">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <Badge variant="outline">{course.category}</Badge>
                          <Badge variant="secondary">{course.level}</Badge>
                        </div>
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CardDescription>Par {course.instructor_name}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                          {course.description}
                        </p>
                        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{course.duration_hours}h</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Book className="h-4 w-4" />
                            <span>{course.lessons_count || 0} leçons</span>
                          </div>
                        </div>
                        <Button 
                          className="w-full" 
                          onClick={() => loadCourseDetails(course.course_id)}
                        >
                          Voir le cours
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {courses.length === 0 && (
                  <div className="text-center py-12">
                    <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">Aucun cours disponible</p>
                    <Button onClick={loadCourses}>Actualiser</Button>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* Videos Management (Instructors Only) */}
          {user.role === 'instructor' && (
            <TabsContent value="videos" className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Gestion des Vidéos</h2>
                <Badge variant="outline">Instructeur</Badge>
              </div>

              {/* Upload Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Upload className="h-5 w-5" />
                    <span>Uploader une vidéo</span>
                  </CardTitle>
                  <CardDescription>
                    Formats supportés: MP4, AVI, MOV, WMV, WebM (Max: 100MB)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleVideoUpload} className="space-y-4">
                    <div>
                      <Label htmlFor="video-title">Titre de la vidéo *</Label>
                      <Input
                        id="video-title"
                        type="text"
                        value={videoUpload.title}
                        onChange={(e) => setVideoUpload({...videoUpload, title: e.target.value})}
                        placeholder="Ex: Introduction au JavaScript"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="video-description">Description</Label>
                      <Textarea
                        id="video-description"
                        value={videoUpload.description}
                        onChange={(e) => setVideoUpload({...videoUpload, description: e.target.value})}
                        placeholder="Description de la vidéo..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <Label htmlFor="video-file">Fichier vidéo *</Label>
                      <Input
                        id="video-file"
                        type="file"
                        accept="video/*"
                        onChange={(e) => setVideoUpload({...videoUpload, file: e.target.files[0]})}
                        required
                      />
                      {videoUpload.file && (
                        <p className="text-sm text-gray-600 mt-1">
                          Fichier sélectionné: {videoUpload.file.name} ({formatFileSize(videoUpload.file.size)})
                        </p>
                      )}
                    </div>

                    {isUploading && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Upload en cours...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="h-2" />
                      </div>
                    )}

                    <Button 
                      type="submit" 
                      disabled={isUploading}
                      className="bg-indigo-600 hover:bg-indigo-700"
                    >
                      {isUploading ? 'Upload en cours...' : 'Uploader la vidéo'}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Videos List */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Video className="h-5 w-5" />
                    <span>Mes vidéos ({videos.length})</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {videos.length > 0 ? (
                    <div className="space-y-4">
                      {videos.map((video) => (
                        <div key={video.video_id} className="p-4 border rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <FileVideo className="h-5 w-5 text-indigo-600" />
                                <h3 className="font-semibold">{video.title}</h3>
                              </div>
                              {video.description && (
                                <p className="text-sm text-gray-600 mb-2">{video.description}</p>
                              )}
                              <div className="flex items-center space-x-4 text-xs text-gray-500">
                                <span>Taille: {formatFileSize(video.file_size || 0)}</span>
                                <span>Uploadé le: {new Date(video.uploaded_at).toLocaleDateString('fr-FR')}</span>
                                <span>Format: {video.content_type}</span>
                              </div>
                              <div className="mt-2">
                                <p className="text-xs text-gray-400 font-mono break-all">
                                  URL: {API_BASE_URL}{video.file_path}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2 ml-4">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  navigator.clipboard.writeText(`${API_BASE_URL}${video.file_path}`);
                                  alert('URL copiée dans le presse-papiers !');
                                }}
                              >
                                Copier URL
                              </Button>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button variant="destructive" size="sm">
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Supprimer la vidéo</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Êtes-vous sûr de vouloir supprimer "{video.title}" ? Cette action est irréversible.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Annuler</AlertDialogCancel>
                                    <AlertDialogAction onClick={() => deleteVideo(video.video_id)}>
                                      Supprimer
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          </div>
                          
                          {/* Video Preview */}
                          <div className="mt-4">
                            <video 
                              controls 
                              className="w-full max-w-md h-48 bg-gray-100 rounded"
                              src={`${API_BASE_URL}${video.file_path}`}
                            >
                              Votre navigateur ne supporte pas la lecture vidéo.
                            </video>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Video className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">Aucune vidéo uploadée</p>
                      <p className="text-sm text-gray-500">Uploadez votre première vidéo pour commencer</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Profile */}
          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <User className="h-5 w-5" />
                  <span>Mon profil</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center space-x-4">
                  <Avatar className="h-20 w-20">
                    <AvatarFallback className="bg-indigo-100 text-indigo-600 text-2xl">
                      {user.full_name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="text-xl font-semibold">{user.full_name}</h3>
                    <p className="text-gray-600">{user.email}</p>
                    <Badge variant="outline" className="mt-2">
                      {user.role === 'student' ? 'Étudiant' : 'Instructeur'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-indigo-50 rounded-lg text-center">
                    <Award className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-indigo-700">{user.level}</p>
                    <p className="text-sm text-indigo-600">Niveau actuel</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg text-center">
                    <Star className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-purple-700">{user.xp}</p>
                    <p className="text-sm text-purple-600">Points XP</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <Trophy className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-green-700">{user.badges?.length || 0}</p>
                    <p className="text-sm text-green-600">Badges obtenus</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Progression vers le niveau suivant</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Niveau {user.level}</span>
                      <span>Niveau {user.level + 1}</span>
                    </div>
                    <Progress value={(user.xp % 100)} className="h-3" />
                    <p className="text-xs text-gray-500">
                      {user.xp % 100} / 100 XP pour le niveau suivant
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;