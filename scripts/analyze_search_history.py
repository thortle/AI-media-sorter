#!/usr/bin/env python3
"""
Analyze search history to identify problematic queries and suggest expansions.
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "photo-server"))

from app.search_logger import SearchLogger
from app.search import QUERY_EXPANSIONS


def analyze_search_history(
    min_occurrences: int = 2,
    score_threshold: float = 0.45,
):
    """Analyze search history and suggest new query expansions."""
    
    # Use relative path from script location
    data_path = Path(__file__).parent.parent / "data" / "search_history.jsonl"
    logger = SearchLogger(str(data_path))
    
    print("="*70)
    print("SEARCH HISTORY ANALYSIS")
    print("="*70)
    
    # Get all recent searches
    recent = logger.get_recent_searches(limit=1000)
    print(f"\nTotal searches logged: {len(recent)}")
    
    if not recent:
        print("\nNo search history found yet. Start searching to build history!")
        return
    
    # Most common queries
    all_queries = [s["query"] for s in recent]
    most_common = Counter(all_queries).most_common(20)
    
    print(f"\nTop 20 Most Searched Queries:")
    print("-" * 70)
    for query, count in most_common:
        has_exp = "✓" if query in QUERY_EXPANSIONS else " "
        print(f"  [{has_exp}] {query:40} ({count} searches)")
    
    # Problematic queries
    problematic = logger.get_problematic_queries(
        min_occurrences=min_occurrences,
        score_threshold=score_threshold,
    )
    
    print(f"\nProblematic Queries (avg top score < {score_threshold}):")
    print("-" * 70)
    
    if not problematic:
        print("  No problematic queries found! All searches performing well.")
    else:
        print(f"  Found {len(problematic)} queries that need improvement:\n")
        
        for item in problematic:
            exp_status = "HAS expansion" if item["has_expansion"] else "NO expansion"
            print(f"  • {item['query']:<40} avg: {item['avg_top_score']:.3f} ({item['count']}x) [{exp_status}]")
        
        # Suggest which need expansions
        needs_expansion = [q for q in problematic if not q["has_expansion"]]
        
        if needs_expansion:
            print(f"\nSuggested New Expansions:")
            print("-" * 70)
            print("  Add these to QUERY_EXPANSIONS in search.py:\n")
            
            for item in needs_expansion[:10]:  # Top 10
                query = item['query']
                print(f'  "{query}": "TODO - add expansion for {query}",')
        
        # Check if existing expansions are working
        has_expansion_but_poor = [q for q in problematic if q["has_expansion"]]
        if has_expansion_but_poor:
            print(f"\nExpansions That May Need Improvement:")
            print("-" * 70)
            for item in has_expansion_but_poor:
                query = item['query']
                current_exp = QUERY_EXPANSIONS.get(query, "")
                print(f'  "{query}": "{current_exp[:60]}..."')
                print(f"    (avg score: {item['avg_top_score']:.3f})\n")
    
    # Average scores by expansion status
    with_exp = [s["top_score"] for s in recent if s.get("expanded_query")]
    without_exp = [s["top_score"] for s in recent if not s.get("expanded_query")]
    
    if with_exp and without_exp:
        print(f"\nExpansion Impact:")
        print("-" * 70)
        print(f"  Avg score WITH expansion:    {sum(with_exp)/len(with_exp):.4f} ({len(with_exp)} searches)")
        print(f"  Avg score WITHOUT expansion: {sum(without_exp)/len(without_exp):.4f} ({len(without_exp)} searches)")
        improvement = ((sum(with_exp)/len(with_exp)) - (sum(without_exp)/len(without_exp))) / (sum(without_exp)/len(without_exp)) * 100
        print(f"  Improvement: {improvement:+.1f}%")
    
    print("\n" + "="*70)


def export_suggestions(output_path: str = None):
    """Export problematic queries as a JSON file for manual expansion creation."""
    data_path = Path(__file__).parent.parent / "data" / "search_history.jsonl"
    logger = SearchLogger(str(data_path))
    problematic = logger.get_problematic_queries(min_occurrences=2, score_threshold=0.45)
    
    needs_expansion = [q for q in problematic if not q["has_expansion"]]
    
    output = {
        "generated_at": "now",
        "suggestions": [
            {
                "query": q["query"],
                "avg_score": q["avg_top_score"],
                "count": q["count"],
                "suggested_expansion": f"TODO - manually write expansion for '{q['query']}'"
            }
            for q in needs_expansion
        ]
    }
    
    if output_path is None:
        output_path = str(Path(__file__).parent.parent / "data" / "expansion_suggestions.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Exported {len(needs_expansion)} suggestions to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze search history")
    parser.add_argument("--min-occurrences", type=int, default=2, help="Min times query must appear")
    parser.add_argument("--threshold", type=float, default=0.45, help="Score threshold for problematic queries")
    parser.add_argument("--export", action="store_true", help="Export suggestions to JSON")
    
    args = parser.parse_args()
    
    analyze_search_history(
        min_occurrences=args.min_occurrences,
        score_threshold=args.threshold,
    )
    
    if args.export:
        export_suggestions()
