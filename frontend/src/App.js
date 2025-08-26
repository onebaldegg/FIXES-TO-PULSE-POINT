import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Loader2, TrendingUp, TrendingDown, Minus, BarChart3, Brain, Zap } from "lucide-react";
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Section */}
      <div className="relative">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-10"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1666875753105-c63a6f3bdc86?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHxhbmFseXRpY3MlMjBkYXNoYm9hcmR8ZW58MHx8fHwxNzU2MjE2OTg3fDA&ixlib=rb-4.1.0&q=85')`
          }}
        />
        <div className="relative z-10 px-6 py-16">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-2xl shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 bg-clip-text text-transparent mb-4">
              Brand Watch AI
            </h1>
            <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Advanced sentiment analysis for PR and marketing professionals. Analyze brand mentions, customer feedback, and campaign performance with AI-powered insights.
            </p>
            <div className="flex items-center justify-center space-x-8 text-sm text-slate-500">
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-blue-500" />
                <span>Real-time Analysis</span>
              </div>
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4 text-indigo-500" />
                <span>Professional Insights</span>
              </div>
              <div className="flex items-center space-x-2">
                <Brain className="h-4 w-4 text-purple-500" />
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
          <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-2xl font-semibold text-slate-800">
                Sentiment Analysis
              </CardTitle>
              <CardDescription className="text-slate-600">
                Enter your text below to analyze sentiment and get professional insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <label className="text-sm font-medium text-slate-700">
                  Text to Analyze
                </label>
                <Textarea
                  placeholder="Enter customer feedback, social media mentions, reviews, or any text you want to analyze..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="min-h-[120px] resize-none border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              
              <Button 
                onClick={analyzeSentiment}
                disabled={loading || !text.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium py-3 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl"
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
                <Alert className="border-l-4 border-l-blue-500 bg-blue-50/50">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-full ${getSentimentColor(analysis.sentiment)}`}>
                      {getSentimentIcon(analysis.sentiment)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge variant={getSentimentBadgeVariant(analysis.sentiment)} className="font-medium">
                          {analysis.sentiment.toUpperCase()}
                        </Badge>
                        <span className="text-sm text-slate-600">
                          {Math.round(analysis.confidence * 100)}% confidence
                        </span>
                      </div>
                      <AlertDescription className="text-slate-700">
                        {analysis.analysis}
                      </AlertDescription>
                    </div>
                  </div>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* History Panel */}
          <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-2xl font-semibold text-slate-800">
                Recent Analysis
              </CardTitle>
              <CardDescription className="text-slate-600">
                Your sentiment analysis history
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {history.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No analysis history yet</p>
                    <p className="text-sm">Start analyzing text to see results here</p>
                  </div>
                ) : (
                  history.map((item) => (
                    <div key={item.id} className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors bg-white/60">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant={getSentimentBadgeVariant(item.sentiment)} className="text-xs">
                          {item.sentiment}
                        </Badge>
                        <span className="text-xs text-slate-500">
                          {Math.round(item.confidence * 100)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 mb-2 line-clamp-2">
                        "{item.text.length > 100 ? item.text.substring(0, 100) + "..." : item.text}"
                      </p>
                      <p className="text-xs text-slate-600 italic">
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
          <h2 className="text-3xl font-bold text-center text-slate-800 mb-12">
            Professional Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center p-6 border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">Real-time Analysis</h3>
              <p className="text-sm text-slate-600">
                Get instant sentiment analysis with confidence scores and detailed insights
              </p>
            </Card>

            <Card className="text-center p-6 border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">AI-Powered Insights</h3>
              <p className="text-sm text-slate-600">
                Advanced AI models trained specifically for PR and marketing text analysis
              </p>
            </Card>

            <Card className="text-center p-6 border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-shadow">
              <div className="bg-gradient-to-r from-purple-500 to-pink-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">Professional Reports</h3>
              <p className="text-sm text-slate-600">
                Comprehensive analysis history and insights for professional decision making
              </p>
            </Card>
          </div>
        </div>
      </div>

      <Toaster />
    </div>
  );
};

export default App;