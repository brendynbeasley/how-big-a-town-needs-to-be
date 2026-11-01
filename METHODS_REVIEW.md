# Methods review: Bresnahan and Reiss (1991)

**Paper:** Timothy F. Bresnahan and Peter C. Reiss, "Entry and Competition in Concentrated Markets," *Journal of
Political Economy* 99(5), October 1991, pp. 977–1009.

**Statistical focus:** the entry thresholds and per-firm threshold ratios in Table 5 (for example $`s_2/s_1`$ =
1.98 for doctors and 1.06 for plumbers), the likelihood-ratio tests of threshold proportionality in Table 5B, and
the tire-price regressions in Table 11 offered as cross-validation.

**Review standard:** current AEA Data and Code Availability Policy, and standard reporting of estimates,
uncertainty, sample construction and robustness for structural discrete-choice models.

**What was read:** the full published article (pages 977–1009, including Tables 1 to 11 and Figures 1 to 4), from
a JSTOR copy hosted on a Caltech course page. Tables 4 and 5 were read from page images because the scanned text
layer is incomplete. The earlier Bresnahan and Reiss papers (1988, 1990) that supply the sample criteria were not
read.

## Methods summary

The paper derives, from a free-entry model with U-shaped average costs, the market size $`S_N`$ at which $`N`$
firms break even, and shows that the ratio of per-firm thresholds $`s_{N+1}/s_N`$ equals 1 when entry does not
change conduct and costs. It then estimates these thresholds from a cross-section of 202 geographically isolated
US towns, mostly western county seats, using ordered probit models of the number of firms (0 to 4, and 5 or more)
for doctors, dentists, druggists, plumbers and tire dealers. Profit is market size times variable profit per
resident minus fixed cost, with step changes in both by number of firms. Tire prices collected by telephone in
1990 provide an independent check.

## Research design

Cross-sectional, structural. Identification comes from comparing towns of different size under the maintained
assumptions that each town is an isolated market, that demand scales with population, and that all firms in a
town share one profit shock. There is no time variation; the authors say panel data would be needed to address
entry timing (p. 998).

## Sampling strategy

Purposive. Towns were selected to be at least 20 miles from the nearest town of 1,000 or more and not within 100
miles of a city of 100,000, and not part of a cluster of towns (p. 985). Details are deferred to the 1988 and 1990
papers. Industries were kept only if each size class had at least 10 towns; beauticians and electricians were then
dropped because two thresholds could not be estimated reliably (p. 987).

## Sample size

202 towns. Table 2 gives counts by industry and number of firms; for example 28 towns had no druggist and 62 had
one. Table 3 gives a mean town population of 3,740 (range 120 to 45,090). The tire price sample has 282 usable
quotations (Table 11). The isolation checks use 157 very isolated towns and a separate sample of counties under
10,000 residents for doctors and dentists only (p. 1001 to 1003); the size of the county sample is not stated.

## Inclusion and exclusion criteria

Stated at the level of rules (distance and size thresholds, ten towns per class) but not with a list of towns or
a count of towns excluded at each step. Firms at the same address and phone number were merged into one firm; the
authors report that counting individual physicians and dentists changes the ratios only slightly (p. 987).

## Independent and dependent variables

Dependent: number of firms in town. The text says firms were identified from telephone books and trade
information and checked by visiting some markets and against secondary sources (p. 987); the source note to
Table 2 credits the authors' tabulations from American Business Lists. Market size: town population plus weighted nearby population (within 10 miles), positive and negative
1970–80 growth, and out-of-county commuters. Variable-profit shifters: births and elderly share (health
industries), per capita income, heating degree days, housing units, house values, farmland share. Fixed-cost
shifter: farmland value. Definitions and moments are in Table 3.

## Statistical methods

Maximum likelihood ordered probit with 19 parameters per industry, with inequality constraints that later entrants
are no more profitable at a given size (constrained specifications reported when constraints bind). Asymptotic
standard errors for parameters (Table 4). Likelihood-ratio tests of threshold equality (Table 5B), equal fixed costs
(Table 6), and exclusion of market-size and profit variables (Tables 7 and 8). Tire prices are analyzed with OLS
and least absolute deviations with brand, mileage and wage controls (Table 11).

## Reported effect sizes

The thresholds and ratios in Table 5 are the effect sizes. Monopoly thresholds run from 490 residents (tire
dealers) to 1,430 (plumbers). The second-firm ratio is between 1.78 and 1.99 for four industries and 1.06 for
plumbers; ratios for the fourth and fifth firm lie between 0.94 and 1.14. In the tire data, prices fall about 8
percent from monopoly to five dealers and another 20 percent to the Bay Area (p. 1006).

## Confidence intervals

None are reported for the thresholds or ratios, which are nonlinear functions of the estimated parameters. Only
parameter standard errors (Table 4) and test statistics are shown. This is a reporting gap rather than an error,
since a delta-method or bootstrap interval was feasible.

## P-values, if applicable

Significance is marked with asterisks at the 5 percent level, with test statistics and degrees of freedom given
(Tables 5B, 6, 11). Exact p-values are not reported. The authors note the sequential tests are not independent
(p. 997).

## Missing data treatment

