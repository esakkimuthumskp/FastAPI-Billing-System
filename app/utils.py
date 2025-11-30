from typing import List, Dict, Tuple

def calculate_change_bounded(denominations: List[Tuple[int,int]], change_amount: int) -> Dict[int,int]:
    """
    denominations: list of (value, available_count) ordered descending by value
    change_amount: integer amount of change to return (in same units as denominations, e.g., cents or rupees)

    Returns: dict value->count for change. If impossible, returns empty dict.

    Uses a greedy-with-backtrack strategy: greedy first, then backtracks if stuck.
    This is practical for small denomination sets.
    """

    result = {v:0 for v,_ in denominations}

    # greedy with backtracking stack
    idx = 0
    remaining = change_amount
    stack = []  # stack of (idx, used_count, remaining_before)

    while remaining > 0 and idx < len(denominations):
        val, avail = denominations[idx]
        max_use = min(avail, remaining // val)
        if max_use > 0:
            result[val] = max_use
            stack.append((idx, max_use, remaining))
            remaining -= val * max_use
            idx += 1
        else:
            result[val] = 0
            idx += 1

    if remaining == 0:
        return {k:v for k,v in result.items() if v>0}

    # backtrack
    while stack:
        idx, used, prev_remaining = stack.pop()
        val, avail = denominations[idx]
        # try to reduce usage by 1 and then continue greedily after
        if used > 0:
            used -= 1
            result[val] = used
            remaining = prev_remaining - val * used
            # continue greedily for denominations after idx
            tmp_idx = idx + 1
            tmp_res = {k:v for k,v in result.items()}
            while tmp_idx < len(denominations):
                v2, a2 = denominations[tmp_idx]
                use2 = min(a2, remaining // v2)
                tmp_res[v2] = use2
                remaining -= v2 * use2
                tmp_idx += 1
            if remaining == 0:
                return {k:v for k,v in tmp_res.items() if v>0}
            # if not solved, continue backtracking further

    return {}
