import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Loader2, TrendingUp, TrendingDown, Minus, BarChart3, Brain, Zap, Smile, Frown, Meh, Heart, Shield, X, Sparkles, Clock, AlertTriangle, Tag, Users, DollarSign, Truck, Monitor, Bug, Megaphone, FileText, GitCompare, Lightbulb, Lock, Zap as Performance, Upload, Download, FileUp, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { Toaster } from "./components/ui/toaster";
import { useToast } from "./hooks/use-toast";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const { toast } = useToast();

  // File upload states
  const [activeTab, setActiveTab] = useState("text"); // "text" or "file"
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResults, setBatchResults] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/sentiment-history`);
      setHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

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
        {/* Hero Section */}
        <div className="relative">
          <div className="relative z-10 px-6 py-16">
            <div className="max-w-4xl mx-auto text-center">
              <div className="flex items-center justify-center mb-6">
                <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-3 rounded-2xl shadow-lg backdrop-blur-sm border border-green-500/20">
                  <Brain className="h-8 w-8 text-white" />
                </div>
              </div>
              <h1 className="text-5xl font-bold bg-gradient-to-r from-green-400 via-emerald-300 to-green-500 bg-clip-text text-transparent mb-4 drop-shadow-lg">
                Brand Watch AI
              </h1>
              <p className="text-xl text-green-100 mb-8 max-w-2xl mx-auto leading-relaxed drop-shadow-md">
                Advanced sentiment analysis for PR and marketing professionals. Analyze brand mentions, customer feedback, and campaign performance with AI-powered insights.
              </p>
              <div className="flex items-center justify-center space-x-8 text-sm text-green-200">
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-green-400" />
                  <span>Real-time Analysis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-4 w-4 text-emerald-400" />
                  <span>Professional Insights</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Brain className="h-4 w-4 text-green-300" />
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
                  className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === "text"
                      ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg"
                      : "text-green-300 hover:text-green-100 hover:bg-green-500/20"
                  }`}
                >
                  <FileText className="mr-2 h-4 w-4 inline" />
                  Text Analysis
                </button>
                <button
                  onClick={() => setActiveTab("file")}
                  className={`px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === "file"
                      ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg"
                      : "text-green-300 hover:text-green-100 hover:bg-green-500/20"
                  }`}
                >
                  <Upload className="mr-2 h-4 w-4 inline" />
                  File Analysis
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Analysis Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold text-green-100">
                  {activeTab === "text" ? "Sentiment Analysis" : "File Upload & Analysis"}
                </CardTitle>
                <CardDescription className="text-green-200">
                  {activeTab === "text" 
                    ? "Enter your text below to analyze sentiment and get professional insights"
                    : "Upload TXT, CSV, Excel, or PDF files for batch sentiment analysis"
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {activeTab === "text" ? (
                  // Text Analysis Mode
                  <>
                    <div className="space-y-3">
                      <label className="text-sm font-medium text-green-200">
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
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-medium py-3 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl border border-green-500/20"
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
                ) : (
                  // File Analysis Mode
                  <>
                    {/* File Upload Drop Zone */}
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                        isDragActive
                          ? "border-green-400 bg-green-500/10"
                          : "border-green-500/30 hover:border-green-500/50"
                      }`}
                    >
                      <FileUp className={`mx-auto h-12 w-12 mb-4 ${isDragActive ? "text-green-400" : "text-green-300"}`} />
                      <div className="space-y-2">
                        <p className="text-green-100 font-medium">
                          {isDragActive ? "Drop your file here" : "Drag & drop your file here"}
                        </p>
                        <p className="text-green-300 text-sm">
                          or click to browse files
                        </p>
                        <p className="text-green-400/80 text-xs">
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
                            <p className="text-green-300 text-sm">
                              {uploadedFile.total_entries} text entries extracted • {uploadedFile.file_type.toUpperCase()} file
                            </p>
                          </div>
                        </div>

                        <Button 
                          onClick={handleBatchAnalysis}
                          disabled={batchLoading}
                          className="w-full bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white font-medium py-3 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl border border-emerald-500/20"
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
                          <span className="text-sm text-green-200">
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
                                  <span className="text-xs text-green-300">{Math.round(analysis.confidence * 100)}%</span>
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
                                <span className="text-xs text-green-300">
                                  Row {result.row_number} • {Math.round(result.confidence * 100)}%
                                </span>
                                {result.aspects_analysis && result.aspects_analysis.length > 0 && (
                                  <Badge className="text-xs bg-emerald-500/20 text-emerald-300">
                                    {result.aspects_analysis.length} aspects
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <p className="text-sm text-green-200 line-clamp-2">
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
              </CardContent>
            </Card>

            {/* History Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold text-green-100">
                  {activeTab === "text" ? "Recent Analysis" : "Batch Analysis Results"}
                </CardTitle>
                <CardDescription className="text-green-200">
                  {activeTab === "text" 
                    ? "Your sentiment analysis history"
                    : batchResults 
                      ? "Detailed results from your uploaded file"
                      : "Upload a file to see detailed batch analysis results"
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {activeTab === "text" ? (
                  // Text Analysis History
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                  {history.length === 0 ? (
                    <div className="text-center py-8 text-green-300">
                      <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>No analysis history yet</p>
                      <p className="text-sm">Start analyzing text to see results here</p>
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
                        <p className="text-sm text-green-200 mb-2 line-clamp-2">
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
                ) : (
                  // File Analysis Detailed Results
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {!batchResults ? (
                      <div className="text-center py-8 text-green-300">
                        <FileUp className="h-12 w-12 mx-auto mb-3 opacity-50" />
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
                              <span className="text-xs text-green-300">
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
                          <p className="text-sm text-green-200 mb-2 line-clamp-2">
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
                )}
              </CardContent>
            </Card>
          </div>

          {/* Features Section */}
          <div className="mt-16">
            <h2 className="text-3xl font-bold text-center text-green-100 mb-12">
              Professional Features
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border border-green-500/20">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Tag className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-semibold text-green-100 mb-2">Aspect-Based Analysis</h3>
                <p className="text-sm text-green-200">
                  Analyze sentiment for specific aspects like food quality, service speed, pricing, and more with individual confidence scores
                </p>
              </Card>

              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border border-green-500/20">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Heart className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-semibold text-green-100 mb-2">Emotion Detection</h3>
                <p className="text-sm text-green-200">
                  Advanced AI detects 8 core emotions including joy, trust, anger, and fear with confidence scores
                </p>
              </Card>

              <Card className="text-center p-6 border-0 shadow-2xl bg-black/60 backdrop-blur-lg hover:shadow-xl transition-shadow border border-green-500/20">
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-semibold text-green-100 mb-2">Professional Reports</h3>
                <p className="text-sm text-green-200">
                  Comprehensive analysis history and insights for professional decision making
                </p>
              </Card>
            </div>
          </div>
        </div>
      </div>

      <Toaster />
    </div>
  );
};

export default App;