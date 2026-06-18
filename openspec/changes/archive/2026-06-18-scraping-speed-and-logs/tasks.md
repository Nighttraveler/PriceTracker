## 1. Normalizer: preload catalog and add stats

- [x] 1.1 Add `self._productos`, `self._cache_hits`, `self._cache_misses`, `self._new_products` fields in `Normalizer.__init__`, loading the catalog with `db.get_all_productos()`
- [x] 1.2 Replace `productos = self.db.get_all_productos()` inside `get_or_create_product` with `self._productos`
- [x] 1.3 Increment `self._cache_hits` on cache hit and `self._cache_misses` on cache miss
- [x] 1.4 Append the new product dict to `self._productos` and increment `self._new_products` when a product is created
- [x] 1.5 Add `stats()` method returning `{"cache_hits": ..., "cache_misses": ..., "new_products": ...}`

## 2. tracker.py: progress and summary logs

- [x] 2.1 Record `save_start = time.monotonic()` before the save loop and snapshot normalizer stats before the loop starts
- [x] 2.2 Inside the save loop, after incrementing `inserted`, emit an INFO log every 1000 products: count, elapsed, rate (products/sec), ETA
- [x] 2.3 After the save loop, compute per-source normalizer stat deltas (current stats minus pre-loop snapshot) and log them together with total save duration
