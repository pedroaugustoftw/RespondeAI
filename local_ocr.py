"""OCR executado no computador; nenhuma imagem é enviada por este módulo."""
from dataclasses import dataclass
from threading import Lock

import cv2
import numpy as np

OCR_VERSION = 'latin-v5-layout-1'
_engine = None
_lock = Lock()


@dataclass
class CaptureText:
    text: str
    figure: bytes | None = None


def figure_region(image, boxes):
    """Heurística local: procura conteúdo visual grande fora das linhas de texto.

    Não é uma classificação semântica: modos manuais corrigem falsos positivos
    (elementos da página) e falsos negativos (figuras muito pequenas).
    """
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 150)
    heights = []
    for box in boxes:
        points = np.asarray(box, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(points)
        heights.append(h)
        # Inclui antialiasing e pequenas bordas das letras.
        edges[max(0, y-4):min(height, y+h+4), max(0, x-4):min(width, x+w+4)] = 0
    edges[:5, :] = edges[-5:, :] = 0
    edges[:, :5] = edges[:, -5:] = 0
    merged = cv2.dilate(edges, np.ones((7, 7), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(merged)
    line_height = float(np.median(heights)) if heights else 20
    regions = []
    for x, y, w, h, area in stats[1:]:
        if w < 45 or h < max(40, line_height * 2.2):
            continue
        if w*h < max(2500, width*height*.006):
            continue
        # Bordas de cartões/caixas e linhas longas não são figuras.
        interior = edges[y+8:y+h-8, x+8:x+w-8]
        if interior.size == 0 or np.count_nonzero(interior) < 100:
            continue
        regions.append((x, y, x+w, y+h))
    if not regions:
        return None
    x1 = max(0, min(r[0] for r in regions)-18)
    y1 = max(0, min(r[1] for r in regions)-18)
    x2 = min(width, max(r[2] for r in regions)+18)
    y2 = min(height, max(r[3] for r in regions)+18)
    return image[y1:y2, x1:x2]


def read_capture(png, mode='auto'):
    global _engine
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Não foi possível ler a captura.')
    with _lock:
        if _engine is None:
            from rapidocr import RapidOCR, LangRec, OCRVersion, ModelType
            _engine = RapidOCR(params={
                'Rec.lang_type': LangRec.LATIN,
                'Rec.ocr_version': OCRVersion.PPOCRV5,
                'Rec.model_type': ModelType.MOBILE,
                'Global.log_level': 'warning',
            })
        result = _engine(image)
    lines = []
    for text, score in zip(result.txts or (), result.scores or ()):
        lines.append(text if score >= .6 else '[trecho ilegível]')
    text = '\n'.join(lines).strip()
    boxes = result.boxes if result.boxes is not None else []
    region = image if mode == 'figure' else figure_region(image, boxes) if mode == 'auto' else None
    figure = None
    if region is not None:
        ok, encoded = cv2.imencode('.png', region)
        if ok:
            figure = encoded.tobytes()
    if not text and figure is None:
        raise ValueError('O OCR local não encontrou texto legível. Amplie a pergunta e capture novamente; nenhuma imagem foi enviada.')
    return CaptureText(text, figure)
