"""Estimate Bresnahan-Reiss (1991) entry thresholds for isolated American towns, 2016 and 2000.

For each industry the number of establishments in a town, N = 0, 1, ..., K-1 or K-or-more, is
modeled with the paper's ordered probit. The Nth firm's profit is

    Pi_N = S * V_N - F_N + e,   S = town population + lam * hinterland population (thousands)
    V_N  = a_1 + X b - (a_2 + ... + a_N)      variable profit per resident
    F_N  = g_1 + (g_2 + ... + g_N)            fixed cost

with e standard normal and a_n, g_n >= 0, so later entrants earn less per resident and may face
higher fixed costs. The entry threshold is S_N = F_N / V_N at the sample mean of X, and the
paper's statistic is the ratio of per-firm thresholds s_{N+1} / s_N, where s_N = S_N / N.

2016 is the replication; 2000 is the extension (same towns, same model). Confidence intervals
come from a bootstrap over towns that resamples the same towns in both years, so the change in
each threshold between 2000 and 2016 gets its own interval.

Usage (from the repository root, after src/build_markets.py):
    python src/entry_thresholds.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.special import log_ndtr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

INDUSTRIES = ["doctors", "dentists", "druggists", "plumbers", "tire_dealers"]
LABELS = {"doctors": "Doctors", "dentists": "Dentists", "druggists": "Druggists (drugstores)",
          "plumbers": "Plumbers", "tire_dealers": "Tire dealers"}
# The paper put births (and elderly share) in doctors' and dentists' profit functions; I add
# births for drugstores as well, as a health-care demand shifter.
HEALTH = {"doctors", "dentists", "druggists"}
MIN_TOWN_POP = 120      # smallest town in the paper's sample (Table 3: TPOP min .12 thousand)
MAX_CLASS = 5           # the paper's residual category is "five or more firms"
MIN_PER_CLASS = 10      # the paper dropped industries with fewer than 10 towns in a size class
LAMBDA_BOUNDS = (0.0, 3.0)  # hinterland residents count between zero and three town residents
N_BOOT = 200
SEED = 1991
ISOLATION_CHECK_MILES = (20, 25, 30)  # the paper's robustness check moved the 20-mile rule to 40
# Towns the README discusses by name; their counts are written to featured_towns.csv.
FEATURED = [("Lamar city", "CO"), ("Miles City city", "MT"), ("Havre city", "MT"),
            ("Sidney city", "NE"), ("Ely city", "NV"), ("Algona city", "IA"), ("Dillon city", "MT")]

# Bresnahan and Reiss (1991), Table 5, part A: entry thresholds (thousands) S1..S5.
PAPER_TABLE5 = {
    "doctors": [0.88, 3.49, 5.78, 7.72, 9.14],
    "dentists": [0.71, 2.54, 4.18, 5.43, 6.41],
    "druggists": [0.53, 2.12, 5.04, 7.67, 9.39],
    "plumbers": [1.43, 3.02, 4.53, 6.20, 7.47],
    "tire_dealers": [0.49, 1.78, 3.41, 4.74, 6.10],
}
PAPER_RATIOS = {  # Table 5, part A: s2/s1, s3/s2, s4/s3, s5/s4 as printed
    "doctors": [1.98, 1.10, 1.00, 0.95],
    "dentists": [1.78, 0.79, 0.97, 0.94],
    "druggists": [1.99, 1.58, 1.14, 0.98],
    "plumbers": [1.06, 1.00, 1.02, 0.96],
    "tire_dealers": [1.81, 1.28, 1.04, 1.03],
}


def design(m, ind, yr):
    """Outcome, market-size inputs and demeaned profit shifters for one industry and year."""
    n = m[f"{ind}{yr}"].to_numpy()
    tpop = m[f"tpop{yr}"].to_numpy() / 1000
    opop = m[f"opop{yr}"].to_numpy() / 1000
    cols = [m[f"pinc{yr}"].to_numpy()]  # per capita income, $ thousands
    if ind in HEALTH:
        cols.append(100 * m[f"births{yr}"].to_numpy())  # births per 100 county residents
    X = np.column_stack(cols)
    return n, tpop, opop, X - X.mean(axis=0)


def unpack(theta, K, p):
    lam, b = theta[0], theta[1:1 + p]
    a = theta[1 + p:1 + p + K]
    g = theta[1 + p + K:1 + p + 2 * K]
    return lam, b, a, g


def profits(theta, K, p, tpop, opop, X, prop_from=None):
    """Pi_1..Pi_K for every town (towns x K). prop_from=m imposes s_m = ... = s_K."""
    lam, b, a, g = unpack(theta, K, p)
    S = tpop + lam * opop
    V = a[0] + (X @ b)[:, None] - np.concatenate([[0.0], np.cumsum(a[1:])])[None, :]
    F = g[0] + np.concatenate([[0.0], np.cumsum(g[1:])])
    if prop_from is not None:
        Vbar = a[0] - np.concatenate([[0.0], np.cumsum(a[1:])])
        mm = prop_from - 1
        for j in range(prop_from, K):
            F[j] = (j + 1) / prop_from * F[mm] * Vbar[j] / Vbar[mm]
    return S[:, None] * V - F[None, :]


def log_interval_prob(upper, lower):
    """log(Phi(upper) - Phi(lower)) for upper >= lower, computed on the more precise tail."""
    upper, lower = np.maximum(upper, lower), lower
    flip = lower > 0
    hi = np.where(flip, -lower, upper)
    lo = np.where(flip, -upper, lower)
    lhi, llo = log_ndtr(hi), log_ndtr(lo)
    return lhi + np.log1p(-np.exp(np.minimum(llo - lhi, -1e-15)))


def negloglik(theta, K, p, n, tpop, opop, X, prop_from=None):
    """Minus the log likelihood of the observed counts (N >= K pooled into the top class)."""
    pi = profits(theta, K, p, tpop, opop, X, prop_from)
    big = 1e6
    upper = np.column_stack([np.full(len(n), big), pi])   # N firms needs Pi_N > 0 ...
    lower = np.column_stack([pi, np.full(len(n), -big)])  # ... and Pi_{N+1} < 0
    k = np.minimum(n, K)
    rows = np.arange(len(n))
    return -log_interval_prob(upper[rows, k], lower[rows, k]).sum()


def start_values(n, tpop, K, p, scale):
    """Starting point: thresholds near the populations of towns that have N firms."""
    guess = [np.percentile(tpop[n >= j], 25) if (n >= j).sum() else j for j in range(1, K + 1)]
    guess = np.maximum.accumulate(np.maximum(guess, 0.05))
    F = scale * guess  # with V_N = scale, S_N = guess
    return np.r_[0.5, np.zeros(p), scale, np.zeros(K - 1), F[0], np.diff(F)]


def fit(n, tpop, opop, X, K, prop_from=None, start=None):
    """Maximum likelihood under the bounds; tries several starting points unless given one."""
    p = X.shape[1]
    starts = [start] if start is not None else [start_values(n, tpop, K, p, c)
                                                for c in (0.5, 1.0, 2.0, 4.0)]
    bounds = ([LAMBDA_BOUNDS] + [(None, None)] * p + [(1e-4, None)] + [(0, None)] * (K - 1)
              + [(0, None)] * K)
    if prop_from is not None:  # the fixed-cost steps above m are implied, so pin them at zero
        bounds = bounds[:1 + p + K + prop_from] + [(0, 0)] * (K - prop_from)
    best = None
    for x0 in starts:
        x0 = np.clip(x0, [b[0] if b[0] is not None else -np.inf for b in bounds],
                     [b[1] if b[1] is not None else np.inf for b in bounds])
        res = optimize.minimize(negloglik, x0, args=(K, p, n, tpop, opop, X, prop_from),
                                method="L-BFGS-B", bounds=bounds,
                                options={"maxiter": 10000, "maxfun": 50000})
        if best is None or res.fun < best.fun:
            best = res
    return best


def thresholds(theta, K, p, prop_from=None):
    """S_1..S_K at the sample mean of X (X is demeaned, so X = 0)."""
    lam, b, a, g = unpack(theta, K, p)
    V = a[0] - np.concatenate([[0.0], np.cumsum(a[1:])])
    F = g[0] + np.concatenate([[0.0], np.cumsum(g[1:])])
    S = np.where(V > 0, F / np.where(V > 0, V, 1), np.inf)
    return S


def per_firm_ratios(S):
    s = S / np.arange(1, len(S) + 1)
    return s[1:] / s[:-1]


def choose_K(m, ind):
    """Largest residual class K <= 5 with at least 10 towns in every class, in both years."""
    for K in range(MAX_CLASS, 1, -1):
        ok = all(np.bincount(np.minimum(m[f"{ind}{yr}"], K), minlength=K + 1).min()
                 >= MIN_PER_CLASS for yr in ("00", "16"))
        if ok:
            return K
    return 1


def std_errors(res, args):
    """Asymptotic standard errors from a numerical Hessian of the log likelihood."""
    theta = res.x
    k = len(theta)
    h = 1e-4 * np.maximum(1, np.abs(theta))
    H = np.zeros((k, k))
    f = lambda t: negloglik(t, *args)
    for i in range(k):
        for j in range(i, k):
            ei, ej = np.eye(k)[i] * h[i], np.eye(k)[j] * h[j]
            H[i, j] = H[j, i] = (f(theta + ei + ej) - f(theta + ei - ej) - f(theta - ei + ej)
                                 + f(theta - ei - ej)) / (4 * h[i] * h[j])
    try:
        se = np.sqrt(np.clip(np.diag(np.linalg.pinv(H)), 0, None))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)
    return se


def main():
    OUT.mkdir(exist_ok=True)
    m = pd.read_csv(ROOT / "data" / "markets.csv", dtype={"GEOID": str, "county": str})
    print(f"Loaded {len(m)} isolated towns from data/markets.csv")
    keep = m.tpop16 >= MIN_TOWN_POP
    print(f"Dropped {(~keep).sum()} towns with fewer than {MIN_TOWN_POP} residents in 2016")
    m = m[keep].reset_index(drop=True)
    print(f"Kept {len(m)} towns in {m.st.nunique()} states")
    funnel = pd.read_csv(OUT / "sample_funnel.csv")
    funnel = funnel[~funnel.step.str.contains("residents in 2016")]
    funnel.loc[len(funnel)] = [f"... with at least {MIN_TOWN_POP} residents in 2016 "
                               f"(estimation sample)", len(m)]
    funnel.to_csv(OUT / "sample_funnel.csv", index=False)
    m.groupby("state").size().sort_values(ascending=False).rename("towns").to_csv(
        OUT / "towns_by_state.csv")

    # Table 2 analog: towns by number of establishments, plus median population by N.
    rows = []
    for yr in ("16", "00"):
        for ind in INDUSTRIES:
            c = np.minimum(m[f"{ind}{yr}"], MAX_CLASS)
            for k in range(MAX_CLASS + 1):
                sel = c == k
                rows.append(dict(year=2000 + int(yr), industry=ind, n_firms=k,
                                 towns=int(sel.sum()),
                                 median_town_pop=m.loc[sel, f"tpop{yr}"].median()))
    pd.DataFrame(rows).to_csv(OUT / "market_counts.csv", index=False, float_format="%.0f")

    # 2022 check: ZBP now omits cells with one or two establishments, so only "3 or more"
    # can be compared with 2016.
    rows = []
    for ind in INDUSTRIES:
        a, b = m[f"{ind}16"] >= 3, m[f"{ind}22"] >= 3
        rows.append(dict(industry=ind, towns_3plus_2016=int(a.sum()), towns_3plus_2022=int(b.sum()),
                         both=int((a & b).sum()), median_pop_3plus_2016=m.loc[a, "tpop16"].median(),
                         median_pop_3plus_2022=m.loc[b, "tpop22"].median()))
    pd.DataFrame(rows).to_csv(OUT / "check_2022_three_plus.csv", index=False, float_format="%.0f")

    # Table 3 analog: sample statistics.
    stat_cols = {"tpop16": "Town population, 2016", "opop16": "Hinterland population, 2016",
                 "tpop00": "Town population, 2000", "pinc16": "County per capita income, 2016 ($000)",
                 "births16": "County births per resident, 2016",
                 "miles_to_1k_town": "Miles to nearest place of 1,000+",
                 "miles_to_100k_city": "Miles to nearest city of 100,000+"}
    stat_cols.update({f"{i}16": f"{LABELS[i]}, 2016" for i in INDUSTRIES})
    stat_cols.update({f"{i}00": f"{LABELS[i]}, 2000" for i in INDUSTRIES})
    desc = m[list(stat_cols)].describe().T[["mean", "std", "min", "50%", "max"]]
    desc.index = [stat_cols[c] for c in desc.index]
    desc.rename(columns={"50%": "median"}).to_csv(OUT / "sample_stats.csv", float_format="%.3f")

    rng = np.random.default_rng(SEED)
    boot_idx = [rng.integers(0, len(m), len(m)) for _ in range(N_BOOT)]
    est_rows, thr_rows, lr_rows, chg_rows = [], [], [], []
    boot_S = {}
    for ind in INDUSTRIES:
        K = choose_K(m, ind)
        print(f"\n{LABELS[ind]}: residual class {K}+ "
              f"(at least {MIN_PER_CLASS} towns per class in 2000 and 2016)")
        fits = {}
        for yr in ("16", "00"):
            n, tpop, opop, X = design(m, ind, yr)
            p = X.shape[1]
            res = fit(n, tpop, opop, X, K)
            se = std_errors(res, (K, p, n, tpop, opop, X))
            fits[yr] = res
            names = (["lambda_hinterland", "b_income"] + (["b_births"] if p == 2 else [])
                     + ["a1_V1"] + [f"a{j}_V{j-1}-V{j}" for j in range(2, K + 1)]
                     + ["g1_F1"] + [f"g{j}_F{j}-F{j-1}" for j in range(2, K + 1)])
            for nm, v, s in zip(names, res.x, se):
                est_rows.append(dict(year=2000 + int(yr), industry=ind, parameter=nm,
                                     estimate=v, std_error=s))
            est_rows.append(dict(year=2000 + int(yr), industry=ind, parameter="log_likelihood",
                                 estimate=-res.fun, std_error=np.nan))
            S = thresholds(res.x, K, p)
            # Bootstrap: same resampled towns in both years.
            bS = []
            for idx in boot_idx:
                r = fit(n[idx], tpop[idx], opop[idx], X[idx] - X[idx].mean(axis=0), K,
                        start=res.x)
                bS.append(thresholds(r.x, K, p))
            bS = np.array(bS)
            boot_S[(ind, yr)] = bS
            bR = np.array([per_firm_ratios(b) for b in bS])
            R = per_firm_ratios(S)
            for j in range(K):
                row = dict(year=2000 + int(yr), industry=ind, K=K, N=j + 1, S_N=S[j],
                           S_lo=np.nanpercentile(bS[:, j], 2.5),
                           S_hi=np.nanpercentile(bS[:, j], 97.5), s_N=S[j] / (j + 1))
                if j > 0:
                    finite = np.isfinite(bR[:, j - 1])
                    row.update(ratio=R[j - 1], ratio_lo=np.percentile(bR[finite, j - 1], 2.5),
                               ratio_hi=np.percentile(bR[finite, j - 1], 97.5))
                row.update(paper_S_N=PAPER_TABLE5[ind][j],
                           S_over_paper=S[j] / PAPER_TABLE5[ind][j],
                           paper_ratio=PAPER_RATIOS[ind][j - 1] if j > 0 else np.nan)
                thr_rows.append(row)
            print(f"  20{yr}: logL {-res.fun:.2f}, lambda {res.x[0]:.2f}, "
                  f"S_N (000s) {np.round(S, 2)}, s_N+1/s_N {np.round(R, 2)}")

            # Likelihood-ratio tests of proportional thresholds, as in the paper's Table 5B.
            for m0 in range(K - 1, 0, -1):
                rc = fit(n, tpop, opop, X, K, prop_from=m0, start=res.x)
                lr = max(2 * (rc.fun - res.fun), 0.0)
                df = K - m0
                lr_rows.append(dict(year=2000 + int(yr), industry=ind,
                                    hypothesis=" = ".join(f"s{j}" for j in range(m0, K + 1)),
                                    lr_stat=lr, df=df, p_value=stats.chi2.sf(lr, df)))

        # Extension: change in each threshold, 2000 -> 2016, paired bootstrap.
        p = 2 if ind in HEALTH else 1
        S16, S00 = thresholds(fits["16"].x, K, p), thresholds(fits["00"].x, K, p)
        d = boot_S[(ind, "16")] - boot_S[(ind, "00")]
        for j in range(K):
            fin = np.isfinite(d[:, j])
            chg_rows.append(dict(industry=ind, N=j + 1, S_2000=S00[j], S_2016=S16[j],
                                 change=S16[j] - S00[j], pct_change=100 * (S16[j] / S00[j] - 1),
                                 change_lo=np.percentile(d[fin, j], 2.5),
                                 change_hi=np.percentile(d[fin, j], 97.5),
                                 share_boot_higher=(d[fin, j] > 0).mean()))

    pd.DataFrame(est_rows).to_csv(OUT / "probit_estimates.csv", index=False, float_format="%.4f")
    thr = pd.DataFrame(thr_rows)
    thr.to_csv(OUT / "entry_thresholds.csv", index=False, float_format="%.3f")
    pd.DataFrame(lr_rows).to_csv(OUT / "lr_tests.csv", index=False, float_format="%.4f")
    chg = pd.DataFrame(chg_rows)
    chg.to_csv(OUT / "threshold_change.csv", index=False, float_format="%.3f")
    print("\nWrote market_counts, sample_stats, probit_estimates, entry_thresholds, lr_tests, "
          "threshold_change")
    make_figures(thr, chg)
    named_towns(m)
    featured_towns(m)
    isolation_check(m)


def featured_towns(m):
    """Population and every industry's count in 2000 and 2016 for the towns named in the README."""
    rows = []
    for town, st in FEATURED:
        r = m[(m.town == town) & (m.st == st)].iloc[0]
        row = dict(town=town, st=st, tpop00=r.tpop00, tpop16=r.tpop16, n_zips=r.n_zips16,
                   miles_to_1k_town=round(r.miles_to_1k_town, 1))
        for ind in INDUSTRIES:
            row[f"{ind}_2000"], row[f"{ind}_2016"] = r[f"{ind}00"], r[f"{ind}16"]
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "featured_towns.csv", index=False, float_format="%.0f")
    print("Wrote featured_towns.csv")


