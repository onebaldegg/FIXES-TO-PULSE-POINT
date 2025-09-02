import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Loader2, TrendingUp, TrendingDown, Minus, BarChart3, Brain, Zap, Smile, Frown, Meh, Heart, Shield, X, Sparkles, Clock, AlertTriangle, Tag, Users, DollarSign, Truck, Monitor, Bug, Megaphone, FileText, GitCompare, Lightbulb, Lock, Zap as Performance } from "lucide-react";
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Analysis Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold text-green-100">
                  Sentiment Analysis
                </CardTitle>
                <CardDescription className="text-green-200">
                  Enter your text below to analyze sentiment and get professional insights
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
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

                {/* Current Analysis Result */}
                {analysis && (
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
              </CardContent>
            </Card>

            {/* History Panel */}
            <Card className="shadow-2xl border-0 bg-black/60 backdrop-blur-lg border border-green-500/20">
              <CardHeader className="pb-4">
                <CardTitle className="text-2xl font-semibold text-green-100">
                  Recent Analysis
                </CardTitle>
                <CardDescription className="text-green-200">
                  Your sentiment analysis history
                </CardDescription>
              </CardHeader>
              <CardContent>
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
                        
                        <div className="flex flex-wrap gap-1 mb-2">
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
                                .slice(0, 2) // Show top 2 emotions in history (reduced to make room for topics)
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
                <h3 className="font-semibold text-green-100 mb-2">Topic Analysis</h3>
                <p className="text-sm text-green-200">
                  Automatically detect discussion topics including customer service, pricing, product quality, and technical issues
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