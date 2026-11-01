# Technical notes

This is the technical companion to the [README](README.md). Every number below is written by the scripts to
`results/*.csv`. A plain-English summary and all tables are in [results/FINDINGS.md](results/FINDINGS.md).

## The original study

Timothy F. Bresnahan and Peter C. Reiss, "Entry and Competition in Concentrated Markets," *Journal of Political
Economy* 99(5), October 1991, pp. 977–1009. Using 202 isolated towns (mostly western county seats at least 20
miles from a town of 1,000 and 100 miles from a city of 100,000), firm counts tabulated from American Business
Lists and checked against telephone books and site visits, and county Census covariates, they estimated ordered probits of the number of firms for five industries. Table 5 reports
monopoly thresholds of 880 residents (doctors), 710 (dentists), 530 (druggists), 1,430 (plumbers) and 490 (tire
dealers), and per-firm ratios $`s_2/s_1`$ of 1.98, 1.78, 1.99, 1.06 and 1.81. Ratios for the fourth and fifth firm
lie between 0.94 and 1.14. Their conclusion is that almost all change in conduct comes with the second and third
entrant.

## Headline results

| Industry | Top class | $`S_1`$ 2016 (paper) | $`s_2/s_1`$ 2016 [95% CI] | Paper | Equal-$`s`$ test, 2016 | $`\Delta S_1`$ 2000→2016 [95% CI] |
|---|---|---|---|---|---|---|
| Doctors | 3+ | 3,590 (880) | 0.86 [0.79, 1.00] | 1.98 | χ² = 9.93, df 2, p = 0.007 | +1,550 [+574, +2,939] |
| Dentists | 4+ | 1,871 (710) | 1.04 [0.89, 1.20] | 1.78 | χ² = 6.00, df 3, p = 0.11 | −99 [−495, +316] |
| Drugstores | 3+ | 2,306 (530) | 1.58 [1.23, 2.08] | 1.99 | χ² = 23.46, df 2, p < 0.001 | +1,028 [+522, +2,090] |
| Plumbers | 5+ | 1,821 (1,430) | 0.81 [0.74, 0.92] | 1.06 | χ² = 13.80, df 4, p = 0.008 | −316 [−699, +163] |
| Tire dealers | 3+ | 3,032 (490) | 1.11 [0.88, 1.41] | 1.81 | χ² = 0.98, df 2, p = 0.61 | −986 [−2,136, +29] |

The equal-$`s`$ test is the joint null $`s_1 = \dots = s_K`$. Drugstores keep the paper's pattern (a large
second-firm ratio, then about 1). Dentists and tire dealers show ratios near 1 throughout. Doctors and plumbers
show ratios below 1, which the paper's theory rules out for identical firms with nondecreasing fixed costs and
margins that do not rise with entry.

## Data

All files are free Census Bureau or BEA downloads, retrieved on 1 November 2026. Committed in `data/raw/`:
`2023_Gaz_place_national.zip` (place internal points), `co-est2009-alldata.csv`,
`co-est2020-alldata.csv`, `co-est2023-alldata.csv` (county population and births; the 2000 births measure is
`BIRTHS2001`, July 2000 to June 2001, because `BIRTHS2000` in that file covers only April to June 2000), `zbp00totals.zip`,
`zbp16totals.zip`, `zbp22totals.zip` (ZIP code post-office names) and `CAINC1.zip` (BEA county per capita
income). Fetched by `src/build_markets.py` on first run and ignored by git: `acsdt5y2022-b01003.dat` (ACS
2018–22 population for every place and ZIP code tabulation area), `sub-est2023.csv`, `SUB-EST2020_ALL.csv`,
`sub-est00int.csv` (July 2022, 2016 and 2000 incorporated-place estimates) and `zbp00detail.zip`,
`zbp16detail.zip`, `zbp22detail.zip` (ZIP Code Business Patterns by NAICS). The built town file is
`data/markets.csv`.

Industries are NAICS 621111 (offices of physicians), 621210 (dentists), 446110 (pharmacies and drug stores),
238220 in 2016 and 2022 and 235110 in 2000 (plumbing, heating and air-conditioning contractors) and 441320 (tire
dealers). From 2017 on, ZBP drops ZIP-industry cells with fewer than three establishments, so 2016 is the main
year and 2022 is used only to compare counts of three or more (`check_2022_three_plus.csv`).

## Method

These rules were fixed before estimation.

