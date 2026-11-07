"""FP32 ONNX Runtime embedder for all-MiniLM-L6-v2, without PyTorch.

The ONNX graph and tokenizer are the official export of the same Hugging Face
revision used to build data/embeddings/vectors.npy. Mean-token pooling and L2
normalisation reproduce SentenceTransformer.encode(normalize_embeddings=True),
so the existing 152 Chroma vectors and cosine retrieval are unchanged.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import numpy as np

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

SUPPORTED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_DIR = ROOT / "models"
EMBEDDING_DIMENSION = 384
MAX_SEQ_LENGTH = 256

_EMBEDDER: "OnnxEmbedder | None" = None
_LOCK = threading.Lock()


class OnnxEmbedder:
    """Small drop-in replacement for the query-time SentenceTransformer call."""

    def __init__(self, model_dir: Path) -> None:
        model_path = model_dir / "model.onnx"
        tokenizer_path = model_dir / "tokenizer.json"
        missing = [str(path) for path in (model_path, tokenizer_path) if not path.exists()]
        if missing:
            raise RuntimeError(
                "ONNX model files are missing: "
                f"{', '.join(missing)}. Run "
                "`python scripts/fetch_onnx_model.py` (Render does this at build time)."
            )

        import onnxruntime as ort
        from tokenizers import Tokenizer

        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self._tokenizer.enable_truncation(max_length=MAX_SEQ_LENGTH)
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", pad_type_id=0)

        options = ort.SessionOptions()
        options.log_severity_level = 3
        # Render Free has 0.1 vCPU; one thread avoids oversubscription.
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(
            str(model_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

    def encode(
        self,
        sentences: list[str] | str,
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = False,
        **_: object,
    ) -> np.ndarray:
        if isinstance(sentences, str):
            sentences = [sentences]
        texts = [str(text) for text in sentences]
        if not texts:
            return np.zeros((0, EMBEDDING_DIMENSION), dtype=np.float32)

        vectors: list[np.ndarray] = []
        for start in range(0, len(texts), max(1, batch_size)):
            batch = texts[start : start + max(1, batch_size)]
            encoded = self._tokenizer.encode_batch(batch)
            length = max(len(item.ids) for item in encoded)

            input_ids = np.zeros((len(encoded), length), dtype=np.int64)
            attention_mask = np.zeros((len(encoded), length), dtype=np.int64)
            for row, item in enumerate(encoded):
                input_ids[row, : len(item.ids)] = item.ids
                attention_mask[row, : len(item.ids)] = item.attention_mask

            hidden = self._session.run(
                None,
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": np.zeros_like(input_ids),
                },
            )[0]

            mask = attention_mask[:, :, None].astype(np.float32)
            pooled = (hidden * mask).sum(axis=1) / np.clip(mask.sum(axis=1), 1e-9, None)
            if normalize_embeddings:
                pooled = pooled / np.clip(
                    np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None
                )
            vectors.append(pooled.astype(np.float32))

        result = np.vstack(vectors)
        if result.shape[1] != EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"unexpected embedding dimension {result.shape[1]}, "
                f"expected {EMBEDDING_DIMENSION}"
            )
        return result


def get_onnx_embedder(model_name: str = SUPPORTED_MODEL) -> OnnxEmbedder:
    """Return the process-wide embedder, loading it once."""
    global _EMBEDDER
    if model_name != SUPPORTED_MODEL:
        raise RuntimeError(
            f"ONNX runtime only supports {SUPPORTED_MODEL!r}, got {model_name!r}. "
            "Revert config.yaml or add a matching ONNX export."
        )
    if _EMBEDDER is None:
        with _LOCK:
            if _EMBEDDER is None:
                model_dir = Path(os.getenv("ONNX_MODEL_DIR") or DEFAULT_MODEL_DIR)
                _EMBEDDER = OnnxEmbedder(model_dir)
    return _EMBEDDER
