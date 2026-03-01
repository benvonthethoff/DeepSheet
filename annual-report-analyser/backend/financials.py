def analyze_revenue(derived: list[dict]) -> dict:
    results = []
    for i, year_data in enumerate(derived):
        year = year_data["year"]
        growth = year_data.get("revenueGrowthPct")
        flags = []
        interpretation = None
        confidence = "high"

        if growth is None:
            results.append({
                "year": year,
                "flags": [],
                "interpretation": None,
                "confidence": "low",
                "gap": "Insufficient data for first year"
            })
            continue

        if growth > 10:
            flags.append("accelerating")
        elif growth >= 0:
            flags.append("stable")
        else:
            flags.append("declining")

        # Check consecutive declines
        if i >= 2:
            prev_growth = derived[i-1].get("revenueGrowthPct")
            prev_prev_growth = derived[i-2].get("revenueGrowthPct")
            if growth < 0 and prev_growth and prev_growth < 0:
                flags.append("consecutive_declines")

        # Check decelerating momentum
        if i >= 3:
            growths = [derived[j].get("revenueGrowthPct") for j in range(i-2, i+1)]
            if all(g is not None for g in growths):
                if growths[0] > growths[1] > growths[2]:
                    flags.append("decelerating_3yr")

        results.append({
            "year": year,
            "figure": year_data.get("revenueGrowthPct"),
            "flags": flags,
            "confidence": confidence,
            "gap": None
        })
    return {"revenueSignals": results}


def analyze_margins(derived: list[dict]) -> dict:
    results = []
    for i, year_data in enumerate(derived):
        year = year_data["year"]
        margin = year_data.get("grossMarginPct")
        growth = year_data.get("revenueGrowthPct")
        flags = []
        confidence = "high"

        if margin is None:
            results.append({
                "year": year,
                "flags": [],
                "interpretation": None,
                "confidence": "low",
                "gap": "Gross margin data unavailable"
            })
            continue

        if i > 0:
            prev_margin = derived[i-1].get("grossMarginPct")
            if prev_margin:
                if margin > prev_margin:
                    flags.append("expanding")
                    if growth is not None and growth < 0:
                        flags.append("expanding_during_revenue_decline")
                else:
                    flags.append("compressing")
                    if growth is not None and growth > 0:
                        flags.append("compressing_during_revenue_growth")

        results.append({
            "year": year,
            "figure": margin,
            "flags": flags,
            "confidence": confidence,
            "gap": None
        })
    return {"marginSignals": results}


def analyze_fcf(derived: list[dict]) -> dict:
    results = []
    for i, year_data in enumerate(derived):
        year = year_data["year"]
        fcf = year_data.get("fcf")
        flags = []
        confidence = "high"

        if fcf is None:
            results.append({
                "year": year,
                "flags": [],
                "interpretation": None,
                "confidence": "low",
                "gap": "FCF data unavailable"
            })
            continue

        # Get net income from raw financials if available
        net_income = year_data.get("netIncome")
        if net_income:
            if fcf > net_income:
                flags.append("fcf_exceeds_net_income")
            else:
                flags.append("fcf_below_net_income")

        if i > 0:
            prev_fcf = derived[i-1].get("fcf")
            prev_net_income = derived[i-1].get("netIncome")
            if prev_fcf:
                fcf_growth = ((fcf - prev_fcf) / abs(prev_fcf)) * 100
                if prev_net_income and net_income:
                    ni_growth = ((net_income - prev_net_income) / abs(prev_net_income)) * 100
                    if fcf_growth < ni_growth - 5:
                        flags.append("fcf_declining_faster_than_net_income")

        results.append({
            "year": year,
            "figure": fcf,
            "flags": flags,
            "confidence": confidence,
            "gap": None
        })
    return {"fcfSignals": results}


def analyze_earnings_quality(derived: list[dict]) -> dict:
    results = []
    for i, year_data in enumerate(derived):
        year = year_data["year"]
        fcf = year_data.get("fcf")
        net_income = year_data.get("netIncome")
        flags = []
        confidence = "high"

        if fcf is None or net_income is None:
            results.append({
                "year": year,
                "flags": [],
                "confidence": "low",
                "gap": "Insufficient data for earnings quality analysis"
            })
            continue

        if fcf > net_income:
            flags.append("high_earnings_quality")
        elif fcf < net_income * 0.75:
            flags.append("low_earnings_quality")
        else:
            flags.append("medium_earnings_quality")

        results.append({
            "year": year,
            "fcf": fcf,
            "netIncome": net_income,
            "flags": flags,
            "confidence": confidence,
            "gap": None
        })
    return {"earningsQualitySignals": results}


