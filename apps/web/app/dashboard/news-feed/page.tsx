"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Calendar,
  Filter,
  Search,
  RefreshCw,
  ExternalLink,
  BarChart3,
  MessageSquare,
  Hash,
  Youtube,
  Globe,
} from "lucide-react";

interface NewsArticle {
  id: string;
  title: string;
  description: string;
  url: string;
  source: string;
  source_type: "official" | "reddit" | "youtube" | "twitter" | "scraped";
  published_at: string;
  sentiment: number;
  relevance_score: number;
  entities: Array<{
    symbol: string;
    name: string;
    relevance: number;
  }>;
  tags: string[];
  image_url?: string;
  author?: string;
  engagement?: {
    views?: number;
    likes?: number;
    comments?: number;
  };
}

interface MarketData {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
}

export default function NewsFeegPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<NewsArticle[]>([]);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedSentiment, setSelectedSentiment] = useState("all");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchNews();
    fetchMarketData();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchNews();
        fetchMarketData();
      }, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  useEffect(() => {
    filterArticles();
  }, [articles, searchTerm, selectedSource, selectedSentiment, activeTab]);

  const fetchNews = async () => {
    try {
      const response = await fetch("/api/v1/news/feed");
      if (!response.ok) throw new Error("Failed to fetch news");
      const data = await response.json();
      setArticles(data.articles || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketData = async () => {
    try {
      const response = await fetch("/api/v1/market/summary");
      if (!response.ok) throw new Error("Failed to fetch market data");
      const data = await response.json();
      setMarketData(data.tickers || []);
    } catch (err) {
      console.error("Market data error:", err);
    }
  };

  const filterArticles = () => {
    let filtered = [...articles];

    // Tab filter
    if (activeTab !== "all") {
      filtered = filtered.filter(article => {
        switch (activeTab) {
          case "official":
            return article.source_type === "official";
          case "social":
            return ["reddit", "twitter", "youtube"].includes(article.source_type);
          case "ai_insights":
            return article.relevance_score > 0.8;
          default:
            return true;
        }
      });
    }

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        article =>
          article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          article.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          article.entities.some(e =>
            e.symbol.toLowerCase().includes(searchTerm.toLowerCase())
          )
      );
    }

    // Source filter
    if (selectedSource !== "all") {
      filtered = filtered.filter(article => article.source_type === selectedSource);
    }

    // Sentiment filter
    if (selectedSentiment !== "all") {
      filtered = filtered.filter(article => {
        if (selectedSentiment === "positive") return article.sentiment > 0.3;
        if (selectedSentiment === "negative") return article.sentiment < -0.3;
        return Math.abs(article.sentiment) <= 0.3; // neutral
      });
    }

    setFilteredArticles(filtered);
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.3) return "text-green-600";
    if (sentiment < -0.3) return "text-red-600";
    return "text-gray-600";
  };

  const getSentimentIcon = (sentiment: number) => {
    if (sentiment > 0.3) return <TrendingUp className="h-4 w-4" />;
    if (sentiment < -0.3) return <TrendingDown className="h-4 w-4" />;
    return <AlertCircle className="h-4 w-4" />;
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case "reddit":
        return <MessageSquare className="h-4 w-4" />;
      case "twitter":
        return <Hash className="h-4 w-4" />;
      case "youtube":
        return <Youtube className="h-4 w-4" />;
      default:
        return <Globe className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Financial News Feed</h1>
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchNews();
              fetchMarketData();
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            Auto-Refresh: {autoRefresh ? "ON" : "OFF"}
          </Button>
        </div>
      </div>

      {/* Market Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Market Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {marketData.map((ticker) => (
              <div key={ticker.ticker} className="text-center">
                <div className="font-bold">{ticker.ticker}</div>
                <div className="text-lg">${ticker.price.toFixed(2)}</div>
                <div
                  className={`text-sm ${
                    ticker.change_percent >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {ticker.change_percent >= 0 ? "+" : ""}
                  {ticker.change_percent.toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search news, tickers, or keywords..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedSource} onValueChange={setSelectedSource}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="official">Official</SelectItem>
                <SelectItem value="reddit">Reddit</SelectItem>
                <SelectItem value="twitter">Twitter</SelectItem>
                <SelectItem value="youtube">YouTube</SelectItem>
                <SelectItem value="scraped">Scraped</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSentiment} onValueChange={setSelectedSentiment}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sentiment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sentiments</SelectItem>
                <SelectItem value="positive">Positive</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
                <SelectItem value="negative">Negative</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* News Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All News</TabsTrigger>
          <TabsTrigger value="official">Official Sources</TabsTrigger>
          <TabsTrigger value="social">Social Media</TabsTrigger>
          <TabsTrigger value="ai_insights">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4">
            {filteredArticles.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <p className="text-muted-foreground">No articles found matching your filters.</p>
                </CardContent>
              </Card>
            ) : (
              filteredArticles.map((article) => (
                <Card key={article.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold mb-2">
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-primary transition-colors"
                          >
                            {article.title}
                          </a>
                        </h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {article.description}
                        </p>
                      </div>
                      {article.image_url && (
                        <img
                          src={article.image_url}
                          alt={article.title}
                          className="w-24 h-24 object-cover rounded ml-4"
                        />
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 mb-3">
                      {/* Source */}
                      <div className="flex items-center gap-1">
                        {getSourceIcon(article.source_type)}
                        <span className="text-sm font-medium">{article.source}</span>
                      </div>

                      {/* Time */}
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {formatTimeAgo(article.published_at)}
                      </div>

                      {/* Sentiment */}
                      <div className={`flex items-center gap-1 ${getSentimentColor(article.sentiment)}`}>
                        {getSentimentIcon(article.sentiment)}
                        <span className="text-sm">
                          {article.sentiment > 0.3 ? "Bullish" :
                           article.sentiment < -0.3 ? "Bearish" : "Neutral"}
                        </span>
                      </div>

                      {/* Relevance Score */}
                      {article.relevance_score > 0.7 && (
                        <Badge variant="secondary">
                          High Relevance: {(article.relevance_score * 100).toFixed(0)}%
                        </Badge>
                      )}
                    </div>

                    {/* Entities */}
                    {article.entities.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {article.entities.map((entity) => (
                          <Badge key={entity.symbol} variant="outline">
                            ${entity.symbol}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Tags */}
                    {article.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {article.tags.map((tag) => (
                          <span key={tag} className="text-xs bg-secondary px-2 py-1 rounded">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Engagement */}
                    {article.engagement && (
                      <div className="flex gap-4 text-sm text-muted-foreground">
                        {article.engagement.views && (
                          <span>👁 {article.engagement.views.toLocaleString()} views</span>
                        )}
                        {article.engagement.likes && (
                          <span>👍 {article.engagement.likes.toLocaleString()}</span>
                        )}
                        {article.engagement.comments && (
                          <span>💬 {article.engagement.comments.toLocaleString()}</span>
                        )}
                      </div>
                    )}

                    <div className="mt-3 flex justify-end">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex items-center gap-1"
                      >
                        Read More
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}