"""
Search query logging for tracking search quality and identifying problematic queries.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class SearchLogger:
    """Logs search queries and results for analysis."""
    
    def __init__(self, log_path: str = "/app/data/search_history.jsonl"):
        self.log_path = Path(log_path)
        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_search(
        self,
        query: str,
        results_count: int,
        top_score: float,
        top_3_avg: float,
        expanded_query: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> None:
        """
        Log a search query and its results.
        
        Args:
            query: Original search query
            results_count: Number of results returned
            top_score: Similarity score of top result
            top_3_avg: Average score of top 3 results
            expanded_query: The expanded query (if different from original)
            filters: Any filters applied (has_characters, etc.)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "expanded_query": expanded_query if expanded_query != query else None,
            "results_count": results_count,
            "top_score": round(top_score, 4),
            "top_3_avg": round(top_3_avg, 4),
            "filters": filters or {},
        }
        
        # Append to JSONL file (one JSON object per line)
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except OSError:
            # Read-only filesystem or other write error - silently skip logging
            pass
    
    def get_recent_searches(self, limit: int = 100) -> list[dict]:
        """Get the most recent search queries."""
        if not self.log_path.exists():
            return []
        
        searches = []
        with open(self.log_path, "r") as f:
            for line in f:
                searches.append(json.loads(line.strip()))
        
        return searches[-limit:]
    
    def get_problematic_queries(
        self,
        min_occurrences: int = 2,
        score_threshold: float = 0.45,
    ) -> list[dict]:
        """
        Find queries that consistently return poor results.
        
        Args:
            min_occurrences: Minimum times a query must appear
            score_threshold: Queries with avg top_score below this are flagged
            
        Returns:
            List of problematic queries with stats
        """
        if not self.log_path.exists():
            return []
        
        # Group by query
        query_stats = {}
        
        with open(self.log_path, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                query = entry["query"]
                
                if query not in query_stats:
                    query_stats[query] = {
                        "query": query,
                        "count": 0,
                        "scores": [],
                        "has_expansion": entry.get("expanded_query") is not None,
                    }
                
                query_stats[query]["count"] += 1
                query_stats[query]["scores"].append(entry["top_score"])
        
        # Find problematic ones
        problematic = []
        for stats in query_stats.values():
            if stats["count"] >= min_occurrences:
                avg_score = sum(stats["scores"]) / len(stats["scores"])
                
                if avg_score < score_threshold:
                    problematic.append({
                        "query": stats["query"],
                        "count": stats["count"],
                        "avg_top_score": round(avg_score, 4),
                        "has_expansion": stats["has_expansion"],
                    })
        
        # Sort by avg score (worst first)
        problematic.sort(key=lambda x: x["avg_top_score"])
        return problematic
