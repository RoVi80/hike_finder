import math
import logging

logger = logging.getLogger(__name__)


def format_hike_time(minutes: int) -> str:
    try:
        minutes = int(float(minutes))
    except (ValueError, TypeError):
        return None
    
    minutes = int(math.ceil(minutes / 5.0) * 5)
    hours = minutes // 60
    mins = minutes % 60

    if hours and mins:
        return f"{hours} h {mins} min"
    elif hours:
        return f"{hours} h"
    else:
        return f"{mins} min"

def percentage_dict(values):
    logger.debug(f"[percent] Raw input: {values}")

    if not values or isinstance(values, str) or not hasattr(values, '__iter__'):
        logger.debug("[percent] Input is invalid or not iterable.")
        return {}

    filtered = [str(v).strip() for v in values if str(v).strip()]
    if not filtered:
        logger.debug("[percent] No valid items after filtering.")
        return {}

    total = len(filtered)
    counts = {v: filtered.count(v) for v in set(filtered)}
    percentages = {k: round((v / total) * 100, 1) for k, v in counts.items()}
    logger.debug(f"[percent] Final percentages: {percentages}")
    return percentages
