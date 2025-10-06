import os
import json
import hashlib
import time
import shutil
from typing import Dict, Any, Optional, List
from . import config

class CacheManager:
    """Manages caching of scraped content to speed up repeated downloads."""
    
    def __init__(self, log_func=None):
        """Initialize the cache manager."""
        self.log = log_func
        self.cache_dir = os.path.join(config.get_output_dir(), ".cache")
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        self.max_cache_age_days = 7  # Default cache expiration: 7 days
        self.max_cache_size_mb = 500  # Default max cache size: 500MB
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load cache metadata
        self.metadata = self._load_metadata()

    def set_cache_dir(self, output_dir: str):
        """Set the cache directory dynamically."""
        self.cache_dir = os.path.join(output_dir, ".cache")
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            if self.log:
                self.log.logger.warning(f"Failed to load cache metadata: {e}")
        
        return {"entries": {}, "created_at": time.time()}
    
    def _save_metadata(self):
        """Save cache metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if self.log:
                self.log.logger.warning(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, url: str, formats: List[str]) -> str:
        """Generate a cache key for a URL and formats."""
        # Create a hash of URL and formats for consistent cache keys
        key_data = f"{url}:{','.join(sorted(formats))}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str, format_type: str) -> str:
        """Get the file path for a cached item."""
        return os.path.join(self.cache_dir, f"{cache_key}.{format_type}")
    
    def is_cached(self, url: str, formats: List[str], content_hash: Optional[str] = None) -> bool:
        """Check if content is cached and not expired."""
        cache_key = self._get_cache_key(url, formats)
        
        if cache_key not in self.metadata["entries"]:
            return False
        
        entry = self.metadata["entries"][cache_key]
        
        # Check if cache entry is expired
        age_days = (time.time() - entry["timestamp"]) / (24 * 60 * 60)
        if age_days > self.max_cache_age_days:
            if self.log:
                self.log.logger.debug(f"Cache entry expired for {url}")
            return False
        
        # Check if content hash matches (if provided)
        if content_hash and entry.get("content_hash") != content_hash:
            if self.log:
                self.log.logger.debug(f"Content hash mismatch for {url}")
            return False
        
        # Check if all format files exist
        for format_type in formats:
            cache_path = self._get_cache_path(cache_key, format_type)
            if not os.path.exists(cache_path):
                if self.log:
                    self.log.logger.debug(f"Cache file missing for {format_type} format of {url}")
                return False
        
        return True
    
    def get_cached_content(self, url: str, formats: List[str], output_dir: str) -> Dict[str, str]:
        """Retrieve cached content and copy to output directory."""
        cache_key = self._get_cache_key(url, formats)
        entry = self.metadata["entries"][cache_key]
        
        copied_files = {}
        
        try:
            for format_type in formats:
                cache_path = self._get_cache_path(cache_key, format_type)
                
                if os.path.exists(cache_path):
                    # Determine output path based on format
                    if format_type == 'json':
                        output_path = os.path.join(config.get_json_dir(), entry['files'][format_type].split('\\')[-1])
                    elif format_type == 'pdf':
                        output_path = os.path.join(config.get_pdf_dir(), entry['files'][format_type].split('\\')[-1])
                    elif format_type == 'txt':
                        output_path = os.path.join(config.get_txt_dir(), entry['files'][format_type].split('\\')[-1])
                    elif format_type == 'markdown':
                        output_path = os.path.join(config.get_markdown_dir(), entry['files'][format_type].split('\\')[-1])
                    elif format_type == 'docx':
                        output_path = os.path.join(config.get_docx_dir(), entry['files'][format_type].split('\\')[-1])
                    else:
                        continue
                    
                    # Copy cached file to output directory
                    shutil.copy2(cache_path, output_path)
                    copied_files[format_type] = output_path
                    
                    if self.log:
                        self.log.logger.debug(f"Retrieved cached {format_type} file for {url}")
            
            # Update access time
            entry["last_accessed"] = time.time()
            self._save_metadata()
            
            return copied_files
            
        except Exception as e:
            if self.log:
                self.log.logger.error(f"Failed to retrieve cached content for {url}: {e}")
            return {}
    
    def cache_content(self, url: str, formats: List[str], files: Dict[str, str], content_hash: Optional[str] = None):
        """Cache content files."""
        cache_key = self._get_cache_key(url, formats)
        
        try:
            # Copy files to cache
            cached_files = {}
            for format_type, file_path in files.items():
                if os.path.exists(file_path):
                    cache_path = self._get_cache_path(cache_key, format_type)
                    shutil.copy2(file_path, cache_path)
                    cached_files[format_type] = cache_path
                    
                    if self.log:
                        self.log.logger.debug(f"Cached {format_type} file for {url}")
            
            # Update metadata
            self.metadata["entries"][cache_key] = {
                "url": url,
                "formats": formats,
                "timestamp": time.time(),
                "last_accessed": time.time(),
                "content_hash": content_hash,
                "files": cached_files
            }
            
            self._save_metadata()
            
            # Clean up old entries if cache is too large
            self._cleanup_cache()
            
        except Exception as e:
            if self.log:
                self.log.logger.error(f"Failed to cache content for {url}: {e}")
    
    def _cleanup_cache(self):
        """Clean up old cache entries to maintain size limits."""
        try:
            # Calculate current cache size
            total_size = 0
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file != "cache_metadata.json":
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
            
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_cache_size_mb:
                if self.log:
                    self.log.logger.info(f"Cache size ({total_size_mb:.2f}MB) exceeds limit ({self.max_cache_size_mb}MB), cleaning up")
                
                # Sort entries by last accessed time (oldest first)
                entries = list(self.metadata["entries"].items())
                entries.sort(key=lambda x: x[1].get("last_accessed", x[1].get("timestamp", 0)))
                
                # Remove oldest entries until size is acceptable
                for cache_key, entry in entries:
                    # Remove cached files
                    for format_type in entry.get("formats", []):
                        cache_path = self._get_cache_path(cache_key, format_type)
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                            total_size -= os.path.getsize(cache_path)
                    
                    # Remove metadata entry
                    del self.metadata["entries"][cache_key]
                    
                    # Check if we're under the limit now
                    current_size_mb = total_size / (1024 * 1024)
                    if current_size_mb <= self.max_cache_size_mb * 0.8:  # Leave some buffer
                        break
                
                self._save_metadata()
                
                if self.log:
                    self.log.logger.info(f"Cache cleanup completed. New size: {total_size/(1024*1024):.2f}MB")
        
        except Exception as e:
            if self.log:
                self.log.logger.warning(f"Cache cleanup failed: {e}")
    
    def clear_cache(self):
        """Clear all cached content."""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
            
            self.metadata = {"entries": {}, "created_at": time.time()}
            self._save_metadata()
            
            if self.log:
                self.log.logger.info("Cache cleared")
        
        except Exception as e:
            if self.log:
                self.log.logger.error(f"Failed to clear cache: {e}")
    
    def get_content_hash(self, url, formats=None):
        """Retrieves the content hash for a cached URL."""
        try:
            cache_key = self._get_cache_key(url, formats if formats else [])
            if cache_key in self.metadata["entries"]:
                return self.metadata["entries"][cache_key].get("content_hash")
            return None
        except Exception as e:
            if self.log:
                self.log.logger.warning(f"Failed to get content hash from cache for {url}: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Calculate cache size
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file != "cache_metadata.json":
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            # Count entries
            entry_count = len(self.metadata["entries"])
            
            # Find oldest and newest entries
            timestamps = [entry.get("timestamp", 0) for entry in self.metadata["entries"].values()]
            oldest_entry = min(timestamps) if timestamps else 0
            newest_entry = max(timestamps) if timestamps else 0
            
            return {
                "cache_dir": self.cache_dir,
                "total_size_mb": total_size / (1024 * 1024),
                "file_count": file_count,
                "entry_count": entry_count,
                "oldest_entry_time": oldest_entry,
                "newest_entry_time": newest_entry,
                "max_cache_age_days": self.max_cache_age_days,
                "max_cache_size_mb": self.max_cache_size_mb
            }
        
        except Exception as e:
            if self.log:
                self.log.logger.error(f"Failed to get cache stats: {e}")
            return {}