1. Towns are incorporated places in the 48 contiguous states whose internal point is at least 20 miles from any
   other place (incorporated or not) with 1,000+ residents in the 2018–22 ACS and at least 100 miles from any
   place with 100,000+, with at most 50,000 residents in 2022 and at least 120 in 2016 (the paper's smallest town).
2. A town's market is the ZIP codes whose ZBP post-office name matches the town's name in its state. Towns with
   a name shared with another isolated town in the state, or without a matching ZIP code in both 2000 and 2016, are dropped. Funnel in
   `sample_funnel.csv`.
3. Market size is $`S_i = \text{TPOP}_i + \lambda\,\text{OPOP}_i`$ in thousands, with OPOP the ZIP codes'
   ACS population minus the town's own, scaled to 2016 and 2000 by county population growth. $`\lambda`$ is
   bounded to [0, 3].
4. Profit shifters $`X_i`$ are county per capita income (all industries) and county births per 100 residents
   (doctors, dentists, drugstores; the paper used births for doctors and dentists only), demeaned within year.
   The paper's growth, commuting, elderly-share, heating, housing and farmland variables are not used.
5. The top count class is the largest $`K \le 5`$ with at least ten towns in every class in both years. The
   paper instead dropped industries without ten towns in each of its six classes.

The likelihood is the paper's equations (8) to (11):

```math
\begin{aligned}
\Pi_{N,i} &= S_i\Big(\alpha_1 + X_i\beta - \textstyle\sum_{n=2}^{N}\alpha_n\Big)
 - \Big(\gamma_1 + \textstyle\sum_{n=2}^{N}\gamma_n\Big) + \varepsilon_i \\
\Pr(N_i = N) &= \Phi(\bar\Pi_{N,i}) - \Phi(\bar\Pi_{N+1,i}), \quad
\Pr(N_i \ge K) = \Phi(\bar\Pi_{K,i}) \\
S_N &= \frac{\gamma_1 + \sum_{n=2}^{N}\gamma_n}{\alpha_1 - \sum_{n=2}^{N}\alpha_n},
\qquad \frac{s_{N+1}}{s_N} = \frac{N}{N+1}\cdot\frac{S_{N+1}}{S_N}
\end{aligned}
```

with $`\varepsilon_i \sim N(0,1)`$ and $`\alpha_n, \gamma_n \ge 0`$ for $`n \ge 2`$, estimated by bounded
L-BFGS-B from four starting points. The proportionality test $`H_0\colon s_m = \dots = s_K`$ replaces each
$`F_N`$ for $`N > m`$ by $`(N/m)\,F_m \bar V_N / \bar V_m`$, with $`m`$ running from $`K-1`$ down to 1, and
compares likelihoods with $`\chi^2_{K-m}`$. This imposes one restriction per tied threshold, so the degrees of
freedom are smaller than in the paper's Table 5B, which restricted both the $`\alpha`$ and $`\gamma`$ steps. Threshold and ratio intervals are 2.5th and 97.5th percentiles of 200
bootstrap draws of towns. The same draws are used in both years, which gives the paired interval for each change.
Parameter standard errors in `probit_estimates.csv` come from a numerical Hessian and are not meaningful for
parameters at a bound.

## Full test statistics

Ratios $`s_{N+1}/s_N`$, 2016 and 2000 (`entry_thresholds.csv`):

| Industry | 2016 | 2000 |
|---|---|---|
| Doctors | 0.86, 0.87 | 0.945, 0.905 |
| Dentists | 1.04, 1.14, 0.94 | 0.94, 0.92, 1.06 |
| Drugstores | 1.58, 0.99 | 1.52, 1.07 |
| Plumbers | 0.81, 1.16, 0.93, 1.04 | 0.86, 1.06, 0.90, 0.94 |
| Tire dealers | 1.11, 0.96 | 1.05, 0.86 |

Likelihood-ratio tests, 2016 (`lr_tests.csv`): doctors $`s_2 = s_3`$ χ² = 5.47 (p = 0.019); dentists
$`s_3 = s_4`$ 0.90 (p = 0.34), $`s_2 = s_3 = s_4`$ 4.10 (p = 0.13); drugstores $`s_2 = s_3`$ 0.05 (p = 0.83);
plumbers $`s_4 = s_5`$ 0.53 (p = 0.47), $`s_3 = s_4 = s_5`$ 2.33 (p = 0.31), $`s_2 = \dots = s_5`$ 7.73
(p = 0.052); tire dealers $`s_2 = s_3`$ 0.10 (p = 0.75). Hinterland weights $`\hat\lambda`$ in 2016 run from 0.00
(tire dealers) to 0.94 (plumbers).

Isolation check (`isolation_check.csv`, 2016, three-class model): with the distance rule raised to 30 miles
(176 towns), $`s_2/s_1`$ is 0.97 for doctors, 0.99 for dentists, 2.03 for drugstores, 0.86 for plumbers and 0.90
for tire dealers.

## Reproducing the results

```bash
pip install -r requirements.txt
python src/build_markets.py      # downloads about 110 MB of Census files once; writes data/markets.csv
python src/entry_thresholds.py   # estimation, bootstrap, tables and figures; about three minutes
```

## Repository layout

| Path | What it is |
|---|---|
| [src/build_markets.py](src/build_markets.py) | Isolation rules, ZIP matching, firm counts, covariates |
| [src/entry_thresholds.py](src/entry_thresholds.py) | Ordered probits, thresholds, bootstrap, tests, figures |
| `data/markets.csv` | One row per town, 2000, 2016 and 2022 |
| `results/` | All CSV tables and the two figures |

## References

- Abraham, J. M., Gaynor, M. S. & Vogt, W. B. (2007). Entry and competition in local hospital markets. *Journal
  of Industrial Economics* 55(2), 265–288.
- Bresnahan, T. F. & Reiss, P. C. (1991). Entry and competition in concentrated markets. *Journal of Political
  Economy* 99(5), 977–1009.
- US Census Bureau. ZIP Code Business Patterns, 2000, 2016, 2022; Population Estimates; 2023 Gazetteer;
  American Community Survey 2018–2022, table B01003.
- US Bureau of Economic Analysis. CAINC1, county personal income summary.
