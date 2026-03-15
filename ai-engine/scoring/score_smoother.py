import config.config as config

_score_buffer = []
BUFFER_SIZE = 6


def apply_score_decay(new_score):

    global _score_buffer

    _score_buffer.append(new_score)

    if len(_score_buffer) > BUFFER_SIZE:
        _score_buffer.pop(0)

    # weighted average
    weights = list(range(1, len(_score_buffer) + 1))
    buffered = sum(s * w for s, w in zip(_score_buffer, weights)) / sum(weights)

    # smoothing
    if buffered > config.prev_score:
        smoothed = 0.75 * buffered + 0.25 * config.prev_score
    else:
        smoothed = 0.15 * buffered + 0.85 * config.prev_score

    config.prev_score = smoothed

    return smoothed