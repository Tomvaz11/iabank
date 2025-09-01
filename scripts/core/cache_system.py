#!/usr/bin/env python3
"""
CacheSystem - Sistema de cache inteligente para AGV v5.0.
Implementa cache em memória e disco para otimizar performance em projetos grandes.
"""

import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from functools import wraps
import threading

from .logging_config import get_logger
from .exceptions import AGVException, ErrorContext


logger = get_logger("cache")


@dataclass
class CacheEntry:
    """Entrada de cache com metadados."""
    key: str
    value: Any
    timestamp: float
    ttl: Optional[float] = None
    access_count: int = 0
    size_bytes: int = 0
    tags: Optional[list] = None
    
    @property
    def is_expired(self) -> bool:
        """Verifica se entrada expirou."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age_seconds(self) -> float:
        """Idade da entrada em segundos."""
        return time.time() - self.timestamp


class CacheStats:
    """Estatísticas do cache."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.start_time = time.time()
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acerto do cache."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
    
    @property
    def uptime_seconds(self) -> float:
        """Tempo de funcionamento em segundos."""
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'hit_rate': self.hit_rate,
            'uptime_seconds': self.uptime_seconds
        }


class MemoryCache:
    """Cache em memória thread-safe com LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = threading.RLock()
        
        logger.info(
            "Memory cache initialized",
            extra={
                'context': {
                    'max_size': max_size,
                    'default_ttl': default_ttl
                }
            }
        )
    
    def _cleanup_expired(self):
        """Remove entradas expiradas."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1
        
        if expired_keys:
            logger.debug(
                f"Cleaned up {len(expired_keys)} expired cache entries",
                extra={'context': {'expired_count': len(expired_keys)}}
            )
    
    def _evict_lru(self):
        """Remove entrada menos recentemente usada."""
        if not self._cache:
            return
        
        # Encontrar entrada com menor access_count e mais antiga
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].access_count, self._cache[k].timestamp)
        )
        
        del self._cache[lru_key]
        self._stats.evictions += 1
        
        logger.debug(
            f"Evicted LRU cache entry: {lru_key}",
            extra={'context': {'evicted_key': lru_key}}
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache."""
        with self._lock:
            self._cleanup_expired()
            
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                return None
            
            entry.access_count += 1
            self._stats.hits += 1
            
            logger.debug(
                f"Cache hit: {key}",
                extra={
                    'context': {
                        'key': key,
                        'age_seconds': entry.age_seconds,
                        'access_count': entry.access_count
                    }
                }
            )
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Armazena valor no cache."""
        with self._lock:
            self._cleanup_expired()
            
            # Usar TTL padrão se não especificado
            if ttl is None:
                ttl = self.default_ttl
            
            # Calcular tamanho aproximado
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 0
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            # Evict if needed
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            self._cache[key] = entry
            self._stats.sets += 1
            
            logger.debug(
                f"Cache set: {key}",
                extra={
                    'context': {
                        'key': key,
                        'ttl': ttl,
                        'size_bytes': size_bytes
                    }
                }
            )
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                logger.debug(f"Cache delete: {key}")
                return True
            return False
    
    def clear(self):
        """Limpa todo o cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")
    
    def get_stats(self) -> CacheStats:
        """Retorna estatísticas do cache."""
        return self._stats
    
    def get_size(self) -> int:
        """Retorna número de entradas no cache."""
        with self._lock:
            return len(self._cache)


class DiskCache:
    """Cache persistente em disco."""
    
    def __init__(self, cache_dir: Union[str, Path] = ".agv_cache", max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(exist_ok=True)
        
        # Arquivo de metadados
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(
            "Disk cache initialized",
            extra={
                'context': {
                    'cache_dir': str(self.cache_dir),
                    'max_size_mb': max_size_mb
                }
            }
        )
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Carrega metadados do disco."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Salva metadados no disco."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_file(self, key: str) -> Path:
        """Obtém caminho do arquivo de cache."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _cleanup_expired(self):
        """Remove arquivos expirados."""
        current_time = time.time()
        expired_keys = []
        
        for key, meta in self.metadata.items():
            if meta.get('ttl') and current_time - meta['timestamp'] > meta['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._delete_cache_file(key)
    
    def _delete_cache_file(self, key: str):
        """Remove arquivo de cache."""
        cache_file = self._get_cache_file(key)
        try:
            if cache_file.exists():
                cache_file.unlink()
            if key in self.metadata:
                del self.metadata[key]
            self._save_metadata()
        except Exception as e:
            logger.error(f"Failed to delete cache file {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache em disco."""
        self._cleanup_expired()
        
        if key not in self.metadata:
            return None
        
        meta = self.metadata[key]
        if meta.get('ttl') and time.time() - meta['timestamp'] > meta['ttl']:
            self._delete_cache_file(key)
            return None
        
        cache_file = self._get_cache_file(key)
        if not cache_file.exists():
            # Metadata inconsistente
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                value = pickle.load(f)
            
            # Atualizar contadores
            meta['access_count'] = meta.get('access_count', 0) + 1
            self._save_metadata()
            
            logger.debug(f"Disk cache hit: {key}")
            return value
        
        except Exception as e:
            logger.error(f"Failed to load from disk cache {key}: {e}")
            self._delete_cache_file(key)
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Armazena valor no cache em disco."""
        cache_file = self._get_cache_file(key)
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            # Atualizar metadados
            self.metadata[key] = {
                'timestamp': time.time(),
                'ttl': ttl,
                'size_bytes': cache_file.stat().st_size,
                'access_count': 0
            }
            
            self._save_metadata()
            logger.debug(f"Disk cache set: {key}")
            
        except Exception as e:
            logger.error(f"Failed to save to disk cache {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache em disco."""
        if key in self.metadata:
            self._delete_cache_file(key)
            return True
        return False
    
    def clear(self):
        """Limpa todo o cache em disco."""
        for key in list(self.metadata.keys()):
            self._delete_cache_file(key)
    
    def get_size_mb(self) -> float:
        """Retorna tamanho do cache em MB."""
        total_bytes = sum(
            meta.get('size_bytes', 0) 
            for meta in self.metadata.values()
        )
        return total_bytes / (1024 * 1024)


class AGVCache:
    """Sistema de cache híbrido (memória + disco)."""
    
    def __init__(
        self,
        memory_max_size: int = 1000,
        memory_ttl: Optional[float] = 3600,  # 1 hora
        disk_max_size_mb: int = 100,
        cache_dir: Union[str, Path] = ".agv_cache"
    ):
        self.memory_cache = MemoryCache(memory_max_size, memory_ttl)
        self.disk_cache = DiskCache(cache_dir, disk_max_size_mb)
        
        logger.info(
            "AGV Cache system initialized",
            extra={
                'context': {
                    'memory_max_size': memory_max_size,
                    'memory_ttl': memory_ttl,
                    'disk_max_size_mb': disk_max_size_mb
                }
            }
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor - primeiro memória, depois disco."""
        # Tentar memória primeiro
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Tentar disco
        value = self.disk_cache.get(key)
        if value is not None:
            # Promover para memória
            self.memory_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, memory_ttl: Optional[float] = None, 
            disk_ttl: Optional[float] = None, disk_only: bool = False) -> None:
        """Armazena valor em memória e/ou disco."""
        if not disk_only:
            self.memory_cache.set(key, value, memory_ttl)
        
        # Salvar no disco para persistência
        self.disk_cache.set(key, value, disk_ttl)
    
    def delete(self, key: str) -> bool:
        """Remove de memória e disco."""
        memory_deleted = self.memory_cache.delete(key)
        disk_deleted = self.disk_cache.delete(key)
        return memory_deleted or disk_deleted
    
    def clear(self):
        """Limpa ambos os caches."""
        self.memory_cache.clear()
        self.disk_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas combinadas."""
        memory_stats = self.memory_cache.get_stats().to_dict()
        disk_size_mb = self.disk_cache.get_size_mb()
        
        return {
            'memory': memory_stats,
            'disk': {
                'size_mb': disk_size_mb,
                'entries': len(self.disk_cache.metadata)
            }
        }


# Instância global do cache
_global_cache: Optional[AGVCache] = None


def get_cache() -> AGVCache:
    """Obtém instância global do cache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AGVCache()
    return _global_cache


def cached(
    key_func: Optional[Callable] = None,
    ttl: Optional[float] = None,
    disk_only: bool = False
):
    """
    Decorator para cache de funções.
    
    Args:
        key_func: Função para gerar chave do cache
        ttl: Time to live em segundos
        disk_only: Se True, armazena apenas em disco
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Gerar chave do cache
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Chave padrão baseada na função e argumentos
                args_str = str(args) + str(sorted(kwargs.items()))
                key = f"{func.__module__}.{func.__name__}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Tentar recuperar do cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Function cache hit: {func.__name__}")
                return result
            
            # Executar função e cachear resultado
            logger.debug(f"Function cache miss: {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(key, result, memory_ttl=ttl, disk_ttl=ttl, disk_only=disk_only)
            
            return result
        
        return wrapper
    return decorator


# Exemplo de uso
if __name__ == "__main__":
    # Testar cache
    cache = get_cache()
    
    # Teste básico
    cache.set("test_key", {"data": "test_value"}, memory_ttl=60)
    result = cache.get("test_key")
    print(f"Cache test result: {result}")
    
    # Teste com decorator
    @cached(ttl=300)
    def expensive_operation(n: int) -> int:
        """Simula operação cara."""
        print(f"Executing expensive operation with n={n}")
        time.sleep(0.1)  # Simular trabalho
        return n * n
    
    # Primeira chamada - cache miss
    result1 = expensive_operation(5)
    
    # Segunda chamada - cache hit
    result2 = expensive_operation(5)
    
    print(f"Results: {result1}, {result2}")
    
    # Estatísticas
    stats = cache.get_stats()
    print(f"Cache stats: {json.dumps(stats, indent=2)}")