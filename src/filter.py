import random
import re
from typing import List, Dict, Any, Optional

def filter_articles(articles: List[Dict[str, Any]], 
                   filter_by_title: Optional[str] = None,
                   exclude_by_title: Optional[str] = None,
                   max_articles: Optional[int] = None,
                   skip_first: int = 0,
                   random_sample: Optional[int] = None,
                   log_func=None) -> List[Dict[str, Any]]:
    """
    Filter articles based on various criteria.
    
    Args:
        articles: List of article dictionaries
        filter_by_title: Only include articles with titles containing this string
        exclude_by_title: Exclude articles with titles containing this string
        max_articles: Maximum number of articles to include
        skip_first: Skip first N articles
        random_sample: Randomly sample N articles
        log_func: Logging function
        
    Returns:
        Filtered list of articles
    """
    if log_func:
        log_func.logger.info(f"Starting with {len(articles)} articles")
    
    filtered_articles = articles.copy()
    
    # Skip first N articles
    if skip_first > 0:
        if skip_first >= len(filtered_articles):
            if log_func:
                log_func.logger.warning(f"Skip count ({skip_first}) is greater than or equal to article count ({len(filtered_articles)}), no articles will be processed")
            return []
        
        filtered_articles = filtered_articles[skip_first:]
        if log_func:
            log_func.logger.info(f"Skipped first {skip_first} articles, {len(filtered_articles)} remaining")
    
    # Filter by title
    if filter_by_title:
        original_count = len(filtered_articles)
        filtered_articles = [article for article in filtered_articles 
                           if filter_by_title.lower() in article.get('title', '').lower()]
        
        if log_func:
            log_func.logger.info(f"Filtered by title '{filter_by_title}': {original_count} -> {len(filtered_articles)} articles")
    
    # Exclude by title
    if exclude_by_title:
        original_count = len(filtered_articles)
        filtered_articles = [article for article in filtered_articles 
                           if exclude_by_title.lower() not in article.get('title', '').lower()]
        
        if log_func:
            log_func.logger.info(f"Excluded by title '{exclude_by_title}': {original_count} -> {len(filtered_articles)} articles")
    
    # Random sampling
    if random_sample is not None:
        if random_sample >= len(filtered_articles):
            if log_func:
                log_func.logger.warning(f"Sample size ({random_sample}) is greater than or equal to article count ({len(filtered_articles)}), using all articles")
        else:
            original_count = len(filtered_articles)
            filtered_articles = random.sample(filtered_articles, random_sample)
            
            if log_func:
                log_func.logger.info(f"Random sample of {random_sample} articles from {original_count} total")
    
    # Limit by max_articles
    if max_articles is not None:
        if max_articles < len(filtered_articles):
            filtered_articles = filtered_articles[:max_articles]
            
            if log_func:
                log_func.logger.info(f"Limited to {max_articles} articles")
    
    if log_func:
        log_func.logger.info(f"Final count: {len(filtered_articles)} articles")
    
    return filtered_articles


def filter_by_regex(articles: List[Dict[str, Any]], 
                    pattern: str, 
                    field: str = 'title',
                    exclude: bool = False,
                    log_func=None) -> List[Dict[str, Any]]:
    """
    Filter articles using a regular expression pattern.
    
    Args:
        articles: List of article dictionaries
        pattern: Regular expression pattern to match
        field: Field to apply the pattern to (default: 'title')
        exclude: If True, exclude matching articles instead of including them
        log_func: Logging function
        
    Returns:
        Filtered list of articles
    """
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        if log_func:
            log_func.logger.error(f"Invalid regex pattern '{pattern}': {e}")
        return articles
    
    original_count = len(articles)
    
    if exclude:
        filtered_articles = [article for article in articles 
                           if not regex.search(article.get(field, ''))]
    else:
        filtered_articles = [article for article in articles 
                           if regex.search(article.get(field, ''))]
    
    if log_func:
        action = "Excluded" if exclude else "Filtered"
        log_func.logger.info(f"{action} by regex pattern '{pattern}' on field '{field}': {original_count} -> {len(filtered_articles)} articles")
    
    return filtered_articles


def filter_by_date_range(articles: List[Dict[str, Any]], 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         date_field: str = 'date',
                         log_func=None) -> List[Dict[str, Any]]:
    """
    Filter articles by date range.
    
    Args:
        articles: List of article dictionaries
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        date_field: Field containing the date
        log_func: Logging function
        
    Returns:
        Filtered list of articles
    """
    from datetime import datetime
    
    if not start_date and not end_date:
        return articles
    
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        if log_func:
            log_func.logger.error(f"Invalid date format: {e}")
        return articles
    
    original_count = len(articles)
    filtered_articles = []
    
    for article in articles:
        date_str = article.get(date_field, '')
        if not date_str:
            continue
        
        try:
            # Try to parse the date - this might need adjustment based on actual date format
            article_date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
            
            # Check if article date is within range
            date_in_range = True
            if start_date and article_date < start_dt:
                date_in_range = False
            if end_date and article_date > end_dt:
                date_in_range = False
            
            if date_in_range:
                filtered_articles.append(article)
        except ValueError:
            # Skip articles with invalid date format
            continue
    
    if log_func:
        log_func.logger.info(f"Filtered by date range ({start_date} to {end_date}): {original_count} -> {len(filtered_articles)} articles")
    
    return filtered_articles