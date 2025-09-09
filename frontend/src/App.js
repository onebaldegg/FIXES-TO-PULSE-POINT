import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Loader2, TrendingUp, TrendingDown, Minus, BarChart3, Brain, Zap, Smile, Frown, Meh, Heart, Shield, X, Sparkles, Clock, AlertTriangle, Tag, Users, DollarSign, Truck, Monitor, Bug, Megaphone, FileText, GitCompare, Lightbulb, Lock, Zap as Performance, Upload, Download, FileUp, CheckCircle, XCircle, AlertCircle, User, Settings, LogOut, Eye, EyeOff, Mail, Key } from "lucide-react";
import { Toaster } from "./components/ui/toaster";
import { useToast } from "./hooks/use-toast";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'));
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Set up axios interceptor for authentication
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Load user data on app start
  useEffect(() => {
    if (token) {
      loadUserData();
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadUserData = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Error loading user data:', error);
      // Token might be expired, try to refresh
      if (refreshToken) {
        await tryRefreshToken();
      } else {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const tryRefreshToken = async () => {
    try {
      const response = await axios.post(`${API}/auth/refresh`, {
        refresh_token: refreshToken
      });
      
      const newToken = response.data.access_token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      // Try loading user data again
      await loadUserData();
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
    }
  };

  const login = async (email, password) => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post(`${API}/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, refresh_token } = response.data;
      
      setToken(access_token);
      setRefreshToken(refresh_token);
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Load user data
      await loadUserData();
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (email, password, fullName) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        password,
        full_name: fullName
      });

      return { 
        success: true, 
        message: response.data.message 
      };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    loadUserData
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// User Dashboard Component (moved outside to prevent recreation on each render)
const UserDashboard = ({ showDashboard, setShowDashboard, user, toast }) => {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (showDashboard && user) {
      loadDashboardStats();
    }
  }, [showDashboard, user]);

  const loadDashboardStats = async () => {
    setLoading(true);
    try {
      // Load user's recent activity
      const historyResponse = await axios.get(`${API}/sentiment-history?limit=50`);
      const recentHistory = historyResponse.data;

      // Calculate dashboard statistics
      const stats = calculateDashboardStats(recentHistory);
      setDashboardStats(stats);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
      toast({
        title: "Error",
        description: "Failed to load dashboard statistics",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const calculateDashboardStats = (history) => {
    const now = new Date();
    const lastWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const lastMonth = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Filter analyses by time period
    const weeklyAnalyses = history.filter(item => new Date(item.timestamp) >= lastWeek);
    const monthlyAnalyses = history.filter(item => new Date(item.timestamp) >= lastMonth);

    // Sentiment distribution
    const sentimentCounts = history.reduce((acc, item) => {
      acc[item.sentiment] = (acc[item.sentiment] || 0) + 1;
      return acc;
    }, {});

    // Most frequent emotions
    const emotionCounts = {};
    history.forEach(item => {
      if (item.emotions) {
        Object.entries(item.emotions).forEach(([emotion, confidence]) => {
          if (confidence > 0.5) {
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
          }
        });
      }
    });

    // Most frequent topics
    const topicCounts = {};
    history.forEach(item => {
      if (item.primary_topic) {
        topicCounts[item.primary_topic] = (topicCounts[item.primary_topic] || 0) + 1;
      }
    });

    // Usage trends
    const dailyUsage = {};
    weeklyAnalyses.forEach(item => {
      const date = new Date(item.timestamp).toDateString();
      dailyUsage[date] = (dailyUsage[date] || 0) + 1;
    });

    return {
      totalAnalyses: history.length,
      weeklyAnalyses: weeklyAnalyses.length,
      monthlyAnalyses: monthlyAnalyses.length,
      sentimentCounts,
      emotionCounts,
      topicCounts,
      dailyUsage,
      averageConfidence: history.length > 0 
        ? (history.reduce((sum, item) => sum + item.confidence, 0) / history.length).toFixed(2)
        : 0
    };
  };

  const getUsageLimits = () => {
    const tier = user?.subscription_tier || 'free';
    const limits = {
      free: { analyses: 50, files: 5, urls: 10 },
      pro: { analyses: 10000, files: 1000, urls: 5000 }
    };
    return limits[tier];
  };

  const getColorsForSentiment = (sentiment) => {
    const colors = {
      positive: 'from-green-600 to-emerald-600',
      negative: 'from-red-600 to-pink-600',
      neutral: 'from-gray-600 to-slate-600'
    };
    return colors[sentiment] || colors.neutral;
  };

  // Helper functions from original component
  const getEmotionIcon = (emotion) => {
    switch (emotion) {
      case "joy":
        return <Smile className="h-3 w-3" />;
      case "sadness":
        return <Frown className="h-3 w-3" />;
      case "anger":
        return <X className="h-3 w-3" />;
      case "fear":
        return <Meh className="h-3 w-3" />;
      case "trust":
        return <Shield className="h-3 w-3" />;
      case "disgust":
        return <X className="h-3 w-3" />;
      case "surprise":
        return <Sparkles className="h-3 w-3" />;
      case "anticipation":
        return <Clock className="h-3 w-3" />;
      default:
        return <Heart className="h-3 w-3" />;
    }
  };

  const formatEmotionName = (emotion) => {
    return emotion.charAt(0).toUpperCase() + emotion.slice(1);
  };

  if (!showDashboard) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl h-full max-h-[90vh] bg-black/90 backdrop-blur-lg border border-green-500/20 rounded-xl overflow-hidden">
        {/* Dashboard Header */}
        <div className="flex items-center justify-between p-6 border-b border-green-500/20">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{background: '#42DF50'}}>
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold" style={{color: '#42DF50'}}>User Dashboard</h2>
              <p style={{color: '#42DF50'}}>Analytics and Account Overview</p>
            </div>
          </div>
          <button
            onClick={() => setShowDashboard(false)}
            className="p-2 hover:bg-green-500/20 rounded-lg transition-colors"
          >
            <X className="h-6 w-6" style={{color: '#42DF50'}} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin" style={{color: '#42DF50'}} />
              <span className="ml-2" style={{color: '#42DF50'}}>Loading dashboard...</span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* User Info Card */}
              <Card className="bg-black/60 border-green-500/20">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{background: '#42DF50'}}>
                        <User className="h-8 w-8 text-white" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold" style={{color: '#42DF50'}}>{user.full_name}</h3>
                        <p style={{color: '#42DF50'}}>{user.email}</p>
                        <div className="flex items-center space-x-2 mt-2">
                          <Badge variant={user.subscription_tier === 'pro' ? 'default' : 'secondary'}>
                            {user.subscription_tier.toUpperCase()} PLAN
                          </Badge>
                          <span className="text-xs" style={{color: '#42DF50'}}>
                            {user.is_verified ? "✅ Verified" : "⚠️ Email verification required"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm" style={{color: '#42DF50'}}>Member since</p>
                      <p style={{color: '#42DF50'}}>{new Date(user.created_at).toLocaleDateString()}</p>
                      {user.last_login && (
                        <>
                          <p className="text-sm mt-2" style={{color: '#42DF50'}}>Last login</p>
                          <p style={{color: '#42DF50'}}>{new Date(user.last_login).toLocaleDateString()}</p>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Usage Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {(() => {
                  const limits = getUsageLimits();
                  const usage = user.usage_stats || {};
                  
                  return [
                    { 
                      label: 'Text Analyses', 
                      current: usage.analyses_this_month || 0, 
                      limit: limits.analyses,
                      icon: FileText,
                      color: 'from-blue-600 to-cyan-600'
                    },
                    { 
                      label: 'Files Uploaded', 
                      current: usage.files_uploaded || 0, 
                      limit: limits.files,
                      icon: Upload,
                      color: 'from-[#42DF50] to-[#42DF50]'
                    },
                    { 
                      label: 'URLs Analyzed', 
                      current: usage.urls_analyzed || 0, 
                      limit: limits.urls,
                      icon: Monitor,
                      color: 'from-cyan-600 to-blue-600'
                    }
                  ].map((stat, index) => (
                    <Card key={index} className="bg-black/60 border-green-500/20">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="w-12 h-12 rounded-xl flex items-center justify-center" 
                               style={{
                                 background: stat.label === 'Files Uploaded' ? '#42DF50' : 
                                            stat.label === 'Text Analyses' ? '#3B82F6' : 
                                            '#06B6D4'
                               }}>
                            <stat.icon className="h-6 w-6 text-white" />
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold" style={{color: '#42DF50'}}>{stat.current}</p>
                            <p className="text-sm" style={{color: '#42DF50'}}>of {stat.limit}</p>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span style={{color: '#42DF50'}}>{stat.label}</span>
                            <span style={{color: '#42DF50'}}>{Math.round((stat.current / stat.limit) * 100)}%</span>
                          </div>
                          <div className="w-full bg-green-800/30 rounded-full h-2">
                            <div 
                              className="h-2 rounded-full transition-all duration-300"
                              style={{ 
                                width: `${Math.min((stat.current / stat.limit) * 100, 100)}%`,
                                background: stat.label === 'Files Uploaded' ? '#42DF50' : 
                                           stat.label === 'Text Analyses' ? '#3B82F6' : 
                                           '#06B6D4'
                              }}
                            />
                          </div>
                          {stat.current / stat.limit > 0.8 && (
                            <p className="text-xs text-orange-400">⚠️ Approaching limit</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ));
                })()}
              </div>

              {/* Analytics Overview */}
              {dashboardStats && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Sentiment Distribution */}
                  <Card className="bg-black/60 border-green-500/20">
                    <CardHeader>
                      <CardTitle style={{color: '#42DF50'}} className="flex items-center space-x-2">
                        <TrendingUp className="h-5 w-5" />
                        <span>Sentiment Distribution</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {Object.entries(dashboardStats.sentimentCounts).map(([sentiment, count]) => (
                          <div key={sentiment} className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span style={{color: '#42DF50'}} className="capitalize">{sentiment}</span>
                              <span style={{color: '#42DF50'}}>{count} analyses</span>
                            </div>
                            <div className="w-full bg-green-800/30 rounded-full h-2">
                              <div 
                                className={`h-2 bg-gradient-to-r ${getColorsForSentiment(sentiment)} rounded-full`}
                                style={{ width: `${(count / dashboardStats.totalAnalyses) * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Activity Summary */}
                  <Card className="bg-black/60 border-green-500/20">
                    <CardHeader>
                      <CardTitle style={{color: '#42DF50'}} className="flex items-center space-x-2">
                        <Clock className="h-5 w-5" />
                        <span>Activity Summary</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-green-950/30 rounded-lg">
                          <span style={{color: '#42DF50'}}>Total Analyses</span>
                          <span style={{color: '#42DF50'}} className="font-bold">{dashboardStats.totalAnalyses}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-green-950/30 rounded-lg">
                          <span style={{color: '#42DF50'}}>This Week</span>
                          <span style={{color: '#42DF50'}} className="font-bold">{dashboardStats.weeklyAnalyses}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-green-950/30 rounded-lg">
                          <span style={{color: '#42DF50'}}>This Month</span>
                          <span style={{color: '#42DF50'}} className="font-bold">{dashboardStats.monthlyAnalyses}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-green-950/30 rounded-lg">
                          <span style={{color: '#42DF50'}}>Avg. Confidence</span>
                          <span style={{color: '#42DF50'}} className="font-bold">{dashboardStats.averageConfidence}%</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Top Topics */}
                  {Object.keys(dashboardStats.topicCounts).length > 0 && (
                    <Card className="bg-black/60 border-green-500/20">
                      <CardHeader>
                        <CardTitle style={{color: '#42DF50'}} className="flex items-center space-x-2">
                          <Tag className="h-5 w-5" />
                          <span>Most Analyzed Topics</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {Object.entries(dashboardStats.topicCounts)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 5)
                            .map(([topic, count]) => (
                              <div key={topic} className="flex items-center justify-between p-2 bg-green-950/30 rounded">
                                <span style={{color: '#42DF50'}} className="text-sm capitalize">{topic.replace('_', ' ')}</span>
                                <span style={{color: '#42DF50'}} className="text-sm font-medium">{count}</span>
                              </div>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Top Emotions */}
                  {Object.keys(dashboardStats.emotionCounts).length > 0 && (
                    <Card className="bg-black/60 border-green-500/20">
                      <CardHeader>
                        <CardTitle style={{color: '#42DF50'}} className="flex items-center space-x-2">
                          <Heart className="h-5 w-5" />
                          <span>Most Detected Emotions</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {Object.entries(dashboardStats.emotionCounts)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 5)
                            .map(([emotion, count]) => (
                              <div key={emotion} className="flex items-center justify-between p-2 bg-green-950/30 rounded">
                                <div className="flex items-center space-x-2">
                                  {getEmotionIcon(emotion)}
                                  <span style={{color: '#42DF50'}} className="text-sm capitalize">{formatEmotionName(emotion)}</span>
                                </div>
                                <span style={{color: '#42DF50'}} className="text-sm font-medium">{count}</span>
                              </div>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { user, loading: authLoading, isAuthenticated, logout } = useAuth();
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const { toast } = useToast();
  
  // Authentication UI states
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" or "register"
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  // Show auth modal if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      setShowAuthModal(true);
    } else {
      setShowAuthModal(false);
    }
  }, [authLoading, isAuthenticated]);

  // Load user-specific data when user logs in
  useEffect(() => {
    console.log("useEffect [isAuthenticated, user] triggered:", { isAuthenticated, user: user?.email, authLoading });
    if (isAuthenticated && user) {
      console.log("Calling fetchHistory from useEffect");
      fetchHistory(); // Reload history for the authenticated user
    }
  }, [isAuthenticated, user]);

  // Authentication Modal Component
  const AuthModal = () => {
    const { login, register } = useAuth();
    const [formData, setFormData] = useState({
      email: "",
      password: "",
      fullName: "",
      confirmPassword: ""
    });
    const [formLoading, setFormLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({});

    const handleInputChange = (e) => {
      const { name, value } = e.target;
      setFormData(prev => ({ ...prev, [name]: value }));
      // Clear error when user starts typing
      if (errors[name]) {
        setErrors(prev => ({ ...prev, [name]: "" }));
      }
    };

    const validateForm = () => {
      const newErrors = {};
      
      if (!formData.email) {
        newErrors.email = "Email is required";
      } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
        newErrors.email = "Email is invalid";
      }
      
      if (!formData.password) {
        newErrors.password = "Password is required";
      } else if (formData.password.length < 8) {
        newErrors.password = "Password must be at least 8 characters";
      }
      
      if (authMode === "register") {
        if (!formData.fullName) {
          newErrors.fullName = "Full name is required";
        }
        if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = "Passwords do not match";
        }
      }
      
      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!validateForm()) return;
      
      setFormLoading(true);
      
      try {
        if (authMode === "login") {
          const result = await login(formData.email, formData.password);
          if (result.success) {
            toast({
              title: "Welcome back!",
              description: "You have been logged in successfully.",
            });
            setShowAuthModal(false);
          } else {
            toast({
              title: "Login Failed",
              description: result.error,
              variant: "destructive"
            });
          }
        } else {
          const result = await register(formData.email, formData.password, formData.fullName);
          if (result.success) {
            toast({
              title: "Registration Successful",
              description: result.message,
            });
            setAuthMode("login");
            setFormData({ email: formData.email, password: "", fullName: "", confirmPassword: "" });
          } else {
            toast({
              title: "Registration Failed",
              description: result.error,
              variant: "destructive"
            });
          }
        }
      } catch (error) {
        toast({
          title: "Error",
          description: "An unexpected error occurred. Please try again.",
          variant: "destructive"
        });
      } finally {
        setFormLoading(false);
      }
    };

    if (!showAuthModal) return null;

    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-2xl border-0 bg-black/80 backdrop-blur-lg border border-green-500/20">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto flex flex-col items-center">
              <img src="/pulse-point-icon.png" alt="Pulse Point Icon" className="h-16 w-16" />
              <CardTitle className="text-3xl font-bold mt-2" style={{color: '#42DF50'}}>
                PULSE POINT
              </CardTitle>
            </div>
            <CardDescription className="mt-4" style={{color: '#42DF50'}}>
              {authMode === "login" ? "Sign in to your account" : "Create your account"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {authMode === "register" && (
                <div className="space-y-2">
                  <label className="text-sm font-medium" style={{color: '#42DF50'}}>Full Name</label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-black/40 border rounded-lg placeholder:text-green-300/60 focus:outline-none"
                    style={{
                      color: '#42DF50',
                      borderColor: errors.fullName ? '#ef4444' : '#42DF50'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#42DF50';
                      e.target.style.boxShadow = '0 0 0 1px rgba(66, 223, 80, 0.5)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = errors.fullName ? '#ef4444' : '#42DF50';
                      e.target.style.boxShadow = 'none';
                    }}
                    placeholder="Enter your full name"
                  />
                  {errors.fullName && <p className="text-xs text-red-400">{errors.fullName}</p>}
                </div>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium" style={{color: '#42DF50'}}>Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-black/40 border rounded-lg placeholder:text-green-300/60 focus:outline-none"
                  style={{
                    color: '#42DF50',
                    borderColor: errors.email ? '#ef4444' : '#42DF50'
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#42DF50';
                    e.target.style.boxShadow = '0 0 0 1px rgba(66, 223, 80, 0.5)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = errors.email ? '#ef4444' : '#42DF50';
                    e.target.style.boxShadow = 'none';
                  }}
                  placeholder="Enter your email"
                />
                {errors.email && <p className="text-xs text-red-400">{errors.email}</p>}
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium" style={{color: '#42DF50'}}>Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 pr-10 bg-black/40 border rounded-lg placeholder:text-green-300/60 focus:outline-none"
                    style={{
                      color: '#42DF50',
                      borderColor: errors.password ? '#ef4444' : '#42DF50'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#42DF50';
                      e.target.style.boxShadow = '0 0 0 1px rgba(66, 223, 80, 0.5)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = errors.password ? '#ef4444' : '#42DF50';
                      e.target.style.boxShadow = 'none';
                    }}
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 hover:opacity-80"
                    style={{color: '#42DF50'}}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-red-400">{errors.password}</p>}
              </div>
              
              {authMode === "register" && (
                <div className="space-y-2">
                  <label className="text-sm font-medium" style={{color: '#42DF50'}}>Confirm Password</label>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-black/40 border rounded-lg placeholder:text-green-300/60 focus:outline-none"
                    style={{
                      color: '#42DF50',
                      borderColor: errors.confirmPassword ? '#ef4444' : '#42DF50'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#42DF50';
                      e.target.style.boxShadow = '0 0 0 1px rgba(66, 223, 80, 0.5)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = errors.confirmPassword ? '#ef4444' : '#42DF50';
                      e.target.style.boxShadow = 'none';
                    }}
                    placeholder="Confirm your password"
                  />
                  {errors.confirmPassword && <p className="text-xs text-red-400">{errors.confirmPassword}</p>}
                </div>
              )}
              
              <Button
                type="submit"
                disabled={formLoading}
                className="w-full text-white font-medium py-3 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl border"
                style={{
                  background: '#42DF50',
                  borderColor: '#42DF50'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#3BC642';
                  e.target.style.borderColor = '#3BC642';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = '#42DF50';
                  e.target.style.borderColor = '#42DF50';
                }}
              >
                {formLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {authMode === "login" ? "Signing In..." : "Creating Account..."}
                  </>
                ) : (
                  <>
                    {authMode === "login" ? (
                      <>
                        <Key className="mr-2 h-4 w-4" />
                        Sign In
                      </>
                    ) : (
                      <>
                        <User className="mr-2 h-4 w-4" />
                        Create Account
                      </>
                    )}
                  </>
                )}
              </Button>
            </form>
            
            <div className="mt-4 text-center">
              <p className="text-center mt-6" style={{color: '#42DF50'}}>
                {authMode === "login" ? (
                  <>
                    Don't have an account?{" "}
                    <button
                      onClick={() => setAuthMode("register")}
                      className="font-medium hover:underline"
                      style={{color: '#42DF50'}}
                    >
                      Sign up
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{" "}
                    <button
                      onClick={() => setAuthMode("login")}
                      className="font-medium hover:underline"
                      style={{color: '#42DF50'}}
                    >
                      Sign in
                    </button>
                  </>
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // File upload states
  const [activeTab, setActiveTab] = useState("text"); // "text" or "file" or "url"
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  // URL analysis states  
  const [url, setUrl] = useState("");
  const [urls, setUrls] = useState("");
  const [urlLoading, setUrlLoading] = useState(false);
  const [batchUrlLoading, setBatchUrlLoading] = useState(false);
  const [urlResults, setUrlResults] = useState(null);
  const [batchUrlResults, setBatchUrlResults] = useState(null);

  // Dashboard state
  const [showDashboard, setShowDashboard] = useState(false);

  const fetchHistory = async () => {
    console.log("fetchHistory called - Auth state:", { isAuthenticated, user: user?.email, authLoading });
    
    // Only fetch history if user is authenticated
    if (!isAuthenticated || !user || authLoading) {
      console.log("Skipping history fetch - user not authenticated or still loading");
      return;
    }
    
    console.log("Proceeding with history fetch for authenticated user");
    
    try {
      const response = await axios.get(`${API}/sentiment-history`);
      setHistory(response.data);
      console.log("History fetched successfully:", response.data.length, "items");
    } catch (error) {
      console.error("Error fetching history:", error);
      // Only show toast for non-authentication errors
      if (error.response?.status !== 401) {
        toast({
          title: "Error",
          description: "Failed to load analysis history",
          variant: "destructive"
        });
      }
    }
  };

  const analyzeSentiment = async () => {
    if (!text.trim()) {
      toast({
        title: "Error",
        description: "Please enter some text to analyze",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-sentiment`, {
        text: text.trim()
      });
      
      setAnalysis(response.data);
      setText("");
      fetchHistory();
      
      toast({
        title: "Analysis Complete",
        description: `Sentiment detected: ${response.data.sentiment}`,
      });
    } catch (error) {
      console.error("Error analyzing sentiment:", error);
      toast({
        title: "Error",
        description: "Failed to analyze sentiment. Please try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // File upload functions
  const handleFileUpload = async (file) => {
    if (!file) return;

    // Validate file type
    const allowedTypes = ['text/plain', 'text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/pdf'];
    const allowedExtensions = ['txt', 'csv', 'xls', 'xlsx', 'pdf'];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      toast({
        title: "Invalid File Type",
        description: "Please upload TXT, CSV, Excel, or PDF files only.",
        variant: "destructive"
      });
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "File Too Large",
        description: "Please upload files smaller than 5MB.",
        variant: "destructive"
      });
      return;
    }

    setUploadLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadedFile(response.data);
      toast({
        title: "File Uploaded Successfully",
        description: `Extracted ${response.data.total_entries} text entries from ${response.data.filename}`,
      });
    } catch (error) {
      console.error("Error uploading file:", error);
      toast({
        title: "Upload Failed",
        description: error.response?.data?.detail || "Failed to upload file. Please try again.",
        variant: "destructive"
      });
    } finally {
      setUploadLoading(false);
    }
  };

  const handleBatchAnalysis = async () => {
    if (!uploadedFile) {
      toast({
        title: "No File",
        description: "Please upload a file first.",
        variant: "destructive"
      });
      return;
    }

    setBatchLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-batch`, {
        file_id: uploadedFile.file_id,
        texts: uploadedFile.extracted_texts
      });

      setBatchResults(response.data);
      toast({
        title: "Batch Analysis Complete",
        description: `Analyzed ${response.data.total_processed} text entries successfully`,
      });
    } catch (error) {
      console.error("Error in batch analysis:", error);
      toast({
        title: "Analysis Failed",
        description: error.response?.data?.detail || "Failed to analyze batch. Please try again.",
        variant: "destructive"
      });
    } finally {
      setBatchLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  // URL analysis functions
  const analyzeUrl = async () => {
    if (!url.trim()) {
      toast({
        title: "Error",
        description: "Please enter a URL to analyze",
        variant: "destructive"
      });
      return;
    }

    setUrlLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-url`, {
        url: url.trim(),
        extract_full_content: true,
        include_metadata: true
      });
      
      setUrlResults(response.data);
      setUrl("");
      
      toast({
        title: "URL Analysis Complete",
        description: `Analyzed ${response.data.text_length} characters from ${response.data.title || 'webpage'}`,
      });
    } catch (error) {
      console.error("Error analyzing URL:", error);
      toast({
        title: "Analysis Failed",
        description: error.response?.data?.detail || "Failed to analyze URL. Please check the URL and try again.",
        variant: "destructive"
      });
    } finally {
      setUrlLoading(false);
    }
  };

  const analyzeBatchUrls = async () => {
    if (!urls.trim()) {
      toast({
        title: "Error",
        description: "Please enter URLs to analyze",
        variant: "destructive"
      });
      return;
    }

    // Parse URLs from textarea (one per line)
    const urlList = urls.trim().split('\n').map(u => u.trim()).filter(u => u);
    
    if (urlList.length === 0) {
      toast({
        title: "Error", 
        description: "Please enter valid URLs",
        variant: "destructive"
      });
      return;
    }

    if (urlList.length > 20) {
      toast({
        title: "Too Many URLs",
        description: "Maximum 20 URLs allowed per batch",
        variant: "destructive"
      });
      return;
    }

    setBatchUrlLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-batch-urls`, {
        urls: urlList,
        extract_full_content: true,
        include_metadata: true
      });
      
      setBatchUrlResults(response.data);
      setUrls("");
      
      toast({
        title: "Batch URL Analysis Complete",
        description: `Analyzed ${response.data.total_processed}/${response.data.total_requested} URLs successfully`,
      });
    } catch (error) {
      console.error("Error analyzing batch URLs:", error);
      toast({
        title: "Batch Analysis Failed",
        description: error.response?.data?.detail || "Failed to analyze URLs. Please check your URLs and try again.",
        variant: "destructive"
      });
    } finally {
      setBatchUrlLoading(false);
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp className="h-4 w-4" />;
      case "negative":
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case "positive":
        return "bg-emerald-500";
      case "negative":
        return "bg-rose-500";
      default:
        return "bg-slate-500";
    }
  };

  const getSentimentBadgeVariant = (sentiment) => {
    switch (sentiment) {
      case "positive":
        return "default";
      case "negative":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const getEmotionIcon = (emotion) => {
    switch (emotion) {
      case "joy":
        return <Smile className="h-3 w-3" />;
      case "sadness":
        return <Frown className="h-3 w-3" />;
      case "anger":
        return <X className="h-3 w-3" />;
      case "fear":
        return <Meh className="h-3 w-3" />;
      case "trust":
        return <Shield className="h-3 w-3" />;
      case "disgust":
        return <X className="h-3 w-3" />;
      case "surprise":
        return <Sparkles className="h-3 w-3" />;
      case "anticipation":
        return <Clock className="h-3 w-3" />;
      default:
        return <Heart className="h-3 w-3" />;
    }
  };

  const getEmotionColor = (emotion) => {
    switch (emotion) {
      case "joy":
        return "bg-yellow-500 text-white";
      case "sadness":
        return "bg-blue-500 text-white";
      case "anger":
        return "bg-red-500 text-white";
      case "fear":
        return "bg-purple-500 text-white";
      case "trust":
        return "bg-green-500 text-white";
      case "disgust":
        return "bg-gray-500 text-white";
      case "surprise":
        return "bg-orange-500 text-white";
      case "anticipation":
        return "bg-teal-500 text-white";
      default:
        return "bg-slate-500 text-white";
    }
  };

  const formatEmotionName = (emotion) => {
    return emotion.charAt(0).toUpperCase() + emotion.slice(1);
  };

  const getSarcasmBadgeColor = () => {
    return "bg-orange-500 text-white";
  };

  const getTopicIcon = (topic) => {
    switch (topic) {
      case "customer_service":
        return <Users className="h-3 w-3" />;
      case "product_quality":
        return <Tag className="h-3 w-3" />;
      case "pricing":
        return <DollarSign className="h-3 w-3" />;
      case "delivery_shipping":
        return <Truck className="h-3 w-3" />;
      case "user_experience":
        return <Monitor className="h-3 w-3" />;
      case "technical_issues":
        return <Bug className="h-3 w-3" />;
      case "marketing_advertising":
        return <Megaphone className="h-3 w-3" />;
      case "company_policies":
        return <FileText className="h-3 w-3" />;
      case "competitor_comparison":
        return <GitCompare className="h-3 w-3" />;
      case "feature_requests":
        return <Lightbulb className="h-3 w-3" />;
      case "security_privacy":
        return <Lock className="h-3 w-3" />;
      case "performance_speed":
        return <Performance className="h-3 w-3" />;
      default:
        return <Tag className="h-3 w-3" />;
    }
  };

  const getTopicColor = (topic) => {
    switch (topic) {
      case "customer_service":
        return "bg-blue-500 text-white";
      case "product_quality":
        return "bg-purple-500 text-white";
      case "pricing":
        return "bg-emerald-500 text-white";
      case "delivery_shipping":
        return "bg-orange-500 text-white";
      case "user_experience":
        return "bg-indigo-500 text-white";
      case "technical_issues":
        return "bg-red-500 text-white";
      case "marketing_advertising":
        return "bg-pink-500 text-white";
      case "company_policies":
        return "bg-slate-500 text-white";
      case "competitor_comparison":
        return "bg-yellow-600 text-white";
      case "feature_requests":
        return "bg-cyan-500 text-white";
      case "security_privacy":
        return "bg-rose-500 text-white";
      case "performance_speed":
        return "bg-teal-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Matrix Video Background */}
      <video 
        autoPlay 
        muted 
        loop 
        playsInline
        className="fixed inset-0 w-full h-full object-cover z-0"
        style={{ filter: 'brightness(0.3) opacity(0.8)' }}
      >
        <source 
          src="https://customer-assets.emergentagent.com/job_prinsight/artifacts/qlgtor1l_medium-vecteezy_looping-matrix-style-cyrillic-alphabet-code-rain-effect_6102172_medium%20%281%29.mp4" 
          type="video/mp4" 
        />
      </video>

      {/* Dark Overlay for Better Readability */}
      <div className="fixed inset-0 bg-black/40 z-10"></div>

      {/* Content Container */}
      <div className="relative z-20">
        <AuthModal />
        <UserDashboard 
          showDashboard={showDashboard} 
          setShowDashboard={setShowDashboard} 
          user={user}
          toast={toast}
        />
        
        {/* Header */}
        <header className="bg-black/90 backdrop-blur-lg border-b border-green-500/20 shadow-2xl">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 rounded-xl">
                  <img src="/pulse-point-icon.png" alt="Pulse Point Icon" className="h-14 w-14" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold" style={{color: '#42DF50'}}>PULSE POINT</h1>
                  <p className="text-green-300" style={{color: '#42DF50'}}>Advanced Sentiment Analysis Platform</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                {user && (
                  <div className="flex items-center space-x-4">
                    {/* Usage Statistics */}
                    <div className="bg-green-950/50 px-4 py-2 rounded-lg border" style={{borderColor: '#42DF50'}}>
                      <div className="flex items-center space-x-2">
                        <Badge 
                          variant={user.subscription_tier === 'pro' ? 'default' : 'secondary'} 
                          className={`text-xs ${user.subscription_tier === 'pro' ? 'bg-gradient-to-r from-yellow-600 to-orange-600' : 'bg-green-600'}`}
                        >
                          {user.subscription_tier.toUpperCase()}
                        </Badge>
                        <span className="text-sm" style={{color: '#42DF50'}}>
                          {user.usage_stats?.analyses_this_month || 0} analyses
                        </span>
                      </div>
                    </div>
                    
                    {/* Header Buttons */}
                    <div className="flex items-center space-x-3">
                      {/* Dashboard Button */}
                      <button
                        onClick={(e) => {
                          console.log("Dashboard button clicked!");
                          e.preventDefault();
                          e.stopPropagation();
                          setShowDashboard(true);
                        }}
                        className="flex items-center space-x-2 bg-black/40 px-3 py-2 rounded-lg border hover:border-[#42DF50]/50 transition-colors hover:text-[#42DF50]"
                        style={{borderColor: '#42DF50', color: '#42DF50'}}>
                        <BarChart3 className="h-4 w-4" />
                        <span className="text-sm">Dashboard</span>
                      </button>

                      {/* User Menu */}
                      <div className="relative">
                      <button
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center space-x-2 bg-black/40 px-3 py-2 rounded-lg border transition-colors"
                        style={{borderColor: '#42DF50'}}
                        onMouseEnter={(e) => e.target.style.borderColor = '#42DF50'}
                        onMouseLeave={(e) => e.target.style.borderColor = '#42DF50'}
                      >
                        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{background: '#42DF50'}}>
                          <User className="h-4 w-4 text-white" />
                        </div>
                        <span className="text-sm" style={{color: '#42DF50'}}>{user.full_name}</span>
                        <span style={{color: '#42DF50'}}>▼</span>
                      </button>
                      
                      {showUserMenu && (
                        <div className="absolute right-0 mt-2 w-64 bg-black/90 backdrop-blur-lg border border-green-500/20 rounded-lg shadow-2xl z-[9999]">
                          <div className="p-4 border-b border-green-500/20">
                            <p style={{color: '#42DF50'}} className="font-medium">{user.full_name}</p>
                            <p className="text-sm" style={{color: '#42DF50'}}>{user.email}</p>
                            <div className="flex items-center space-x-2 mt-2">
                              <Badge variant={user.subscription_tier === 'pro' ? 'default' : 'secondary'}>
                                {user.subscription_tier.toUpperCase()}
                              </Badge>
                              <span className="text-xs" style={{color: '#42DF50'}}>
                                {user.is_verified ? "✅ Verified" : "⚠️ Unverified"}
                              </span>
                            </div>
                          </div>
                          <div className="p-2">
                            <div className="px-3 py-2 text-sm" style={{color: '#42DF50'}}>
                              <p className="font-medium mb-1">Usage This Month:</p>
                              <div className="space-y-1 text-xs">
                                <div className="flex justify-between">
                                  <span>Text Analyses:</span>
                                  <span>{user.usage_stats?.analyses_this_month || 0}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Files Uploaded:</span>
                                  <span>{user.usage_stats?.files_uploaded || 0}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>URLs Analyzed:</span>
                                  <span>{user.usage_stats?.urls_analyzed || 0}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Logout Button - Moved to right of User Menu */}
                    <button
                      onClick={(e) => {
                        console.log("Logout button clicked!");
                        e.preventDefault();
                        e.stopPropagation();
                        logout();
                        toast({
                          title: "Logged Out",
                          description: "You have been successfully logged out.",
                        });
                      }}
                      className="flex items-center space-x-2 bg-black/40 px-3 py-2 rounded-lg border hover:border-red-500/50 transition-colors text-red-400 hover:text-red-300"
                      style={{borderColor: 'red'}}>
                      <LogOut className="h-4 w-4" />
                      <span className="text-sm">Logout</span>
                    </button>
                  </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <div className="relative">
          <div className="relative z-10 px-6 py-16 pointer-events-none">
            <div className="max-w-4xl mx-auto text-center pointer-events-auto">
              <div className="flex flex-col items-center justify-center text-center mb-6">
                <img src="/pulse-point-icon.png" alt="Pulse Point Icon" className="h-40 w-40 mb-4" />
                <div className="flex justify-center w-full">
                  <img src="/pulse-point-logo.png" alt="Pulse Point Logo" className="h-30 w-auto mx-auto ml-8" />
                </div>
              </div>
              <p className="text-xl mb-8 max-w-2xl mx-auto leading-relaxed drop-shadow-md" style={{color: '#42DF50'}}>
                Advanced sentiment analysis for PR and marketing professionals. Analyze brand mentions, customer feedback, and campaign performance with AI-powered insights.
              </p>
              <div className="flex items-center justify-center space-x-8 text-sm" style={{color: '#42DF50'}}>
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4" style={{color: '#42DF50'}} />
                  <span>Real-time Analysis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4" style={{color: '#42DF50'}} />
                  <span>Professional Insights</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Brain className="h-4 w-4" style={{color: '#42DF50'}} />
                  <span>AI-Powered</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto px-6 pb-16">
          {/* Tab Navigation */}
          <div className="flex justify-center mb-8">
            <div className="bg-black/60 backdrop-blur-lg rounded-xl p-1 border border-green-500/20">
              <div className="flex space-x-1">
                <button
                  onClick={() => setActiveTab("text")}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === "text"
                      ? "text-black shadow-lg"
                      : "hover:text-white"
                  }`}
                  style={activeTab === "text" 
                    ? {backgroundColor: '#42DF50'} 
                    : {color: '#42DF50', backgroundColor: 'rgba(66, 223, 80, 0.1)'}}
                >
                  <FileText className="mr-2 h-4 w-4 inline" />
                  Text Analysis
                </button>
                <button
                  onClick={() => setActiveTab("file")}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === "file"
                      ? "text-black shadow-lg"
                      : "hover:text-white"
                  }`}
                  style={activeTab === "file" 
                    ? {backgroundColor: '#42DF50'} 
                    : {color: '#42DF50', backgroundColor: 'rgba(66, 223, 80, 0.1)'}}
                >
                  <Upload className="mr-2 h-4 w-4 inline" />
                  File Analysis
                </button>
                <button
                  onClick={() => setActiveTab("url")}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === "url"
                      ? "text-white shadow-lg"
                      : "hover:text-white"
                  }`}
                  style={activeTab === "url" 
                    ? {backgroundColor: '#42DF50'} 
                    : {color: '#42DF50', backgroundColor: 'rgba(66, 223, 80, 0.1)'}}
                >
                  <Monitor className="mr-2 h-4 w-4 inline" />
                  URL Analysis
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Analysis Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold" style={{color: '#42DF50'}}>
                  {activeTab === "text" ? "Sentiment Analysis" : 
                   activeTab === "file" ? "File Upload & Analysis" :
                   "URL Analysis & Web Scraping"}
                </CardTitle>
                <CardDescription style={{color: '#42DF50'}}>
                  {activeTab === "text" 
                    ? "Enter your text below to analyze sentiment and get professional insights"
                    : activeTab === "file"
                    ? "Upload TXT, CSV, Excel, or PDF files for batch sentiment analysis"
                    : "Analyze sentiment from any webpage - news articles, blogs, reviews, and more"
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {activeTab === "text" ? (
                  // Text Analysis Mode
                  <>
                    <div className="space-y-3">
                      <label className="text-sm font-medium" style={{color: '#42DF50'}}>
                        Text to Analyze
                      </label>
                      <Textarea
                        placeholder="Enter customer feedback, social media mentions, reviews, or any text you want to analyze..."
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        className="min-h-[120px] resize-none bg-black/40 border-green-500/30 text-green-100 placeholder:text-green-300/60 focus:border-green-400 focus:ring-green-400/50"
                      />
                    </div>
                    
                    <Button 
                      onClick={analyzeSentiment}
                      disabled={loading || !text.trim()}
                      className="w-full py-3 text-lg font-semibold transition-all duration-200 hover:scale-105"
                      style={{backgroundColor: '#42DF50', color: 'black'}}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Brain className="mr-2 h-4 w-4" />
                          Analyze Sentiment
                        </>
                      )}
                    </Button>
                  </>
                ) : activeTab === "file" ? (
                  // File Analysis Mode
                  <>
                    {/* File Upload Drop Zone */}
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      className="border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200"
                      style={{
                        borderColor: isDragActive ? '#42DF50' : '#42DF50',
                        backgroundColor: isDragActive ? 'rgba(66, 223, 80, 0.1)' : 'transparent'
                      }}
                      onMouseEnter={(e) => e.target.style.borderColor = '#42DF50'}
                      onMouseLeave={(e) => e.target.style.borderColor = '#42DF50'}
                    >
                      <FileUp className={`mx-auto h-12 w-12 mb-4`} style={{color: '#42DF50'}} />
                      <div className="space-y-2">
                        <p className="font-medium" style={{color: '#42DF50'}}>
                          {isDragActive ? "Drop your file here" : "Drag & drop your file here"}
                        </p>
                        <p className="text-sm" style={{color: '#42DF50'}}>
                          or click to browse files
                        </p>
                        <p className="text-xs" style={{color: '#42DF50'}}>
                          Supports TXT, CSV, Excel, and PDF files (max 5MB)
                        </p>
                      </div>
                      <input
                        type="file"
                        accept=".txt,.csv,.xls,.xlsx,.pdf"
                        onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                    </div>

                    {/* File Upload Status */}
                    {uploadLoading && (
                      <div className="flex items-center justify-center space-x-2 p-4 bg-blue-950/30 border border-blue-500/30 rounded-lg">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                        <span className="text-blue-300">Uploading and processing file...</span>
                      </div>
                    )}

                    {uploadedFile && (
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2 p-4 bg-green-950/30 border border-green-500/30 rounded-lg">
                          <CheckCircle className="h-5 w-5 text-green-400" />
                          <div className="flex-1">
                            <p className="text-green-200 font-medium">{uploadedFile.filename}</p>
                            <p className="text-sm" style={{color: '#42DF50'}}>
                              {uploadedFile.total_entries} text entries extracted • {uploadedFile.file_type.toUpperCase()} file
                            </p>
                          </div>
                        </div>

                        <Button 
                          onClick={handleBatchAnalysis}
                          disabled={batchLoading}
                          className="w-full font-medium py-3 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl border text-white"
                          style={{
                            background: '#42DF50',
                            borderColor: '#42DF50'
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.background = '#3BC642';
                            e.target.style.borderColor = '#3BC642';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.background = '#42DF50';
                            e.target.style.borderColor = '#42DF50';
                          }}
                        >
                          {batchLoading ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Analyzing {uploadedFile.total_entries} entries...
                            </>
                          ) : (
                            <>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Analyze All Entries
                            </>
                          )}
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  // URL Analysis Mode
                  <>
                    {/* Single URL Analysis */}
                    <div className="space-y-4">
                      <div className="space-y-3">
                        <label className="text-sm font-medium" style={{color: '#42DF50'}}>
                          Website URL to Analyze
                        </label>
                        <div className="flex space-x-2">
                          <input
                            type="url"
                            placeholder="https://example.com/article"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            className="flex-1 px-3 py-2 bg-black/40 border border-green-500/30 rounded-lg text-green-100 placeholder:text-green-300/60 focus:border-green-400 focus:ring-green-400/50 focus:outline-none"
                          />
                          <Button 
                            onClick={analyzeUrl}
                            disabled={urlLoading || !url.trim()}
                            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-medium px-6 rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl border border-blue-500/20"
                          >
                            {urlLoading ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <Monitor className="mr-2 h-4 w-4" />
                                Analyze
                              </>
                            )}
                          </Button>
                        </div>
                        <p className="text-xs" style={{color: '#42DF50'}}>
                          Supports news articles, blog posts, product pages, and any web content
                        </p>
                      </div>
                    </div>

                    {/* Batch URL Analysis */}
                    <div className="mt-6 pt-6 border-t border-green-500/20">
                      <div className="space-y-3">
                        <label className="text-sm font-medium" style={{color: '#42DF50'}}>
                          Batch URL Analysis (One URL per line)
                        </label>
                        <Textarea
                          placeholder={`https://example.com/article1\nhttps://example.com/article2\nhttps://example.com/article3`}
                          value={urls}
                          onChange={(e) => setUrls(e.target.value)}
                          className="min-h-[100px] resize-none bg-black/40 border text-green-100 placeholder:text-green-300/60 focus:ring-green-400/50 focus:outline-none"
                          style={{
                            borderColor: '#42DF50',
                            color: '#42DF50'
                          }}
                          onFocus={(e) => {
                            e.target.style.borderColor = '#42DF50';
                            e.target.style.boxShadow = '0 0 0 1px rgba(66, 223, 80, 0.5)';
                          }}
                          onBlur={(e) => {
                            e.target.style.borderColor = '#42DF50';
                            e.target.style.boxShadow = 'none';
                          }}
                        />
                        <div className="flex items-center justify-between">
                          <p className="text-xs" style={{color: '#42DF50'}}>
                            Maximum 20 URLs per batch
                          </p>
                          <Button 
                            onClick={analyzeBatchUrls}
                            disabled={batchUrlLoading || !urls.trim()}
                            className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-medium py-2 px-4 rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl border border-cyan-500/20"
                          >
                            {batchUrlLoading ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Processing {urls.split('\n').filter(u => u.trim()).length} URLs...
                              </>
                            ) : (
                              <>
                                <BarChart3 className="mr-2 h-4 w-4" />
                                Analyze All URLs
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* Current Analysis Result */}
                {analysis && activeTab === "text" && (
                  <Alert className="border-l-4 border-l-green-500 bg-green-950/50 backdrop-blur-sm border border-green-500/20">
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-full ${getSentimentColor(analysis.sentiment)}`}>
                        {getSentimentIcon(analysis.sentiment)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant={getSentimentBadgeVariant(analysis.sentiment)} className="font-medium">
                            {analysis.sentiment.toUpperCase()}
                          </Badge>
                          <span className="text-sm" style={{color: '#42DF50'}}>
                            {Math.round(analysis.confidence * 100)}% confidence
                          </span>
                          {/* Sarcasm Detection Warning */}
                          {analysis.sarcasm_detected && (
                            <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getSarcasmBadgeColor()}`}>
                              <AlertTriangle className="h-3 w-3" />
                              <span>SARCASM ({Math.round(analysis.sarcasm_confidence * 100)}%)</span>
                            </div>
                          )}
                        </div>

                        {/* Aspect-Based Analysis Display */}
                        {analysis.aspects_analysis && analysis.aspects_analysis.length > 0 && (
                          <div className="mb-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-sm font-medium text-green-200">Aspect-Based Analysis:</span>
                              <div className="px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs font-medium">
                                {analysis.aspects_analysis.length} aspects detected
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <div className="grid grid-cols-1 gap-2">
                                {analysis.aspects_analysis
                                  .sort((a, b) => b.confidence - a.confidence) // Sort by confidence
                                  .slice(0, 6) // Show top 6 aspects
                                  .map((aspect, index) => (
                                    <div key={index} className="flex items-center justify-between p-3 bg-black/40 rounded-lg border border-emerald-500/20 hover:border-emerald-500/40 transition-colors">
                                      <div className="flex items-center space-x-3">
                                        <div className={`p-1.5 rounded-full ${getSentimentColor(aspect.sentiment)}`}>
                                          {getSentimentIcon(aspect.sentiment)}
                                        </div>
                                        <div className="flex-1">
                                          <div className="flex items-center space-x-2 mb-1">
                                            <span className="text-sm font-medium text-green-200">
                                              {aspect.aspect}
                                            </span>
                                            <Badge variant={getSentimentBadgeVariant(aspect.sentiment)} className="text-xs">
                                              {aspect.sentiment}
                                            </Badge>
                                          </div>
                                          {aspect.explanation && (
                                            <p className="text-xs text-green-300/80 italic">
                                              {aspect.explanation}
                                            </p>
                                          )}
                                          {aspect.keywords && aspect.keywords.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-1">
                                              {aspect.keywords.slice(0, 3).map((keyword, kidx) => (
                                                <span key={kidx} className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded text-xs">
                                                  {keyword}
                                                </span>
                                              ))}
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <div className="w-16 bg-green-800/50 rounded-full h-2">
                                          <div 
                                            className={`h-2 rounded-full ${getSentimentColor(aspect.sentiment)}`}
                                            style={{ width: `${aspect.confidence * 100}%` }}
                                          />
                                        </div>
                                        <span className="text-xs text-green-300 font-medium">
                                          {Math.round(aspect.confidence * 100)}%
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                              
                              {analysis.aspects_summary && (
                                <div className="mt-2 p-2 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
                                  <span className="text-xs font-medium text-emerald-200">Aspects Summary:</span>
                                  <p className="text-xs text-emerald-300 mt-1">{analysis.aspects_summary}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Topic Analysis Display */}
                        {analysis.topics_detected && analysis.topics_detected.length > 0 && (
                          <div className="mb-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-sm font-medium text-green-200">Primary Topic:</span>
                              {analysis.primary_topic && (
                                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getTopicColor(analysis.primary_topic)}`}>
                                  {getTopicIcon(analysis.primary_topic)}
                                  <span>{analysis.topics_detected.find(t => t.topic === analysis.primary_topic)?.display_name || analysis.primary_topic}</span>
                                  <span>({Math.round((analysis.topics_detected.find(t => t.topic === analysis.primary_topic)?.confidence || 0) * 100)}%)</span>
                                </div>
                              )}
                            </div>
                            
                            <div className="space-y-2">
                              <span className="text-sm font-medium text-green-200">All Topics Detected:</span>
                              <div className="grid grid-cols-1 gap-2">
                                {analysis.topics_detected
                                  .sort((a, b) => b.confidence - a.confidence) // Sort by confidence
                                  .slice(0, 4) // Show top 4 topics
                                  .map((topic, index) => (
                                    <div key={topic.topic} className="flex items-center justify-between p-2 bg-black/40 rounded-lg border border-green-500/20">
                                      <div className="flex items-center space-x-2">
                                        {getTopicIcon(topic.topic)}
                                        <span className="text-sm font-medium text-green-200">
                                          {topic.display_name}
                                        </span>
                                        {topic.keywords && topic.keywords.length > 0 && (
                                          <div className="flex flex-wrap gap-1">
                                            {topic.keywords.slice(0, 3).map((keyword, kidx) => (
                                              <span key={kidx} className="px-1.5 py-0.5 bg-green-500/20 text-green-300 rounded text-xs">
                                                {keyword}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <div className="w-16 bg-green-800/50 rounded-full h-2">
                                          <div 
                                            className={`h-2 rounded-full ${getTopicColor(topic.topic).split(' ')[0]}`}
                                            style={{ width: `${topic.confidence * 100}%` }}
                                          />
                                        </div>
                                        <span className="text-xs text-green-300 font-medium">
                                          {Math.round(topic.confidence * 100)}%
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                              
                              {analysis.topic_summary && (
                                <div className="mt-2 p-2 bg-green-950/30 border border-green-500/30 rounded-lg">
                                  <span className="text-xs font-medium text-green-200">Topic Summary:</span>
                                  <p className="text-xs text-green-300 mt-1">{analysis.topic_summary}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Sarcasm Analysis Display */}
                        {analysis.sarcasm_detected && (
                          <div className="mb-3 p-3 bg-orange-950/30 border border-orange-500/30 rounded-lg">
                            <div className="flex items-start space-x-2 mb-2">
                              <AlertTriangle className="h-4 w-4 text-orange-400 mt-0.5" />
                              <div>
                                <span className="text-sm font-medium text-orange-200">Sarcasm Detected</span>
                                <p className="text-xs text-orange-300 mt-1">{analysis.sarcasm_explanation}</p>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-3">
                              <div>
                                <span className="text-xs text-orange-200 font-medium">Surface Sentiment:</span>
                                <div className="flex items-center space-x-1 mt-1">
                                  <Badge variant={getSentimentBadgeVariant(analysis.sentiment)} className="text-xs">
                                    {analysis.sentiment}
                                  </Badge>
                                  <span className="text-xs" style={{color: '#42DF50'}}>{Math.round(analysis.confidence * 100)}%</span>
                                </div>
                              </div>
                              <div>
                                <span className="text-xs text-orange-200 font-medium">Actual Meaning:</span>
                                <div className="flex items-center space-x-1 mt-1">
                                  <Badge variant={getSentimentBadgeVariant(analysis.adjusted_sentiment)} className="text-xs">
                                    {analysis.adjusted_sentiment}
                                  </Badge>
                                  <span className="text-xs text-orange-300">After sarcasm</span>
                                </div>
                              </div>
                            </div>
                            {analysis.sarcasm_indicators && analysis.sarcasm_indicators.length > 0 && (
                              <div className="mt-3">
                                <span className="text-xs text-orange-200 font-medium">Sarcasm Indicators:</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {analysis.sarcasm_indicators.map((indicator, index) => (
                                    <span key={index} className="px-2 py-0.5 bg-orange-500/20 text-orange-300 rounded text-xs">
                                      "{indicator}"
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Emotion Detection Display */}
                        {analysis.emotions && Object.keys(analysis.emotions).length > 0 && (
                          <div className="mb-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-sm font-medium text-green-200">Dominant Emotion:</span>
                              {analysis.dominant_emotion && (
                                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getEmotionColor(analysis.dominant_emotion)}`}>
                                  {getEmotionIcon(analysis.dominant_emotion)}
                                  <span>{formatEmotionName(analysis.dominant_emotion)}</span>
                                  <span>({Math.round((analysis.emotions[analysis.dominant_emotion] || 0) * 100)}%)</span>
                                </div>
                              )}
                            </div>
                            
                            <div className="space-y-2">
                              <span className="text-sm font-medium text-green-200">All Emotions Detected:</span>
                              <div className="grid grid-cols-2 gap-2">
                                {Object.entries(analysis.emotions)
                                  .filter(([_, confidence]) => confidence > 0.1) // Only show emotions with >10% confidence
                                  .sort(([, a], [, b]) => b - a) // Sort by confidence
                                  .slice(0, 6) // Show top 6 emotions
                                  .map(([emotion, confidence]) => (
                                    <div key={emotion} className="flex items-center justify-between p-2 bg-black/40 rounded-lg border border-green-500/20">
                                      <div className="flex items-center space-x-2">
                                        {getEmotionIcon(emotion)}
                                        <span className="text-sm font-medium text-green-200">
                                          {formatEmotionName(emotion)}
                                        </span>
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <div className="w-16 bg-green-800/50 rounded-full h-2">
                                          <div 
                                            className={`h-2 rounded-full ${getEmotionColor(emotion).split(' ')[0]}`}
                                            style={{ width: `${confidence * 100}%` }}
                                          />
                                        </div>
                                        <span className="text-xs text-green-300 font-medium">
                                          {Math.round(confidence * 100)}%
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          </div>
                        )}

                        <AlertDescription className="text-green-100">
                          {analysis.analysis}
                        </AlertDescription>
                      </div>
                    </div>
                  </Alert>
                )}

                {/* Batch Analysis Results */}
                {batchResults && activeTab === "file" && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-emerald-400" />
                        <div>
                          <p className="text-emerald-200 font-medium">Batch Analysis Complete</p>
                          <p className="text-emerald-300 text-sm">
                            {batchResults.total_processed} entries analyzed from {batchResults.filename}
                          </p>
                        </div>
                      </div>
                      <Button 
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                        onClick={() => {
                          const csvContent = "data:text/csv;charset=utf-8," + 
                            encodeURIComponent(
                              "Row,Text,Sentiment,Confidence,Dominant Emotion,Primary Topic,Aspects Count\n" +
                              batchResults.results.map(result => 
                                `"${result.row_number}","${result.text.replace(/"/g, '""')}","${result.sentiment}","${result.confidence}","${result.dominant_emotion}","${result.primary_topic}","${result.aspects_analysis?.length || 0}"`
                              ).join("\n")
                            );
                          const link = document.createElement("a");
                          link.setAttribute("href", csvContent);
                          link.setAttribute("download", `batch_analysis_${batchResults.filename}.csv`);
                          link.click();
                        }}
                      >
                        <Download className="mr-1 h-3 w-3" />
                        Export CSV
                      </Button>
                    </div>

                    {/* Batch Results Summary */}
                    <div className="grid grid-cols-3 gap-4">
                      {(() => {
                        const sentimentCounts = batchResults.results.reduce((acc, result) => {
                          acc[result.sentiment] = (acc[result.sentiment] || 0) + 1;
                          return acc;
                        }, {});
                        return (
                          <>
                            <div className="text-center p-3 bg-green-950/30 border border-green-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-green-400">{sentimentCounts.positive || 0}</div>
                              <div className="text-xs text-green-300">Positive</div>
                            </div>
                            <div className="text-center p-3 bg-red-950/30 border border-red-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-red-400">{sentimentCounts.negative || 0}</div>
                              <div className="text-xs text-red-300">Negative</div>
                            </div>
                            <div className="text-center p-3 bg-slate-950/30 border border-slate-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-slate-400">{sentimentCounts.neutral || 0}</div>
                              <div className="text-xs text-slate-300">Neutral</div>
                            </div>
                          </>
                        );
                      })()}
                    </div>

                    {/* Sample Results Preview */}
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-green-200">Sample Results Preview:</p>
                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {batchResults.results.slice(0, 5).map((result, index) => (
                          <div key={index} className="p-3 bg-black/40 border border-green-500/20 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <Badge variant={getSentimentBadgeVariant(result.sentiment)} className="text-xs">
                                  {result.sentiment}
                                </Badge>
                                <span className="text-xs" style={{color: '#42DF50'}}>
                                  Row {result.row_number} • {Math.round(result.confidence * 100)}%
                                </span>
                                {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                                  <Badge className="text-xs bg-emerald-500/20 text-emerald-300">
                                    {result.aspects_analysis.length} aspects
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <p className="text-sm" style={{color: '#42DF50'}} className="line-clamp-2">
                              "{result.text.length > 100 ? result.text.substring(0, 100) + "..." : result.text}"
                            </p>
                            {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {result.aspects_analysis.slice(0, 3).map((aspect, aspIdx) => (
                                  <span key={aspIdx} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded text-xs">
                                    {aspect.aspect}: {aspect.sentiment}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                        {batchResults.results.length > 5 && (
                          <div className="text-center py-2">
                            <span className="text-sm text-green-300">
                              ...and {batchResults.results.length - 5} more results
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Single URL Analysis Results */}
                {urlResults && activeTab === "url" && (
                  <Alert className="border-blue-500/30 bg-blue-950/30">
                    <CheckCircle className="h-4 w-4 text-blue-400" />
                    <AlertDescription className="text-blue-100">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{urlResults.title || 'Webpage Analysis'}</p>
                            <div className="flex items-center space-x-4 text-sm text-blue-300 mt-1">
                              <span>{urlResults.text_length} characters</span>
                              <span>{urlResults.processing_time.toFixed(2)}s processing</span>
                              {urlResults.author && <span>by {urlResults.author}</span>}
                            </div>
                          </div>
                          <Badge variant={getSentimentBadgeVariant(urlResults.sentiment)} className="text-sm">
                            {urlResults.sentiment} ({Math.round(urlResults.confidence * 100)}%)
                          </Badge>
                        </div>

                        {/* URL Analysis Details */}
                        <div className="grid grid-cols-1 gap-3">
                          {/* Aspects Analysis Display for URL */}
                          {urlResults.aspects_analysis && urlResults.aspects_analysis.length > 0 && (
                            <div className="space-y-2">
                              <span className="text-sm font-medium text-blue-200">Aspects Detected:</span>
                              <div className="flex flex-wrap gap-2">
                                {urlResults.aspects_analysis.slice(0, 4).map((aspect, index) => (
                                  <div key={index} className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30`}>
                                    {getSentimentIcon(aspect.sentiment)}
                                    <span>{aspect.aspect}</span>
                                    <span>({Math.round(aspect.confidence * 100)}%)</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Topics Display for URL */}
                          {urlResults.topics_detected && urlResults.topics_detected.length > 0 && (
                            <div className="space-y-2">
                              <span className="text-sm font-medium text-blue-200">Topics Detected:</span>
                              <div className="flex flex-wrap gap-2">
                                {urlResults.topics_detected.slice(0, 3).map((topic, index) => (
                                  <div key={topic.topic} className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getTopicColor(topic.topic)}`}>
                                    {getTopicIcon(topic.topic)}
                                    <span>{topic.display_name}</span>
                                    <span>({Math.round(topic.confidence * 100)}%)</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Emotions Display for URL */}
                          {urlResults.emotions && Object.keys(urlResults.emotions).length > 0 && (
                            <div className="space-y-2">
                              <span className="text-sm font-medium text-blue-200">Emotions Detected:</span>
                              <div className="flex flex-wrap gap-2">
                                {Object.entries(urlResults.emotions)
                                  .filter(([_, confidence]) => confidence > 0.2)
                                  .sort(([, a], [, b]) => b - a)
                                  .slice(0, 3)
                                  .map(([emotion, confidence]) => (
                                    <div key={emotion} className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getEmotionColor(emotion)}`}>
                                      {getEmotionIcon(emotion)}
                                      <span>{formatEmotionName(emotion)}</span>
                                      <span>({Math.round(confidence * 100)}%)</span>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Sarcasm Warning for URL */}
                          {urlResults.sarcasm_detected && (
                            <div className="flex items-center space-x-2 p-2 bg-orange-950/30 border border-orange-500/30 rounded-lg">
                              <AlertTriangle className="h-4 w-4 text-orange-400" />
                              <div className="text-sm">
                                <span className="text-orange-200 font-medium">Sarcasm Detected</span>
                                <span className="text-orange-300 ml-2">
                                  Appears {urlResults.sentiment} but likely {urlResults.adjusted_sentiment}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="text-xs text-blue-300 pt-2 border-t border-blue-500/20">
                          <p className="italic">"{urlResults.extracted_text.substring(0, 200)}..."</p>
                          <p className="mt-1">Source: {urlResults.url}</p>
                        </div>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Batch URL Analysis Results */}
                {batchUrlResults && activeTab === "url" && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-cyan-950/30 border border-cyan-500/30 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-cyan-400" />
                        <div>
                          <p className="text-cyan-200 font-medium">Batch URL Analysis Complete</p>
                          <p className="text-cyan-300 text-sm">
                            {batchUrlResults.total_processed}/{batchUrlResults.total_requested} URLs analyzed successfully
                            {batchUrlResults.total_failed > 0 && ` (${batchUrlResults.total_failed} failed)`}
                          </p>
                        </div>
                      </div>
                      <Button 
                        size="sm"
                        className="bg-cyan-600 hover:bg-cyan-700"
                        onClick={() => {
                          const csvContent = "data:text/csv;charset=utf-8," + 
                            encodeURIComponent(
                              "URL,Title,Sentiment,Confidence,Text Length,Processing Time,Dominant Emotion,Primary Topic,Aspects Count\n" +
                              batchUrlResults.results.map(result => 
                                `"${result.url}","${(result.title || '').replace(/"/g, '""')}","${result.sentiment}","${result.confidence}","${result.text_length}","${result.processing_time}","${result.dominant_emotion}","${result.primary_topic}","${result.aspects_analysis?.length || 0}"`
                              ).join("\n")
                            );
                          const link = document.createElement("a");
                          link.setAttribute("href", csvContent);
                          link.setAttribute("download", `batch_url_analysis_${new Date().toISOString().split('T')[0]}.csv`);
                          link.click();
                        }}
                      >
                        <Download className="mr-1 h-3 w-3" />
                        Export CSV
                      </Button>
                    </div>

                    {/* Batch URL Results Summary */}
                    <div className="grid grid-cols-3 gap-4">
                      {(() => {
                        const sentimentCounts = batchUrlResults.results.reduce((acc, result) => {
                          acc[result.sentiment] = (acc[result.sentiment] || 0) + 1;
                          return acc;
                        }, {});
                        return (
                          <>
                            <div className="text-center p-3 bg-green-950/30 border border-green-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-green-400">{sentimentCounts.positive || 0}</div>
                              <div className="text-xs text-green-300">Positive</div>
                            </div>
                            <div className="text-center p-3 bg-red-950/30 border border-red-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-red-400">{sentimentCounts.negative || 0}</div>
                              <div className="text-xs text-red-300">Negative</div>
                            </div>
                            <div className="text-center p-3 bg-slate-950/30 border border-slate-500/30 rounded-lg">
                              <div className="text-2xl font-bold text-slate-400">{sentimentCounts.neutral || 0}</div>
                              <div className="text-xs text-slate-300">Neutral</div>
                            </div>
                          </>
                        );
                      })()}
                    </div>

                    {/* Sample URL Results Preview */}
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-cyan-200">Sample Results Preview:</p>
                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {batchUrlResults.results.slice(0, 3).map((result, index) => (
                          <div key={index} className="p-3 bg-black/40 border border-cyan-500/20 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <Badge variant={getSentimentBadgeVariant(result.sentiment)} className="text-xs">
                                  {result.sentiment}
                                </Badge>
                                <span className="text-xs text-cyan-300">
                                  {result.text_length} chars • {result.processing_time.toFixed(1)}s
                                </span>
                                {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                                  <Badge className="text-xs bg-emerald-500/20 text-emerald-300">
                                    {result.aspects_analysis.length} aspects
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <p className="text-sm text-cyan-200 font-medium line-clamp-1">
                              {result.title || 'Untitled'}
                            </p>
                            <p className="text-xs text-cyan-300 line-clamp-1 mt-1">
                              {result.url}
                            </p>
                            {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {result.aspects_analysis.slice(0, 3).map((aspect, aspIdx) => (
                                  <span key={aspIdx} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded text-xs">
                                    {aspect.aspect}: {aspect.sentiment}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                        {batchUrlResults.results.length > 3 && (
                          <div className="text-center py-2">
                            <span className="text-sm text-cyan-300">
                              ...and {batchUrlResults.results.length - 3} more results
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* History Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold" style={{color: '#42DF50'}}>
                  {activeTab === "text" ? "Recent Analysis" : 
                   activeTab === "file" ? "Batch Analysis Results" :
                   "URL Analysis Results"}
                </CardTitle>
                <CardDescription style={{color: '#42DF50'}}>
                  {activeTab === "text" 
                    ? "Your sentiment analysis history"
                    : activeTab === "file"
                    ? batchResults 
                      ? "Detailed results from your uploaded file"
                      : "Upload a file to see detailed batch analysis results"
                    : batchUrlResults || urlResults
                      ? "Detailed results from your URL analysis"
                      : "Analyze URLs to see detailed results here"
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {activeTab === "text" ? (
                  // Text Analysis History
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                  {history.length === 0 ? (
                    <div className="text-center py-8" style={{color: '#42DF50'}}>
                      <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" style={{color: '#42DF50'}} />
                      <p>No analysis history yet</p>
                      <p className="text-sm" style={{color: '#42DF50'}}>Start analyzing text to see results here</p>
                    </div>
                  ) : (
                    history.map((item) => (
                      <div key={item.id} className="p-4 rounded-xl border border-green-500/20 hover:border-green-500/40 transition-colors bg-black/40 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2 flex-wrap">
                            <Badge variant={getSentimentBadgeVariant(item.sentiment)} className="text-xs">
                              {item.sentiment}
                            </Badge>
                            {item.dominant_emotion && (
                              <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getEmotionColor(item.dominant_emotion)}`}>
                                {getEmotionIcon(item.dominant_emotion)}
                                <span>{formatEmotionName(item.dominant_emotion)}</span>
                              </div>
                            )}
                            {item.sarcasm_detected && (
                              <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getSarcasmBadgeColor()}`}>
                                <AlertTriangle className="h-3 w-3" />
                                <span>SARCASM</span>
                              </div>
                            )}
                            {item.primary_topic && (
                              <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getTopicColor(item.primary_topic)}`}>
                                {getTopicIcon(item.primary_topic)}
                                <span>{item.topics_detected?.find(t => t.topic === item.primary_topic)?.display_name || item.primary_topic.replace('_', ' ')}</span>
                              </div>
                            )}
                            {item.aspects_analysis && item.aspects_analysis.length > 0 && (
                              <div className="inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300">
                                <Tag className="h-3 w-3" />
                                <span>{item.aspects_analysis.length} aspects</span>
                              </div>
                            )}
                          </div>
                          <span className="text-xs text-green-300">
                            {Math.round(item.confidence * 100)}%
                          </span>
                        </div>
                        <p className="text-sm mb-2 line-clamp-2" style={{color: '#42DF50'}}>
                          "{item.text.length > 100 ? item.text.substring(0, 100) + "..." : item.text}"
                        </p>
                        
                        {/* Sarcasm warning in history */}
                        {item.sarcasm_detected && item.adjusted_sentiment !== item.sentiment && (
                          <div className="text-xs text-orange-300 mb-2 italic">
                            ⚠️ Appears {item.sentiment} but actually {item.adjusted_sentiment} (sarcastic)
                          </div>
                        )}
                        
                        {/* Topic summary in history */}
                        {item.topic_summary && (
                          <div className="text-xs text-green-300 mb-2 italic">
                            📋 {item.topic_summary}
                          </div>
                        )}
                        
                        {/* Aspects summary in history */}
                        {item.aspects_summary && (
                          <div className="text-xs text-emerald-300 mb-2 italic">
                            🎯 {item.aspects_summary}
                          </div>
                        )}
                        
                        <div className="flex flex-wrap gap-1 mb-2">
                          {/* Aspects Display */}
                          {item.aspects_analysis && item.aspects_analysis.length > 0 && (
                            <>
                              {item.aspects_analysis
                                .sort((a, b) => b.confidence - a.confidence)
                                .slice(0, 3) // Show top 3 aspects in history
                                .map((aspect, index) => (
                                  <div key={index} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30`}>
                                    {getSentimentIcon(aspect.sentiment)}
                                    <span>{aspect.aspect}</span>
                                    <span>({Math.round(aspect.confidence * 100)}%)</span>
                                  </div>
                                ))}
                            </>
                          )}
                          
                          {/* Topics Display */}
                          {item.topics_detected && item.topics_detected.length > 0 && (
                            <>
                              {item.topics_detected
                                .sort((a, b) => b.confidence - a.confidence)
                                .slice(0, 2) // Show top 2 topics in history
                                .map((topic, index) => (
                                  <div key={topic.topic} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs ${getTopicColor(topic.topic)}`}>
                                    {getTopicIcon(topic.topic)}
                                    <span>{Math.round(topic.confidence * 100)}%</span>
                                  </div>
                                ))}
                            </>
                          )}
                          
                          {/* Emotions Display */}
                          {item.emotions && Object.keys(item.emotions).length > 0 && (
                            <>
                              {Object.entries(item.emotions)
                                .filter(([_, confidence]) => confidence > 0.2) // Show emotions with >20% confidence
                                .sort(([, a], [, b]) => b - a) // Sort by confidence
                                .slice(0, 1) // Show top 1 emotion in history (reduced to make room for aspects and topics)
                                .map(([emotion, confidence]) => (
                                  <div key={emotion} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs ${getEmotionColor(emotion)}`}>
                                    {getEmotionIcon(emotion)}
                                    <span>{Math.round(confidence * 100)}%</span>
                                  </div>
                                ))}
                            </>
                          )}
                        </div>
                        <p className="text-xs text-green-300 italic">
                          {item.analysis}
                        </p>
                      </div>
                    ))
                  )}
                  </div>
                ) : activeTab === "file" ? (
                  // File Analysis Detailed Results
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {!batchResults ? (
                      <div className="text-center py-8" style={{color: '#42DF50'}}>
                        <FileUp className="h-12 w-12 mx-auto mb-3 opacity-50" style={{color: '#42DF50'}} />
                        <p>No batch analysis results yet</p>
                        <p className="text-sm">Upload a file to see detailed results here</p>
                      </div>
                    ) : (
                      batchResults.results.map((result, index) => (
                        <div key={index} className="p-4 rounded-xl border border-green-500/20 hover:border-green-500/40 transition-colors bg-black/40 backdrop-blur-sm">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2 flex-wrap">
                              <Badge variant={getSentimentBadgeVariant(result.sentiment)} className="text-xs">
                                {result.sentiment}
                              </Badge>
                              <span className="text-xs" style={{color: '#42DF50'}}>
                                Row {result.row_number}
                              </span>
                              {result.dominant_emotion && (
                                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getEmotionColor(result.dominant_emotion)}`}>
                                  {getEmotionIcon(result.dominant_emotion)}
                                  <span>{formatEmotionName(result.dominant_emotion)}</span>
                                </div>
                              )}
                              {result.sarcasm_detected && (
                                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getSarcasmBadgeColor()}`}>
                                  <AlertTriangle className="h-3 w-3" />
                                  <span>SARCASM</span>
                                </div>
                              )}
                              {result.primary_topic && (
                                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getTopicColor(result.primary_topic)}`}>
                                  {getTopicIcon(result.primary_topic)}
                                  <span>{result.topics_detected?.find(t => t.topic === result.primary_topic)?.display_name || result.primary_topic.replace('_', ' ')}</span>
                                </div>
                              )}
                              {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                                <div className="inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300">
                                  <Tag className="h-3 w-3" />
                                  <span>{result.aspects_analysis.length} aspects</span>
                                </div>
                              )}
                            </div>
                            <span className="text-xs text-green-300">
                              {Math.round(result.confidence * 100)}%
                            </span>
                          </div>
                          <p className="text-sm mb-2 line-clamp-2" style={{color: '#42DF50'}}>
                            "{result.text.length > 150 ? result.text.substring(0, 150) + "..." : result.text}"
                          </p>
                          
                          {/* Sarcasm warning in batch results */}
                          {result.sarcasm_detected && result.adjusted_sentiment !== result.sentiment && (
                            <div className="text-xs text-orange-300 mb-2 italic">
                              ⚠️ Appears {result.sentiment} but actually {result.adjusted_sentiment} (sarcastic)
                            </div>
                          )}
                          
                          {/* Aspects summary in batch results */}
                          {result.aspects_summary && (
                            <div className="text-xs text-emerald-300 mb-2 italic">
                              🎯 {result.aspects_summary}
                            </div>
                          )}

                          {/* Topic summary in batch results */}
                          {result.topic_summary && (
                            <div className="text-xs text-green-300 mb-2 italic">
                              📋 {result.topic_summary}
                            </div>
                          )}
                          
                          <div className="flex flex-wrap gap-1">
                            {/* Aspects Display */}
                            {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                              <>
                                {result.aspects_analysis
                                  .sort((a, b) => b.confidence - a.confidence)
                                  .slice(0, 2) // Show top 2 aspects in batch history
                                  .map((aspect, aspectIndex) => (
                                    <div key={aspectIndex} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30`}>
                                      {getSentimentIcon(aspect.sentiment)}
                                      <span>{aspect.aspect}</span>
                                      <span>({Math.round(aspect.confidence * 100)}%)</span>
                                    </div>
                                  ))}
                              </>
                            )}
                            
                            {/* Topics Display */}
                            {result.topics_detected && result.topics_detected.length > 0 && (
                              <>
                                {result.topics_detected
                                  .sort((a, b) => b.confidence - a.confidence)
                                  .slice(0, 1) // Show top 1 topic in batch history
                                  .map((topic, topicIndex) => (
                                    <div key={topic.topic} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs ${getTopicColor(topic.topic)}`}>
                                      {getTopicIcon(topic.topic)}
                                      <span>{Math.round(topic.confidence * 100)}%</span>
                                    </div>
                                  ))}
                              </>
                            )}
                            
                            {/* Emotions Display */}
                            {result.emotions && Object.keys(result.emotions).length > 0 && (
                              <>
                                {Object.entries(result.emotions)
                                  .filter(([_, confidence]) => confidence > 0.3) // Show emotions with >30% confidence
                                  .sort(([, a], [, b]) => b - a) // Sort by confidence
                                  .slice(0, 1) // Show top 1 emotion in batch history
                                  .map(([emotion, confidence]) => (
                                    <div key={emotion} className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-xs ${getEmotionColor(emotion)}`}>
                                      {getEmotionIcon(emotion)}
                                      <span>{Math.round(confidence * 100)}%</span>
                                    </div>
                                  ))}
                              </>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                ) : (
                  // URL Analysis Detailed Results
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {!batchUrlResults && !urlResults ? (
                      <div className="text-center py-8" style={{color: '#42DF50'}}>
                        <Monitor className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>No URL analysis results yet</p>
                        <p className="text-sm">Analyze URLs to see detailed results here</p>
                      </div>
                    ) : (
                      <>
                        {/* Display single URL result if available */}
                        {urlResults && (
                          <div className="p-4 rounded-xl border border-blue-500/20 hover:border-blue-500/40 transition-colors bg-black/40 backdrop-blur-sm">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2 flex-wrap">
                                <Badge variant={getSentimentBadgeVariant(urlResults.sentiment)} className="text-xs">
                                  {urlResults.sentiment}
                                </Badge>
                                <span className="text-xs text-blue-300">
                                  Single URL
                                </span>
                                {urlResults.dominant_emotion && (
                                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getEmotionColor(urlResults.dominant_emotion)}`}>
                                    {getEmotionIcon(urlResults.dominant_emotion)}
                                    <span>{formatEmotionName(urlResults.dominant_emotion)}</span>
                                  </div>
                                )}
                                {urlResults.sarcasm_detected && (
                                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getSarcasmBadgeColor()}`}>
                                    <AlertTriangle className="h-3 w-3" />
                                    <span>SARCASM</span>
                                  </div>
                                )}
                                {urlResults.aspects_analysis && urlResults.aspects_analysis.length > 0 && (
                                  <div className="inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300">
                                    <Tag className="h-3 w-3" />
                                    <span>{urlResults.aspects_analysis.length} aspects</span>
                                  </div>
                                )}
                              </div>
                              <span className="text-xs text-blue-300">
                                {Math.round(urlResults.confidence * 100)}%
                              </span>
                            </div>
                            <p className="text-sm text-blue-200 mb-2 font-medium line-clamp-1">
                              {urlResults.title || 'Untitled'}
                            </p>
                            <p className="text-xs text-blue-300 mb-2 line-clamp-1">
                              {urlResults.url}
                            </p>
                            <p className="text-xs text-blue-300">
                              {urlResults.text_length} characters • {urlResults.processing_time.toFixed(2)}s processing
                            </p>
                          </div>
                        )}

                        {/* Display batch URL results if available */}
                        {batchUrlResults && batchUrlResults.results.map((result, index) => (
                          <div key={index} className="p-4 rounded-xl border border-cyan-500/20 hover:border-cyan-500/40 transition-colors bg-black/40 backdrop-blur-sm">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2 flex-wrap">
                                <Badge variant={getSentimentBadgeVariant(result.sentiment)} className="text-xs">
                                  {result.sentiment}
                                </Badge>
                                <span className="text-xs text-cyan-300">
                                  URL #{index + 1}
                                </span>
                                {result.dominant_emotion && (
                                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getEmotionColor(result.dominant_emotion)}`}>
                                    {getEmotionIcon(result.dominant_emotion)}
                                    <span>{formatEmotionName(result.dominant_emotion)}</span>
                                  </div>
                                )}
                                {result.sarcasm_detected && (
                                  <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getSarcasmBadgeColor()}`}>
                                    <AlertTriangle className="h-3 w-3" />
                                    <span>SARCASM</span>
                                  </div>
                                )}
                                {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                                  <div className="inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-300">
                                    <Tag className="h-3 w-3" />
                                    <span>{result.aspects_analysis.length} aspects</span>
                                  </div>
                                )}
                              </div>
                              <span className="text-xs text-cyan-300">
                                {Math.round(result.confidence * 100)}%
                              </span>
                            </div>
                            
                            <p className="text-sm text-cyan-200 mb-2 font-medium line-clamp-1">
                              {result.title || 'Untitled'}
                            </p>
                            <p className="text-xs text-cyan-300 mb-2 line-clamp-1">
                              {result.url}
                            </p>
                            
                            {/* Sarcasm warning in batch results */}
                            {result.sarcasm_detected && result.adjusted_sentiment !== result.sentiment && (
                              <div className="text-xs text-orange-300 mb-2 italic">
                                ⚠️ Appears {result.sentiment} but actually {result.adjusted_sentiment} (sarcastic)
                              </div>
                            )}
                            
                            {/* Aspects summary in batch results */}
                            {result.aspects_summary && (
                              <div className="text-xs text-emerald-300 mb-2 italic">
                                🎯 {result.aspects_summary}
                              </div>
                            )}

                            {/* Topic summary in batch results */}
                            {result.topic_summary && (
                              <div className="text-xs text-green-300 mb-2 italic">
                                📋 {result.topic_summary}
                              </div>
                            )}
                            
                            <div className="flex justify-between items-center text-xs text-cyan-300">
                              <span>{result.text_length} characters</span>
                              <span>{result.processing_time.toFixed(2)}s</span>
                            </div>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Features Section */}
          <div className="mt-16">
            <h2 className="text-3xl font-bold text-center mb-12" style={{color: '#42DF50'}}>
              Professional Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border" style={{borderColor: '#42DF50'}}>
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4" style={{backgroundColor: '#42DF50'}}>
                  <Tag className="h-6 w-6 text-black" />
                </div>
                <h3 className="font-semibold mb-2" style={{color: '#42DF50'}}>Aspect-Based Analysis</h3>
                <p className="text-sm" style={{color: '#42DF50'}}>
                  Analyze sentiment for specific aspects like food quality, service speed, pricing, and more with individual confidence scores
                </p>
              </Card>

              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border" style={{borderColor: '#42DF50'}}>
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4" style={{backgroundColor: '#42DF50'}}>
                  <Heart className="h-6 w-6 text-black" />
                </div>
                <h3 className="font-semibold mb-2" style={{color: '#42DF50'}}>Emotion Detection</h3>
                <p className="text-sm" style={{color: '#42DF50'}}>
                  Advanced AI detects 8 core emotions including joy, trust, anger, and fear with confidence scores
                </p>
              </Card>

              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border" style={{borderColor: '#42DF50'}}>
                <div className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4" style={{backgroundColor: '#42DF50'}}>
                  <BarChart3 className="h-6 w-6 text-black" />
                </div>
                <h3 className="font-semibold mb-2" style={{color: '#42DF50'}}>Professional Reports</h3>
                <p className="text-sm" style={{color: '#42DF50'}}>
                  Comprehensive analysis history and insights for professional decision making
                </p>
              </Card>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

// Main App component with AuthProvider
const App = () => {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
    </AuthProvider>
  );
};

export default App;