def analyze_five_year_trends(derived: list[dict]) -> dict:
    """
    Looks across all 5 years to identify structural trends
    rather than just YoY movements.
    """
    years = [d["year"] for d in derived]
    revenues = [d.get("revenueGrowthPct") for d in derived]
    margins = [d.get("grossMarginPct") for d in derived]
    fcfs = [d.get("fcf") for d in derived]
    net_incomes = [d.get("netIncome") for d in derived]

    # --- Revenue shape ---
    valid_revenues = [r for r in revenues if r is not None]
    declining_count = sum(1 for r in valid_revenues if r < 0)
    accelerating_count = sum(1 for r in valid_revenues if r > 10)

    if declining_count >= 3:
        revenue_shape = "structurally_declining"
    elif declining_count == 2:
        revenue_shape = "deteriorating"
    elif declining_count == 1:
        revenue_shape = "stable_with_one_off_decline"
    else:
        revenue_shape = "stable"

    if accelerating_count >= 3:
        revenue_shape = "consistently_accelerating"

    # Check if trend is improving or worsening over the period
    if len(valid_revenues) >= 3:
        first_half = valid_revenues[:len(valid_revenues)//2]
        second_half = valid_revenues[len(valid_revenues)//2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        revenue_direction = "improving" if avg_second > avg_first else "worsening"
    else:
        revenue_direction = None

    # --- Margin shape ---
    valid_margins = [m for m in margins if m is not None]
    if len(valid_margins) >= 2:
        margin_expanding_count = sum(
            1 for i in range(1, len(valid_margins))
            if valid_margins[i] > valid_margins[i-1]
        )
        if margin_expanding_count == len(valid_margins) - 1:
            margin_shape = "consistently_expanding"
        elif margin_expanding_count >= len(valid_margins) * 0.6:
            margin_shape = "mostly_expanding"
        elif margin_expanding_count <= len(valid_margins) * 0.3:
            margin_shape = "mostly_compressing"
        else:
            margin_shape = "volatile"

        margin_total_change = round(valid_margins[-1] - valid_margins[0], 1)
    else:
        margin_shape = None
        margin_total_change = None

    # --- FCF shape ---
    valid_fcfs = [f for f in fcfs if f is not None]
    if len(valid_fcfs) >= 2:
        fcf_expanding_count = sum(
            1 for i in range(1, len(valid_fcfs))
            if valid_fcfs[i] > valid_fcfs[i-1]
        )
        if fcf_expanding_count == len(valid_fcfs) - 1:
            fcf_shape = "consistently_growing"
        elif fcf_expanding_count >= len(valid_fcfs) * 0.6:
            fcf_shape = "mostly_growing"
        elif fcf_expanding_count <= len(valid_fcfs) * 0.3:
            fcf_shape = "declining"
        else:
            fcf_shape = "volatile"

        fcf_total_change = round(
            ((valid_fcfs[-1] - valid_fcfs[0]) / abs(valid_fcfs[0])) * 100, 1
        )
    else:
        fcf_shape = None
        fcf_total_change = None

    # --- Earnings quality trend ---
    quality_scores = []
    for fcf, ni in zip(fcfs, net_incomes):
        if fcf is not None and ni is not None and ni != 0:
            quality_scores.append(fcf / ni)

    if len(quality_scores) >= 2:
        if quality_scores[-1] > quality_scores[0]:
            earnings_quality_trend = "improving"
        elif quality_scores[-1] < quality_scores[0]:
            earnings_quality_trend = "deteriorating"
        else:
            earnings_quality_trend = "stable"
        avg_quality = round(sum(quality_scores) / len(quality_scores), 2)
    else:
        earnings_quality_trend = None
        avg_quality = None

    # --- Cross metric signals ---
    cross_signals = []
    if margin_shape in ["consistently_expanding", "mostly_expanding"] and revenue_shape in ["structurally_declining", "deteriorating"]:
        cross_signals.append("margin_expansion_masking_revenue_weakness")
    if fcf_shape in ["declining", "volatile"] and margin_shape in ["consistently_expanding", "mostly_expanding"]:
        cross_signals.append("margins_improving_but_cash_not_following")
    if earnings_quality_trend == "deteriorating" and revenue_shape in ["stable", "consistently_accelerating"]:
        cross_signals.append("growth_consuming_cash_quality_declining")

    return {
        "fiveYearTrend": {
            "years": years,
            "revenue": {
                "shape": revenue_shape,
                "direction": revenue_direction,
                "confidence": "high" if len(valid_revenues) >= 4 else "medium"
            },
            "margins": {
                "shape": margin_shape,
                "totalChangepp": margin_total_change,
                "confidence": "high" if len(valid_margins) >= 4 else "medium"
            },
            "fcf": {
                "shape": fcf_shape,
                "totalChangePct": fcf_total_change,
                "confidence": "high" if len(valid_fcfs) >= 4 else "medium"
            },
            "earningsQuality": {
                "trend": earnings_quality_trend,
                "averageRatio": avg_quality,
                "confidence": "high" if len(quality_scores) >= 4 else "medium"
            },
            "crossMetricSignals": cross_signals
        }
    }


def run_rules_engine(derived: list[dict], financials: dict) -> dict:
    net_income_by_year = {
        entry["year"]: entry["val"]
        for entry in financials.get("NetIncomeLoss", [])
        if entry["val"] is not None
    }
    for entry in derived:
        entry["netIncome"] = net_income_by_year.get(entry["year"])

    return {
        **analyze_revenue(derived),
        **analyze_margins(derived),
        **analyze_fcf(derived),
        **analyze_earnings_quality(derived),
        **analyze_five_year_trends(derived),
    }
