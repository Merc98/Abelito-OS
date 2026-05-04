from __future__ import annotations

import ast
import asyncio
import hashlib
import math
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOKEN_RX = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")


@dataclass
class SearchHit:
    path: str
    function_name: str
    snippet: str


class SmartSearchEngine:
    def __init__(self, root: str = ".") -> None:
        self.root = Path(root)
        self._index_mtime = 0.0
        self.docs: list[dict[str, Any]] = []
        self.inverted: dict[str, dict[int, int]] = defaultdict(dict)
        self.doc_len: dict[int, int] = {}
        self.df: dict[str, int] = {}
        self.embeddings: dict[int, list[float]] = {}

    def _iter_files(self) -> list[Path]:
        exts = {".py", ".js", ".ts", ".tsx", ".md", ".json"}
        out: list[Path] = []
        for p in self.root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts:
                continue
            if any(skip in p.parts for skip in (".git", "__pycache__", ".pytest_cache", "node_modules")):
                continue
            out.append(p)
        return out

    def _needs_reindex(self) -> bool:
        latest = 0.0
        for f in self._iter_files():
            latest = max(latest, f.stat().st_mtime)
        return latest > self._index_mtime

    def _tokenize(self, text: str) -> list[str]:
        return [t.lower() for t in TOKEN_RX.findall(text)]

    def _embed(self, text: str, dims: int = 128) -> list[float]:
        vec = [0.0] * dims
        for tok in self._tokenize(text):
            idx = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dims
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _extract_functions(self, path: Path, text: str) -> list[tuple[str, int]]:
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
                return [(n.name, n.lineno) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            except SyntaxError:
                return []
        out = []
        for idx, line in enumerate(text.splitlines(), start=1):
            m = re.search(r"function\s+([A-Za-z0-9_]+)|([A-Za-z0-9_]+)\s*=\s*\([^)]*\)\s*=>", line)
            if m:
                out.append(((m.group(1) or m.group(2) or "anonymous"), idx))
        return out

    def reindex(self) -> None:
        self.docs.clear()
        self.inverted.clear()
        self.df.clear()
        self.doc_len.clear()
        self.embeddings.clear()

        files = self._iter_files()
        for doc_id, p in enumerate(files):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            funcs = self._extract_functions(p, text) or [("<file>", 1)]
            lines = text.splitlines()
            snippet = "\n".join(lines[:5])
            self.docs.append(
                {
                    "id": doc_id,
                    "path": str(p).replace("\\", "/"),
                    "function": funcs[0][0],
                    "line": funcs[0][1],
                    "text": text,
                    "snippet": snippet,
                }
            )
            tokens = self._tokenize(text)
            tf: dict[str, int] = defaultdict(int)
            for t in tokens:
                tf[t] += 1
            self.doc_len[doc_id] = len(tokens)
            for t, cnt in tf.items():
                self.inverted[t][doc_id] = cnt
            for t in tf.keys():
                self.df[t] = self.df.get(t, 0) + 1
            self.embeddings[doc_id] = self._embed(text)

        self._index_mtime = max((f.stat().st_mtime for f in files), default=0.0)

    def _bm25(self, query: str, top_k: int = 20) -> list[int]:
        if not self.docs:
            return []
        q_tokens = self._tokenize(query)
        n_docs = len(self.docs)
        avgdl = (sum(self.doc_len.values()) / max(1, n_docs))
        k1 = 1.5
        b = 0.75
        scores: dict[int, float] = defaultdict(float)
        for t in q_tokens:
            postings = self.inverted.get(t, {})
            if not postings:
                continue
            idf = math.log(1 + (n_docs - self.df.get(t, 0) + 0.5) / (self.df.get(t, 0) + 0.5))
            for doc_id, tf in postings.items():
                dl = self.doc_len.get(doc_id, 1)
                denom = tf + k1 * (1 - b + b * dl / avgdl)
                scores[doc_id] += idf * ((tf * (k1 + 1)) / denom)
        return [doc for doc, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]]

    def _semantic(self, query: str, top_k: int = 20) -> list[int]:
        qv = self._embed(query)
        scored: list[tuple[int, float]] = []
        for doc_id, dv in self.embeddings.items():
            sim = sum(a * b for a, b in zip(qv, dv))
            scored.append((doc_id, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]

    def _rrf(self, rankings: list[list[int]], k: int = 60, top_n: int = 10) -> list[int]:
        scores: dict[int, float] = defaultdict(float)
        for ranking in rankings:
            for rank, doc_id in enumerate(ranking, start=1):
                scores[doc_id] += 1.0 / (k + rank)
        return [doc for doc, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    async def smart_search(self, query: str, mode: str = "auto") -> list[SearchHit]:
        if self._needs_reindex() or not self.docs:
            self.reindex()

        if mode == "keyword":
            doc_ids = self._bm25(query)
        elif mode == "semantic":
            doc_ids = self._semantic(query)
        else:
            bm25_task = asyncio.to_thread(self._bm25, query)
            sem_task = asyncio.to_thread(self._semantic, query)
            bm25_ids, sem_ids = await asyncio.gather(bm25_task, sem_task)
            doc_ids = self._rrf([bm25_ids, sem_ids], k=60)

        hits: list[SearchHit] = []
        for did in doc_ids:
            d = self.docs[did]
            hits.append(SearchHit(path=d["path"], function_name=d["function"], snippet=d["snippet"]))
        return hits
