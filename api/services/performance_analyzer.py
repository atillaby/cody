import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self, cache_manager, database):
        self.cache = cache_manager
        self.db = database

    async def calculate_strategy_metrics(self, strategy_name: str, timeframe: str = "1d") -> Dict:
        """Strateji metriklerini hesapla"""
        try:
            trades = await self._get_strategy_trades(strategy_name)
            df = pd.DataFrame(trades)

            if df.empty:
                return {"status": "no_trades"}

            metrics = {
                "total_trades": len(df),
                "win_rate": self._calculate_win_rate(df),
                "profit_factor": self._calculate_profit_factor(df),
                "avg_profit": df['profit'].mean(),
                "max_drawdown": self._calculate_max_drawdown(df),
                "sharpe_ratio": self._calculate_sharpe_ratio(df),
                "avg_trade_duration": self._calculate_avg_duration(df)
            }

            # Cache'e kaydet
            await self.cache.set(f"metrics_{strategy_name}", metrics, ttl=3600)
            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {"status": "error", "message": str(e)}

    def _calculate_win_rate(self, df: pd.DataFrame) -> float:
        """Kazanç oranını hesapla"""
        winning_trades = len(df[df['profit'] > 0])
        return (winning_trades / len(df)) * 100 if len(df) > 0 else 0

    def _calculate_profit_factor(self, df: pd.DataFrame) -> float:
        """Profit faktörünü hesapla"""
        gross_profit = df[df['profit'] > 0]['profit'].sum()
        gross_loss = abs(df[df['profit'] < 0]['profit'].sum())
        return gross_profit / gross_loss if gross_loss != 0 else 0

    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """Maximum drawdown hesapla"""
        cumulative = (df['profit'] + 1).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = (cumulative - rolling_max) / rolling_max
        return abs(drawdowns.min()) * 100

    def _calculate_sharpe_ratio(self, df: pd.DataFrame) -> float:
        """Sharpe oranını hesapla"""
        returns = df['profit']
        if len(returns) < 2:
            return 0
        return np.sqrt(365) * (returns.mean() / returns.std())

    async def generate_report(self, strategy_name: str) -> Dict:
        """Detaylı performans raporu oluştur"""
        try:
            metrics = await self.calculate_strategy_metrics(strategy_name)
            trades = await self._get_strategy_trades(strategy_name)

            report = {
                "strategy": strategy_name,
                "metrics": metrics,
                "recent_trades": trades[:10],
                "equity_curve": self._generate_equity_curve(trades),
                "monthly_returns": self._calculate_monthly_returns(trades),
                "risk_metrics": self._calculate_risk_metrics(trades)
            }

            return report
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"status": "error", "message": str(e)}
