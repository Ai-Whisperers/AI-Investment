"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpIcon, ArrowDownIcon, TrendingUpIcon, AlertCircleIcon } from "lucide-react";

interface Signal {
  ticker: string;
  action: string;
  confidence: number;
  expected_return: number;
  timeframe: string;
  signal_type: string;
  sources: string[];
  pattern_stack: string[];
  created_at: string;
}

interface MemeStock {
  ticker: string;
  virality_score: number;
  velocity: number;
  expected_move: string;
  timeframe: string;
  platforms: string[];
}

export default function ExtremeSignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [memeStocks, setMemeStocks] = useState<MemeStock[]>([]);
  const [backtestResults, setBacktestResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSignals();
    fetchMemeStocks();
    fetchBacktest();
  }, []);

  const fetchSignals = async () => {
    try {
      const response = await fetch("/api/v1/extreme/signals/live?confidence_min=0.7");
      const data = await response.json();
      setSignals(data);
    } catch (error) {
      console.error("Failed to fetch signals:", error);
    }
  };

  const fetchMemeStocks = async () => {
    try {
      const response = await fetch("/api/v1/extreme/meme/trending");
      const data = await response.json();
      setMemeStocks(data);
    } catch (error) {
      console.error("Failed to fetch meme stocks:", error);
    }
  };

  const fetchBacktest = async () => {
    try {
      const response = await fetch("/api/v1/extreme/backtest/validate");
      const data = await response.json();
      setBacktestResults(data);
    } catch (error) {
      console.error("Failed to fetch backtest:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerCollection = async () => {
    try {
      const response = await fetch("/api/v1/extreme/collect/signals", {
        method: "POST",
      });
      const data = await response.json();
      alert(`Collected ${data.collected} signals, stored ${data.stored}`);
      fetchSignals();
    } catch (error) {
      console.error("Failed to trigger collection:", error);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.85) return "text-green-600";
    if (confidence > 0.7) return "text-yellow-600";
    return "text-red-600";
  };

  const getActionIcon = (action: string) => {
    if (action === "STRONG_BUY" || action === "BUY") {
      return <ArrowUpIcon className="h-4 w-4 text-green-600" />;
    }
    if (action === "SELL") {
      return <ArrowDownIcon className="h-4 w-4 text-red-600" />;
    }
    return <TrendingUpIcon className="h-4 w-4 text-blue-600" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading extreme signals...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🚀 Extreme Alpha Signals</h1>
        <p className="text-gray-600">
          Targeting >30% returns through information asymmetry exploitation
        </p>
      </div>

      {/* Performance Overview */}
      {backtestResults && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Historical Performance Validation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Return</p>
                <p className="text-2xl font-bold text-green-600">
                  {backtestResults.total_return}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold">{backtestResults.win_rate}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Sharpe Ratio</p>
                <p className="text-2xl font-bold">{backtestResults.sharpe_ratio}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Max Drawdown</p>
                <p className="text-2xl font-bold text-red-600">
                  {backtestResults.max_drawdown}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="mb-8 flex gap-4">
        <Button onClick={triggerCollection} variant="default">
          Trigger Signal Collection
        </Button>
        <Button onClick={fetchSignals} variant="outline">
          Refresh Signals
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Live Signals */}
        <div>
          <h2 className="text-2xl font-bold mb-4">🎯 Live High-Confidence Signals</h2>
          <div className="space-y-4">
            {signals.length > 0 ? (
              signals.map((signal, index) => (
                <Card key={index}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getActionIcon(signal.action)}
                        <span className="text-xl font-bold">{signal.ticker}</span>
                        <Badge variant="outline">{signal.signal_type}</Badge>
                      </div>
                      <Badge className={getConfidenceColor(signal.confidence)}>
                        {(signal.confidence * 100).toFixed(0)}% confidence
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">Expected Return:</span>
                        <span className="ml-2 font-semibold text-green-600">
                          +{(signal.expected_return * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Timeframe:</span>
                        <span className="ml-2">{signal.timeframe}</span>
                      </div>
                    </div>
                    
                    {signal.pattern_stack && signal.pattern_stack.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs text-gray-600">Patterns:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {signal.pattern_stack.map((pattern, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {pattern}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-2 flex flex-wrap gap-1">
                      {signal.sources.map((source, i) => (
                        <span key={i} className="text-xs text-gray-500">
                          {source}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-gray-500">
                    <AlertCircleIcon className="h-5 w-5" />
                    <span>No high-confidence signals detected</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Meme Stocks */}
        <div>
          <h2 className="text-2xl font-bold mb-4">🔥 Viral Meme Stocks</h2>
          <div className="space-y-4">
            {memeStocks.length > 0 ? (
              memeStocks.map((stock, index) => (
                <Card key={index}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xl font-bold">{stock.ticker}</span>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-orange-600">
                          {stock.virality_score}/100
                        </div>
                        <div className="text-xs text-gray-600">Virality</div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">Velocity:</span>
                        <span className="ml-2 font-semibold">
                          {stock.velocity}x
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Expected:</span>
                        <span className="ml-2 font-semibold text-green-600">
                          {stock.expected_move}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-2">
                      <span className="text-xs text-gray-600">Active on:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {stock.platforms.map((platform, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {platform}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500">
                      Move expected in: {stock.timeframe}
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 text-gray-500">
                    <AlertCircleIcon className="h-5 w-5" />
                    <span>No viral stocks detected</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-12 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-semibold">Risk Disclaimer</p>
            <p>
              These signals target extreme returns through high-risk strategies.
              Past performance does not guarantee future results. Only invest
              what you can afford to lose. This is not financial advice.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}