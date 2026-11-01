"""Build the sample of isolated American towns and count their doctors, dentists,
pharmacies, plumbers and tire dealers in 2000, 2016 and 2022.

Bresnahan and Reiss (1991) used 202 isolated towns, mostly western county seats, that were
at least 20 miles from the nearest town of 1,000 people and at least 100 miles from a city
of 100,000. This script applies the same two distance rules to every incorporated place in
the 48 contiguous states, using Census internal points and populations, and then counts
establishments in each town's ZIP codes from the Census ZIP Code Business Patterns (ZBP).

A town's market is the set of ZIP codes whose post office carries the town's name. Firms
are the establishments in those ZIP codes. The town's own population and the rest of the
population of those ZIP codes (the "hinterland") measure market size, standing in for the
paper's town population and nearby population.

2016 is the main year: it is the last year in which ZBP published exact establishment
counts for every ZIP code and industry. From 2017 on, cells with one or two establishments
are left out of the file, so the 2022 counts are kept only for a censored check (0-2, 3, 4, 5+).

Usage (from the repository root):
    python src/build_markets.py

Large Census files are downloaded into data/raw/ on first run (ignored by git). Writes
data/markets.csv and results/sample_funnel.csv.
"""

import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"

# Bresnahan and Reiss (1991), p. 985: at least 20 miles from the nearest town of 1,000 or more,
# and no town within 100 miles of a city of 100,000.
NEAR_TOWN_POP = 1_000
NEAR_TOWN_MILES = 20
BIG_CITY_POP = 100_000
BIG_CITY_MILES = 100
# The paper's largest sample town had 45,090 people (Table 3); I keep towns up to 50,000.
MAX_TOWN_POP = 50_000

YEARS = ("00", "16", "22")
# Paper industry -> NAICS code in ZBP 2000 (NAICS 1997), 2016 (NAICS 2012), 2022 (NAICS 2017).
INDUSTRIES = {
    "doctors": ("621111", "621111", "621111"),       # offices of physicians (except mental health)
    "dentists": ("621210", "621210", "621210"),      # offices of dentists
    "druggists": ("446110", "446110", "446110"),     # pharmacies and drug stores
    "plumbers": ("235110", "238220", "238220"),      # plumbing, heating and air-conditioning
    "tire_dealers": ("441320", "441320", "441320"),  # tire dealers
}

NOT_CONTIGUOUS = {"02", "15", "72"}  # Alaska, Hawaii, Puerto Rico

CENSUS = "https://www2.census.gov/programs-surveys/"
DOWNLOADS = {
    "acsdt5y2022-b01003.dat": CENSUS + "acs/summary_file/2022/table-based-SF/data/5YRData/"
                                       "acsdt5y2022-b01003.dat",
    "sub-est2023.csv": CENSUS + "popest/datasets/2020-2023/cities/totals/sub-est2023.csv",
    "SUB-EST2020_ALL.csv": CENSUS + "popest/datasets/2010-2020/cities/SUB-EST2020_ALL.csv",
    "sub-est00int.csv": CENSUS + "popest/datasets/2000-2010/intercensal/cities/sub-est00int.csv",
    "zbp00detail.zip": CENSUS + "cbp/datasets/2000/zbp00detail.zip",
    "zbp16detail.zip": CENSUS + "cbp/datasets/2016/zbp16detail.zip",
    "zbp22detail.zip": CENSUS + "cbp/datasets/2022/zbp22detail.zip",
}


def fetch(name):
    """Return the local path of a raw file, downloading it if it is not there yet."""
    path = RAW / name
    if not path.exists():
        print(f"  downloading {name} ...")
        tmp = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(DOWNLOADS[name], tmp)
        tmp.rename(path)
    return path


def clean_name(name):
    """Upper-case a place or post-office name and drop the legal suffix and punctuation."""
    name = name.upper()
    name = re.sub(r"\s+(CITY AND BOROUGH|CITY|TOWN|VILLAGE|BOROUGH|CDP|MUNICIPALITY)\b.*$",
                  "", name)
    name = name.replace("SAINT ", "ST ").replace("ST. ", "ST ").replace("FORT ", "FT ")
    name = name.replace("MOUNT ", "MT ")
    return re.sub(r"[^A-Z ]", "", name).strip()