Not discussed. The paper does not say whether any towns lacked county covariates or were dropped for missing
values, or how dealers who would not quote prices affect the tire sample beyond the response counts in Table 10.

## Stated limitations

The authors state that threshold ratios cannot separate falling margins from rising entry costs or entrant
inefficiency (pp. 983, 997–998), that product differentiation could offset margin changes, that markets may
overlap, that entry timing is unobserved, and that the auto-dealer result shows the pattern may fail for
differentiated products (p. 1007).

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Sample of markets | 202 towns | p. 985; Table 2 | Isolated markets used in all probits | That every town is a closed market |
| Mean town population | 3,740 residents (s.d. 5,350) | Table 3 | Typical market size | Population of the trading area |
| Monopoly threshold, doctors | 880 residents | Table 5A | Market size at which one doctor breaks even | A doctor's fixed cost in dollars |
| Monopoly threshold, druggists | 530 residents | Table 5A | Same, druggists | Pharmacy margins |
| Monopoly threshold, plumbers | 1,430 residents | Table 5A | Same, plumbers | Why plumbers need more |
| $`s_2/s_1`$, doctors | 1.98 | Table 5A | Rise in residents per firm from one to two doctors | Whether margins or fixed costs changed |
| $`s_2/s_1`$, druggists | 1.99 | Table 5A | Same, druggists | Price effects of entry |
| $`s_2/s_1`$, plumbers | 1.06 | Table 5A | Same, plumbers | That plumbing is competitive at N = 1 |
| $`s_5/s_4`$ range | 0.94 to 1.03 | Table 5A | Change in conduct from the fourth to fifth firm | Conduct relative to a large urban market |
| LR test $`s_1 = \dots = s_5`$, druggists | 113.92, 8 df, significant at 5% | Table 5B | Rejection of proportional thresholds | Which step drives the rejection |
| LR test $`s_3 = s_4 = s_5`$, doctors | 6.20, 3 df, not significant | Table 5B | No detectable change after the third doctor | Equality, given low power |
| Equal fixed costs test, doctors | 28.63, 2 df, significant | Table 6 | Later entrants have higher fixed costs | Whether those costs are inefficiency or barriers |
| Very isolated sample | 157 towns | p. 1001; Table 9 | Robustness of ratios to a 40-mile rule | Thresholds for druggists, plumbers, tires (not run) |
| Tire price, monopoly vs urban | $53.90 vs $43.20 median | Table 10 | Price gap between monopoly towns and the Bay Area | Quality-adjusted margins |
| Tire price regression, monopoly dummy | 1.88 (s.e. 2.12), N = 282 | Table 11, col. 1 | Price premium relative to towns failing the market definition | A causal effect of entry |
| Test monopoly = duopoly price | F = 0.01 | Table 11, col. 1 | No price difference between one and two dealers | That the second dealer leaves margins unchanged |

## Interpretation notes

The headline claim, that most change in conduct happens with the second and third firm, rests on point estimates
of ratios without intervals, and on tests whose power is limited by small cells (for example, 8 towns with four
druggists in Table 2). The tests in Table 5B support the claim for doctors, druggists, plumbers and tire dealers,
but for dentists the hypothesis $`s_3 = s_4 = s_5`$ is rejected (12.30 on 2 df), which the authors acknowledge.
Table 6 shows that later entrants have significantly higher fixed costs in four industries, so part of each ratio
is a cost effect; the constrained ratios in Table 6 are close to the baseline ones, which reduces but does not
remove that concern. The tire price check is consistent with the threshold pattern, but its monopoly and duopoly
coefficients are not individually significant, and the quotes postdate the firm counts. In Table 5A the printed dentist ratio $`s_3/s_2`$ is .79, but the printed thresholds (2.54 and 4.18) imply
$`(4.18/3)/(2.54/2) = 1.10`$; the other nineteen printed ratios agree with the thresholds to within rounding.
This looks like a typesetting error rather than an analytical one, and the paper's text about dentists does not
depend on it. The paper's own unisolated
county sample gives much smaller ratios, which supports the market definition but also shows how sensitive the
statistic is to it.

## Unanswered questions

How many candidate towns failed each selection rule, and how sensitive the thresholds are to the hand-built list
of towns. Whether the ratios would hold with confidence intervals attached. How much of the second-firm ratio is
margin and how much fixed cost, which later work with quantity data (Abraham, Gaynor and Vogt, 2007) addresses for
hospitals. Whether the 1980 pattern holds for other periods, which this repository examines for 2000 and 2016 with
different data and towns.

## Items requiring expert verification

Whether the dentist ratio of .79 in Table 5A is a misprint for about 1.10, as the printed thresholds imply. The
exact construction of nearby population and the town screening rules, which are documented in the 1988 and
1990 papers rather than this one. Whether the American Business Lists counts treated chain outlets and branch
offices consistently across industries. Whether the parameter constraints that bind (for example $`\alpha_3`$ and
$`\alpha_5`$ set to zero for doctors) affect the reported ratios materially.

The modern rerun in this repository uses Census establishment counts for 445 towns in 2016 and 2000. It follows
the paper's selection rules and likelihood but is not a reproduction, since the original town list and firm counts
are not public.