def isolation_check(m):
    """2016 thresholds for N = 1..3 as the distance rule is tightened (point estimates only)."""
    rows = []
    for miles in ISOLATION_CHECK_MILES:
        sub = m[m.miles_to_1k_town >= miles].reset_index(drop=True)
        for ind in INDUSTRIES:
            n, tpop, opop, X = design(sub, ind, "16")
            res = fit(n, tpop, opop, X, 3)
            S = thresholds(res.x, 3, X.shape[1])
            R = per_firm_ratios(S)
            rows.append(dict(min_miles_to_1k_town=miles, towns=len(sub), industry=ind,
                             S_1=S[0], S_2=S[1], S_3=S[2], s2_s1=R[0], s3_s2=R[1]))
    pd.DataFrame(rows).to_csv(OUT / "isolation_check.csv", index=False, float_format="%.4f")
    print("Wrote isolation_check.csv")


def make_figures(thr, chg):
    """Figure 1: per-firm thresholds relative to the monopoly threshold, 2016 vs the paper.
    Figure 2: entry thresholds in 2000 and 2016."""
    colors = dict(zip(INDUSTRIES, ["#2a6fbb", "#d9822b", "#3a9e5f", "#8e5ea2", "#c23b3b"]))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ind in INDUSTRIES:
        paper = np.array(PAPER_TABLE5[ind]) / np.arange(1, 6)
        axes[0].plot(range(1, 6), paper / paper[0], "-o", color=colors[ind], label=LABELS[ind])
        t = thr[(thr.industry == ind) & (thr.year == 2016)]
        axes[1].plot(t.N, t.s_N / t.s_N.iloc[0], "-o", color=colors[ind], label=LABELS[ind])
    for ax, title in zip(axes, ["Bresnahan and Reiss, about 1980 (Table 5)",
                                "Isolated US towns, 2016 (this study)"]):
        ax.axhline(1, color="0.6", lw=0.8)
        ax.set_xticks(range(1, 6))
        ax.set_xlabel("Number of firms, N")
        ax.set_title(title, fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Residents per firm, relative to N = 1 (s_N / s_1)")
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "per_firm_thresholds.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(INDUSTRIES), figsize=(13, 3.6))
    for ax, ind in zip(axes, INDUSTRIES):
        c = chg[chg.industry == ind]
        ax.plot(c.N, c.S_2000, "-o", color="0.55", label="2000")
        ax.plot(c.N, c.S_2016, "-o", color=colors[ind], label="2016")
        ax.set_title(LABELS[ind], fontsize=10)
        ax.set_xticks(c.N)
        ax.set_xlabel("Number of firms, N")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Market size needed, S_N (thousand residents)")
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "thresholds_2000_2016.png", dpi=150)
    plt.close(fig)
    print("Wrote per_firm_thresholds.png and thresholds_2000_2016.png")