def miles_to_nearest(lat, lon, ids, plat, plon, pids, chunk=2000):
    """Great-circle miles from each point to the nearest other point (by id) in a second set."""
    lat2, lon2 = np.radians(plat)[None, :], np.radians(plon)[None, :]
    out = np.empty(len(lat))
    for start in range(0, len(lat), chunk):
        sl = slice(start, start + chunk)
        lat1, lon1 = np.radians(lat[sl])[:, None], np.radians(lon[sl])[:, None]
        a = (np.sin((lat2 - lat1) / 2) ** 2
             + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
        d = 2 * 3958.8 * np.arcsin(np.sqrt(a))
        d[ids[sl][:, None] == pids[None, :]] = np.inf
        out[sl] = d.min(axis=1)
    return out


def load_places():
    """Every Census place with its internal point and 2018-22 ACS population."""
    with zipfile.ZipFile(RAW / "2023_Gaz_place_national.zip") as z:
        gaz = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype={"GEOID": str})
    gaz.columns = [c.strip() for c in gaz.columns]
    acs = pd.read_csv(fetch("acsdt5y2022-b01003.dat"), sep="|", dtype=str)
    place_pop = acs[acs.GEO_ID.str.startswith("1600000US")].copy()
    place_pop["GEOID"] = place_pop.GEO_ID.str[9:]
    place_pop["acs_pop"] = place_pop.B01003_E001.astype(int)
    places = gaz.merge(place_pop[["GEOID", "acs_pop"]], on="GEOID", how="left")
    places["acs_pop"] = places.acs_pop.fillna(0)
    places = places[~places.GEOID.str[:2].isin(NOT_CONTIGUOUS)]
    print(f"Loaded {len(places):,} places in the contiguous states (gazetteer + ACS 2018-22)")
    return places, acs


def place_estimates(file, column, label):
    """July population estimates for incorporated places (summary level 162)."""
    est = pd.read_csv(fetch(file), dtype=str, encoding="latin-1")
    inc = est[est.SUMLEV == "162"].copy()
    inc["GEOID"] = inc.STATE + inc.PLACE
    inc[label] = inc[column].astype(int)
    return est, inc[["GEOID", label]]


def load_town_populations():
    """2000, 2016 and 2022 estimates for incorporated places, with each town's main county."""
    est22, inc = place_estimates("sub-est2023.csv", "POPESTIMATE2022", "tpop22")
    names = est22[est22.SUMLEV == "162"].assign(GEOID=lambda d: d.STATE + d.PLACE)
    inc = inc.merge(names[["GEOID", "NAME", "STNAME"]], on="GEOID")
    parts = est22[est22.SUMLEV == "157"].copy()
    parts["GEOID"] = parts.STATE + parts.PLACE
    parts["p"] = parts.POPESTIMATE2022.astype(int)
    parts = parts.sort_values("p", ascending=False).drop_duplicates("GEOID")
    parts["county"] = parts.STATE + parts.COUNTY
    inc = inc.merge(parts[["GEOID", "county"]], on="GEOID", how="left")
    _, p16 = place_estimates("SUB-EST2020_ALL.csv", "POPESTIMATE2016", "tpop16")
    _, p00 = place_estimates("sub-est00int.csv", "POPESTIMATE2000", "tpop00")
    inc = inc.merge(p16, on="GEOID", how="left").merge(p00, on="GEOID", how="left")
    print(f"Loaded {len(inc):,} incorporated places with 2022 estimates; "
          f"{inc.tpop16.notna().sum():,} have 2016 and {inc.tpop00.notna().sum():,} have 2000")
    return inc


def load_counties():
    """County population, births per resident and per capita personal income ($000)."""
    files = {"00": "co-est2009-alldata.csv", "16": "co-est2020-alldata.csv",
             "22": "co-est2023-alldata.csv"}
    # Births in the twelve months to July of the year. In the vintage 2009 file BIRTHS2000 covers
    # only April to June 2000, so the 2000 measure uses BIRTHS2001 (July 2000 to June 2001).
    births_col = {"00": "BIRTHS2001", "16": "BIRTHS2016", "22": "BIRTHS2022"}
    counties = None
    for yr, file in files.items():
        df = pd.read_csv(RAW / file, dtype=str, encoding="latin-1")
        df = df[df.SUMLEV == "050"].copy()
        df["county"] = df.STATE + df.COUNTY
        df[f"cpop{yr}"] = df[f"POPESTIMATE20{yr}"].astype(float)
        df[f"births{yr}"] = df[births_col[yr]].astype(float) / df[f"cpop{yr}"]
        df = df[["county", f"cpop{yr}", f"births{yr}"]].set_index("county")
        counties = df if counties is None else counties.join(df, how="outer")
    with zipfile.ZipFile(RAW / "CAINC1.zip") as z:
        bea = pd.read_csv(z.open("CAINC1__ALL_AREAS_1969_2024.csv"), dtype=str, encoding="latin-1")
    bea = bea[bea.LineCode.str.strip() == "3"].copy()
    bea["county"] = bea.GeoFIPS.str.strip().str.strip('"').str.strip()
    for yr in YEARS:
        bea[f"pinc{yr}"] = pd.to_numeric(bea[f"20{yr}"], errors="coerce") / 1000
    counties = counties.join(bea.set_index("county")[[f"pinc{y}" for y in YEARS]], how="left")
    return counties.reset_index()


def zip_establishments(year):
    """Establishment counts by ZIP code for the five industries, from a ZBP detail file."""
    col = YEARS.index(year)
    codes = {v[col]: ind for ind, v in INDUSTRIES.items()}
    keep = []
    for chunk in pd.read_csv(fetch(f"zbp{year}detail.zip"), dtype=str,
                             usecols=["zip", "naics", "est"], chunksize=2_000_000):
        keep.append(chunk[chunk.naics.isin(codes)])
    df = pd.concat(keep)
    df["industry"] = df.naics.map(codes)
    df["est"] = df.est.astype(int)
    wide = df.pivot_table(index="zip", columns="industry", values="est", aggfunc="sum").fillna(0)
    print(f"  ZBP 20{year}: {len(df):,} ZIP-industry rows for the five industries "
          f"({int(df.est.sum()):,} establishments nationwide)")
    return wide


def zip_cities(year):
    """ZIP code -> cleaned post-office name and state, from the ZBP totals file."""
    with zipfile.ZipFile(RAW / f"zbp{year}totals.zip") as z:
        tot = pd.read_csv(z.open(z.namelist()[0]), dtype=str, encoding="latin-1")
    tot.columns = [c.lower() for c in tot.columns]
    if "city" in tot.columns:
        tot["po_name"], tot["st"] = tot.city, tot.stabbr
    else:
        split = tot.name.str.rsplit(",", n=1, expand=True)
        tot["po_name"], tot["st"] = split[0], split[1].str.strip()
    tot["key"] = tot.po_name.fillna("").map(clean_name) + "|" + tot.st
    return tot[["zip", "key"]]