def named_towns(m):
    """Real towns behind the numbers: the largest towns in each industry with one firm or none,
    and towns whose count changed most between 2000 and 2016."""
    rows = []
    for ind in INDUSTRIES:
        for k in (0, 1, 2):
            sel = m[m[f"{ind}16"] == k].sort_values("tpop16", ascending=False).head(3)
            for _, r in sel.iterrows():
                rows.append(dict(industry=ind, kind=f"largest towns with {k} in 2016",
                                 town=r.town, st=r.st, tpop16=r.tpop16, tpop00=r.tpop00,
                                 opop16=round(r.opop16), firms_2000=r[f"{ind}00"],
                                 firms_2016=r[f"{ind}16"]))
        d = m.assign(delta=m[f"{ind}16"] - m[f"{ind}00"]).sort_values("delta")
        for kind, sel in (("biggest losses 2000-2016", d.head(3)),
                          ("biggest gains 2000-2016", d.tail(3).iloc[::-1])):
            for _, r in sel.iterrows():
                rows.append(dict(industry=ind, kind=kind, town=r.town, st=r.st,
                                 tpop16=r.tpop16, tpop00=r.tpop00, opop16=round(r.opop16),
                                 firms_2000=r[f"{ind}00"], firms_2016=r[f"{ind}16"]))
    pd.DataFrame(rows).to_csv(OUT / "named_towns.csv", index=False)
    print("Wrote named_towns.csv")


if __name__ == "__main__":
    main()