def main():
    OUT.mkdir(exist_ok=True)
    funnel = []
    places, acs = load_places()
    towns = load_town_populations()
    towns = towns[~towns.GEOID.str[:2].isin(NOT_CONTIGUOUS)]
    towns = towns.merge(places[["GEOID", "NAME", "USPS", "INTPTLAT", "INTPTLONG"]]
                        .rename(columns={"NAME": "gaz_name"}), on="GEOID", how="inner")
    funnel.append(("Incorporated places, contiguous states", len(towns)))

    # Distance rules, measured between Census internal points.
    others = places[places.acs_pop >= NEAR_TOWN_POP]
    big = places[places.acs_pop >= BIG_CITY_POP]
    tlat, tlon = towns.INTPTLAT.to_numpy(float), towns.INTPTLONG.to_numpy(float)
    tid = towns.GEOID.to_numpy(object)
    towns["miles_to_1k_town"] = miles_to_nearest(
        tlat, tlon, tid, others.INTPTLAT.to_numpy(float), others.INTPTLONG.to_numpy(float),
        others.GEOID.to_numpy(object))
    towns["miles_to_100k_city"] = miles_to_nearest(
        tlat, tlon, tid, big.INTPTLAT.to_numpy(float), big.INTPTLONG.to_numpy(float),
        big.GEOID.to_numpy(object))
    towns = towns[towns.miles_to_1k_town >= NEAR_TOWN_MILES]
    funnel.append((f"... at least {NEAR_TOWN_MILES} miles from any other place of "
                   f"{NEAR_TOWN_POP:,}+", len(towns)))
    towns = towns[towns.miles_to_100k_city >= BIG_CITY_MILES]
    funnel.append((f"... and at least {BIG_CITY_MILES} miles from any city of {BIG_CITY_POP:,}+",
                   len(towns)))
    towns = towns[(towns.tpop22 <= MAX_TOWN_POP) & (towns.tpop22 > 0)]
    funnel.append((f"... with 2022 population of at most {MAX_TOWN_POP:,}", len(towns)))

    # Match each town to the ZIP codes named for it, in each year.
    towns["key"] = towns.gaz_name.map(clean_name) + "|" + towns.USPS
    towns = towns[~towns.key.duplicated(keep=False)]
    funnel.append(("... with a name unique among the isolated towns of its state", len(towns)))
    zips = {yr: zip_cities(yr) for yr in YEARS}
    zips = {yr: z[z.key.isin(towns.key)] for yr, z in zips.items()}
    towns = towns[towns.key.isin(zips["00"].key) & towns.key.isin(zips["16"].key)]
    funnel.append(("... with a ZIP code named for the town in both the 2000 and 2016 ZBP",
                   len(towns)))
    for yr in YEARS:
        print(f"Matched {towns.key.isin(zips[yr].key).sum()} towns to "
              f"{zips[yr].key.isin(towns.key).sum()} ZIP codes in 20{yr}")

    # Hinterland: residents of the town's ZIP codes (ZCTAs, ACS 2018-22) living outside the town.
    zcta = acs[acs.GEO_ID.str.startswith("860Z200US")].copy()
    zcta["zip"] = zcta.GEO_ID.str[-5:]
    zcta["zpop"] = zcta.B01003_E001.astype(int)
    zp = zips["16"].merge(zcta[["zip", "zpop"]], on="zip", how="left").fillna({"zpop": 0})
    towns["zip_pop"] = towns.key.map(zp.groupby("key").zpop.sum())
    towns["opop22"] = (towns.zip_pop - towns.tpop22).clip(lower=0)

    # Establishment counts in the town's ZIP codes.
    for yr in YEARS:
        est = zip_establishments(yr)
        m = zips[yr].merge(est, left_on="zip", right_index=True, how="left").fillna(0)
        counts = m.groupby("key")[list(INDUSTRIES)].sum()
        for ind in INDUSTRIES:
            towns[f"{ind}{yr}"] = towns.key.map(counts[ind]).fillna(0).astype(int)
        towns[f"n_zips{yr}"] = towns.key.map(zips[yr].groupby("key").size()).fillna(0)

    counties = load_counties()
    towns = towns.merge(counties, on="county", how="left")
    # Earlier hinterlands: the 2022 hinterland scaled by the county's population ratio.
    for yr in ("00", "16"):
        towns[f"opop{yr}"] = towns.opop22 * towns[f"cpop{yr}"] / towns.cpop22
    need = ["tpop00", "tpop16"] + [f"{v}{y}" for v in ("pinc", "births", "opop") for y in YEARS]
    before = len(towns)
    towns = towns.dropna(subset=need)
    funnel.append(("... with town populations and county covariates in every year", len(towns)))
    print(f"Dropped {before - len(towns)} towns missing an estimate or a county covariate")

    towns = towns.rename(columns={"NAME": "town", "STNAME": "state", "USPS": "st",
                                  "INTPTLAT": "lat", "INTPTLONG": "lon"})
    cols = (["GEOID", "town", "state", "st", "county", "lat", "lon", "miles_to_1k_town",
             "miles_to_100k_city", "zip_pop"]
            + [f"{v}{y}" for y in YEARS for v in ("tpop", "opop", "cpop", "pinc", "births",
                                                  "n_zips")]
            + [f"{i}{y}" for y in YEARS for i in INDUSTRIES])
    towns = towns[cols].sort_values(["st", "town"])
    towns.to_csv(ROOT / "data" / "markets.csv", index=False, float_format="%.4f")
    pd.DataFrame(funnel, columns=["step", "towns"]).to_csv(OUT / "sample_funnel.csv", index=False)
    for step, n in funnel:
        print(f"  {n:>7,}  {step}")
    print(f"Wrote data/markets.csv ({len(towns)} towns in {towns.st.nunique()} states)")


if __name__ == "__main__":
    main()
