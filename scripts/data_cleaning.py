import re
import pandas as pd
import include.helper_functions as helper

"""
    This file reads the generated CSV file into a data frame
    and applies some cleaning and feature engineering to feed the data into
    a linear model.

    If the SPECPower data ever gets updated please walk this file manually
    from top to bottom.

    In the file some asserts are given, but also manual checks should be run
"""


def remove_unneeded_columns(df_original):
    df = df_original.copy()
    # Just for simplicity, remove columns that we currently do not need
    df = df.drop(
        ['100_ActualLoad', '100_ssj_ops', "100_PerfPowerRatio",
           '90_ActualLoad', '90_ssj_ops',  '90_PerfPowerRatio',
           '80_ActualLoad', '80_ssj_ops',  '80_PerfPowerRatio',
           '70_ActualLoad', '70_ssj_ops',  '70_PerfPowerRatio',
           '60_ActualLoad', '60_ssj_ops',  '60_PerfPowerRatio',
           '50_ActualLoad', '50_ssj_ops',  '50_PerfPowerRatio',
           '40_ActualLoad', '40_ssj_ops',  '40_PerfPowerRatio',
           '30_ActualLoad', '30_ssj_ops',  '30_PerfPowerRatio',
           '20_ActualLoad', '20_ssj_ops',  '20_PerfPowerRatio',
           '10_ActualLoad', '10_ssj_ops',  '10_PerfPowerRatio'], axis=1)
    helper.columns_diff(df, df_original)
    return df

def split_hardware_availabilty(df_original):
    df = df_original.copy()

    availability = df["Hardware_Availability"].str.split("-", expand=True)
    df["Hardware_Availability_Month"] = availability[0]
    df["Hardware_Availability_Year"]  = availability[1]
    df["Hardware_Availability_Year"] =  df["Hardware_Availability_Year"].astype(int)

    return df

def melt_power_and_load(df_original):
    df = df_original.copy()

    melt_columns = ['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
           '60_AvgPower', '50_AvgPower', '40_AvgPower', '30_AvgPower',
           '20_AvgPower', '10_AvgPower', 'ActiveIdle']
    remaining_columns = df.columns[~df.columns.isin(melt_columns)]

    df = df.melt(
        id_vars=remaining_columns,
        value_vars=melt_columns,
        var_name='utilization',
        value_name="power",
    )

    helper.columns_diff(df, df_original)
    return df

def clean_power_and_load(df_original):
    df = df_original.copy()
    df.utilization = df.utilization.str.replace('ActiveIdle', '0')
    df.utilization = df.utilization.str.replace('100_AvgPower', '100')
    df.utilization = df.utilization.str.replace('90_AvgPower', '90')
    df.utilization = df.utilization.str.replace('90_AvgPower', '90')
    df.utilization = df.utilization.str.replace('80_AvgPower', '80')
    df.utilization = df.utilization.str.replace('70_AvgPower', '70')
    df.utilization = df.utilization.str.replace('60_AvgPower', '60')
    df.utilization = df.utilization.str.replace('50_AvgPower', '50')
    df.utilization = df.utilization.str.replace('40_AvgPower', '40')
    df.utilization = df.utilization.str.replace('30_AvgPower', '30')
    df.utilization = df.utilization.str.replace('20_AvgPower', '20')
    df.utilization = df.utilization.str.replace('10_AvgPower', '10')

    df.utilization = df.utilization.astype(int)
    helper.same_column_diff(df, df, 'utilization')


    return df


def create_cpu_make(df_original):
    df = df_original.copy()
    df["CPUMake"] = None

    assert df.loc[(df['HW_CPUName'].str.contains("Intel", case=False)) & (df['HW_CPUName'].str.contains("AMD", case=False)), "CPUMake"].empty # Intel and AMD never in one column

    df.loc[df['HW_CPUName'].str.contains("Intel"), "CPUMake"] = "intel"
    df.loc[df['HW_CPUName'].str.contains("AMD"), "CPUMake"] = "amd"


    ## How many do we have left?
    df[df.CPUMake.isna()].HW_CPUName

    ## Currently we only see the Xeon L5420 @Dan: Was not specific
    df.loc[df.HW_CPUName== "Xeon L5420", "CPUMake"] = "intel"

    ## The ARM servers. The Grace name does not contain the vendor
    df.loc[df['HW_CPUName'].str.contains("Ampere"), "CPUMake"] = "ampere"
    df.loc[df['HW_CPUName'].str.contains("Grace"), "CPUMake"] = "nvidia"

    helper.new_column_diff(df, 'HW_CPUName', 'CPUMake')


    # All the makes should now be known
    assert set(df['CPUMake'].unique()) == {"intel", "amd", "ampere", "nvidia"}, f"CPUMake contained unknown vendors: {df['CPUMake'].unique()}"

    return df

def create_cpu_name(df_original):
    df = df_original.copy()

    df['CPUName'] = df['HW_CPUName']


    ## Now remove the vendor from the column and generate a new
    df['CPUName'] = df['CPUName'].str.replace(r'Intel\s*', "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r'AMD\s*', "", regex=True, flags=re.IGNORECASE)


    # Must be done before the frequency is removed, as this glues "8534P 2.30 GHz 64-core" together to "8534P64-core"
    df['CPUName'] = df['CPUName'].str.replace(r"\w+-Core\s*", "", regex=True,flags=re.IGNORECASE) # remove Quad-Core etc.
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Intel\s*Turbo\s*Boost\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Turbo\s*Boost\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Turbo\s*CORE\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*\d+\.\d*\s*GHz\s*\)", "", regex=True,flags=re.IGNORECASE) # remove only frequency
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*r\s*\)", "", regex=True,flags=re.IGNORECASE) # remove (r)
    df['CPUName'] = df['CPUName'].str.replace(r"Processor\s*", "", regex=True,flags=re.IGNORECASE) # remove Processor
    df['CPUName'] = df['CPUName'].str.replace(r"@?\s*\d+\.\d*\s*GHz\s*", "", regex=True,flags=re.IGNORECASE) # remove @ 2.3 GHz
    df['CPUName'] = df['CPUName'].str.replace(r"CPU\s*", "", regex=True,flags=re.IGNORECASE) # remove CPU
    df['CPUName'] = df['CPUName'].str.replace(r",\s*", "", regex=True,flags=re.IGNORECASE) # remove ,

    df['CPUName'] = df['CPUName'].str.replace(r"[®™]|64-Bit\s*", "", regex=True,flags=re.IGNORECASE) # remove ® and the 64-Bit of the Ampere CPUs

    # Unique cases
    df['CPUName'] = df['CPUName'].str.replace("Dell SKU [338-BNCG]", "", regex=False) # remove special case Dell SKU [338-BNCG]
    df['CPUName'] = df['CPUName'].str.replace("Xeon E E-", "Xeon E-", regex=False) # Xeon E is the product line and already part of the model number
    df.loc[df.CPUName == 'X3350', 'CPUName'] = 'xeonx3350'
    df.loc[df.CPUName == 'E3-1260L v5', 'CPUName'] = 'xeone3-1260lv5'
    df.loc[df.CPUName == 'Xeon', 'CPUName'] = 'xeon-undefined' # move to XeonUNDEFINED so the model will later have no false-positive match for "Xeon"

    df['CPUName'] = df['CPUName'].str.replace(r"\s*", "", regex=True) # normalize
    df.CPUName = df.CPUName.str.lower() # normalize

    known_cpus = r"opteron|xeon|epyc|pentium|corei3|corei5|corei7|coreultra|amperealtra|grace"
    assert df[~df.CPUName.str.match(known_cpus)].CPUName.empty, f"Unknown processors in CPUName apart from {known_cpus}: {df[~df.CPUName.str.match(known_cpus)].CPUName.unique()}"

    assert df[df['CPUName'].str.contains('(', regex=False)].empty, "Still brackets () in CPUName"

    # validate what we have as uniques
    helper.visual_check(df.CPUName.unique(), "All names ok?") #DEBUG

    helper.new_column_diff(df, 'HW_CPUName', 'CPUName')

    return df

def create_turbo_boost(df_original):
    df = df_original.copy()

    ## look at all the brackets and try to spot pattern.
    df.HW_CPUName.str.match(r".*\(\s*Turbo.*")

    ## how many? A: 41
    df.loc[df.HW_CPUName.str.match(r".*\(\s*Turbo.*"), 'HW_CPUName'].count()

    # Create TurboBoost column
    df["TurboBoostGHz"] = None

    # Check HW_CPUName column / count
    df.loc[df['HW_CPUName'].str.match(r".*\(.*Turbo.*\)"), 'HW_CPUName'].count()
    df.loc[df['HW_CPUName'].str.match(r".*\(.*up to (.*)GHz.*"), 'HW_CPUName'].count()

    # Fill column from CPU Name data
    df['TurboBoostGHz'] = df['HW_CPUName'].str.extract(r".*\(.*up to (\d+\.\d+)\s*GHz.*")
    df[df['TurboBoostGHz'].notna()] # How many do we have

    helper.new_column_diff(df, 'HW_CPUName', 'TurboBoostGHz')

    return df

# X cores, X chips, X cores/chip
def make_cpu_cores(df_original):
    df = df_original.copy()
    df['CPUCores'] = df.HW_CPUsEnabled.str.extract(r"^\s*(\d+)\s*cores?\s*,.*", flags=re.IGNORECASE).astype(int)
    assert df[df.CPUCores.isna()].empty , "CPUCores contains NA"
    helper.new_column_diff(df, 'CPUCores', 'HW_CPUsEnabled')
    # recover original column
    df.HW_CPUsEnabled = df_original.HW_CPUsEnabled
    return df

def make_cpu_chips(df_original):
    df = df_original.copy()
    df['CPUChips'] = df.HW_CPUsEnabled.str.extract(r".*,\s*(\d+)\s*chips?,.*", flags=re.IGNORECASE).astype(int)
    assert df[df.CPUChips.isna()].empty, "CPUChips contains NA"
    helper.new_column_diff(df, 'CPUChips', 'HW_CPUsEnabled')
    df.HW_CPUsEnabled = df_original.HW_CPUsEnabled
    return df


# 8 (2 / core)
# first number relevant
# second number can be figured out from this / total cores, so shouldn't be needed
# write code to double check that first, similar to FREQ comparision code

def make_hardware_threads(df_original):
    df = df_original.copy()
    df.HW_HardwareThreads.unique() # DEBUG
    df['CPUThreads'] = df.HW_HardwareThreads.str.extract(r"^\s*(\d+)\s*\(.*").astype(int)
    thread_per_core = df['CPUThreads']  / df['CPUCores']
    thread_per_core_extract = df.HW_HardwareThreads.str.extract(r"\((\d+)\s*\/\s*core\)", expand=False, flags=re.IGNORECASE).dropna().astype(int)
    assert thread_per_core.eq(thread_per_core_extract).all(), "Threads per core was not equal to comparison via calculation"

    return df

# can be split into 2 easily
#   2 x 700W
#   1 x 1100
# NumOfPSU, PSURating
def split_psu(df_original):
    df = df_original.copy()

    df.HW_PSUQuantAndRating.unique()

    df['NumOfPSU'] = df.HW_PSUQuantAndRating.str.extract(r"^\s*(\d+)\s*x.*")
    df['NumOfPSU'] = df['NumOfPSU'].astype('Int64')
    df['PSURating'] = df.HW_PSUQuantAndRating.str.extract(r".*x\s*(\d+).*").astype('Int64')
    df['PSURating'] = df['PSURating'].astype('Int64')

    ## Assert that all is good here
    # well since some of them are actually empty, not sure what to actually check for

    # 7 (77 expanded) rows are empty is allowed with the specified hashes ...
    # but somehow the hash column is gone and I cannot reference it ... why?
    #assert df.drop(df.hash)[df.NumOfPSU.isna()].empty
    #assert df[df.PSURating.isna()].empty

    assert df.NumOfPSU.isna().sum() == 7, f"PSU was not 7: {df.NumOfPSU.isna().sum()}"
    return df


## Column with cpu family
# do by known names - Xeon, Opteron, etc.
## Xeon , Opteron , EPYC ,
# do unique, figure it out from there
def make_cpu_family(df_original):
    df = df_original.copy()
    df['CPUFamily'] = None
    pat = r"xeon|opteron|epyc|i3|i5|coreultra|pentium|altra|grace"

    assert df.loc[~df['CPUName'].str.contains(pat, regex=True)].CPUName.empty, "Unknown family found"


    possible_families = [
        df.loc[df['CPUName'].str.contains("xeon"), "CPUName"],
        df.loc[df['CPUName'].str.contains("opteron"), "CPUName"],
        df.loc[df['CPUName'].str.contains("epyc"), "CPUName"],
        df.loc[df['CPUName'].str.contains("i3"), "CPUName"],
        df.loc[df['CPUName'].str.contains("i5"), "CPUName"],
        df.loc[df['CPUName'].str.contains("coreultra"), "CPUName"],
        df.loc[df['CPUName'].str.contains("pentium"), "CPUName"],
        df.loc[df['CPUName'].str.contains("altra"), "CPUName"],
        df.loc[df['CPUName'].str.contains("grace"), "CPUName"]
    ]

    for i, possible_family in enumerate(possible_families):
        for j in range(i+1, len(possible_families)):
            # print(f"Checking {possible_family.iloc[0]} and {possible_families[j].iloc[0]}")
            assert possible_family.index.intersection(possible_families[j].index).empty, f"Possible families had overlap - between {possible_family.iloc[0]} and {possible_families[j].iloc[0]}"


    ## CPUFamily fill
    df.loc[df['CPUName'].str.contains("xeon"), "CPUFamily"] = "xeon"
    df.loc[df['CPUName'].str.contains("opteron"), "CPUFamily"] = "opteron"
    df.loc[df['CPUName'].str.contains("epyc"), "CPUFamily"] = "epyc"
    df.loc[df['CPUName'].str.contains("i3"), "CPUFamily"] = "core-i3"
    df.loc[df['CPUName'].str.contains("i5"), "CPUFamily"] = "core-i5"
    df.loc[df['CPUName'].str.contains("coreultra"), "CPUFamily"] = "core-ultra"
    df.loc[df['CPUName'].str.contains("pentium"), "CPUFamily"] = "pentium"
    df.loc[df['CPUName'].str.contains("altra"), "CPUFamily"] = "altra"
    df.loc[df['CPUName'].str.contains("grace"), "CPUFamily"] = "grace"

    ## Assert CPU Family

    assert df.CPUFamily.isna().sum() == 0, "CPUFamily contained NA"
    return df


def make_l2_cache(df_original):
    df = df_original.copy()
    ## L2 Cache
    df['L2CacheKB'] = None
    mb_pat_l2=r'^\s*(?P<L2Cache>\d+)\s*mb' # remember flags=re.IGNORECASE)
    kb_pat_l2=r'^\s*(?P<L2Cache>\d+)\s*kb' # remember flags=re.IGNORECASE)
    mb_l2 = df.HW_SecondaryCache.str.extract(mb_pat_l2, flags=re.IGNORECASE).astype('float') * 1000
    kb_l2 = df.HW_SecondaryCache.str.extract(kb_pat_l2, flags=re.IGNORECASE).astype('float')
    df['L2CacheKB'] = mb_l2
    df['L2CacheKB'] = df['L2CacheKB'].fillna(kb_l2['L2Cache'])
    assert df['L2CacheKB'].isna().any() == False, "L2Cache contained empties"
    # Only the number is read, not "per core" or "per chip". So it must be the value per core. Otherwise add a patch in spec_data_patches.csv
    assert df[df['L2CacheKB'] > 4000].empty, f"L2Cache bigger than 4 MB per core. Is a patch needed? {df[df['L2CacheKB'] > 4000].CPUName.unique()}"

    return df

def make_l3_cache(df_original):
    df = df_original.copy()
    ## L3 Cache, as #
    df['L3CacheKB'] = None
    mb_pat_l3=r'^\s*(?P<L3Cache>\d+)\s*mb' # remember case=False
    kb_pat_l3=r'^\s*(?P<L3Cache>\d+)\s*kb' # remember case=False
    mb_l3 = df.HW_TertiaryCache.str.extract(mb_pat_l3, flags=re.IGNORECASE).astype('float') * 1000
    kb_l3 = df.HW_TertiaryCache.str.extract(kb_pat_l3, flags=re.IGNORECASE).astype('float')
    df['L3CacheKB'] = mb_l3
    df['L3CacheKB'] = df['L3CacheKB'].fillna(kb_l3['L3Cache'])

    # Typos like 39424 MB instead of KB belong in spec_data_patches.csv
    assert df[df['L3CacheKB'] > 39423000.0].empty, f"Very big L3Cache. Is a patch needed? {df[df['L3CacheKB'] > 39423000.0].CPUName.unique()}"
    assert df['L3CacheKB'].isna().sum() == 6, f"L3Cache did not contain 6 empties: {df['L3CacheKB'].isna().sum()}"

    return df


def upper_bound_watts(value):
    # Specs can be a single value (280W) or unclear (155W / 170W, 35-54W, 45+W). We correct for that to the upper bound
    if pd.isna(value):
        return float('nan')
    return max(float(watts) for watts in re.findall(r"\d+(?:\.\d+)?", value))

def assert_no_conflicting_tdps(tdps):
    conflicts = tdps[tdps.groupby("Model").TDP.transform("nunique") > 1]
    assert conflicts.empty, f"Found conflicting info for processor type and TDP: {conflicts}"

def get_amd_tdps():
    amd = pd.concat([
        pd.read_csv("../cpu-spec-sheets/amd_server.csv"),
        pd.read_csv("../cpu-spec-sheets/amd_client.csv"),
    ], ignore_index=True)

    # Only named after family and model: "AMD EPYC™ 9654" => epyc9654, the same as our CPUName
    amd['Model'] = amd.Name.str.replace(r"AMD|APU|™|\s+", "", regex=True).str.lower()

    amd['TDP'] = amd['Default TDP'].map(upper_bound_watts)
    # Newer EPYC models only have "600W (CPU Power Range: 400W-600W)". The first value is the default.
    amd['TDP'] = amd['TDP'].fillna(amd['Default CPU Power'].str.extract(r"^\s*(\d+)\s*W", expand=False).astype(float))

    # Not all processors in the client list have a TDP
    amd = amd.dropna(subset=['TDP'])
    assert_no_conflicting_tdps(amd)

    return amd.loc[:, ['Model', 'TDP']].drop_duplicates(subset=['Model'])

# Names in SPECPower are inconsistent regarding the Xeon product lines (Intel Xeon 8480+, Intel Xeon Platinum 8480+)
# and sometimes even wrong (Intel Xeon Gold 6780E). So we only compare the model numbers. They are unique for Intel.
def normalize_intel_model(names):
    return names.str.lower().str.replace(r"\(.*\)|intel|xeon|gold|platinum|silver|bronze|processor|cpu|core|®|™|\s+", "", regex=True)

def get_intel_tdps():
    rows = []
    wrapped_name = ''

    # Despite the file extension the columns are separated by four spaces
    with open("../cpu-spec-sheets/intel.tsv", encoding='UTF8') as f:
        header = f.readline().rstrip("\n").split("    ")
        for line in f:
            fields = line.rstrip("\n").split("    ")
            if len(fields) == 1: # Some product names are wrapped onto a second line
                wrapped_name = fields[0]
                continue
            assert len(fields) == len(header), f"Wrong number of columns in Intel spec sheet: {line}"
            fields[0] = f"{wrapped_name} {fields[0]}"
            wrapped_name = ''
            rows.append(fields)

    intel = pd.DataFrame(rows, columns=header)
    intel['Model'] = normalize_intel_model(intel['Product Name'])
    intel['TDP'] = intel['TDP'].map(upper_bound_watts)

    assert intel.TDP.isna().sum() == 0, f"TDP was null for the following models: {intel.loc[intel.TDP.isna(), 'Product Name']}"
    assert_no_conflicting_tdps(intel)

    return intel.loc[:, ['Model', 'TDP']].drop_duplicates(subset=['Model'])

# This function gets the TDP from the spec sheets of AMD and Intel in cpu-spec-sheets/
# It leaves the TDP empty for the CPUs not in there. These are filled by add_tdp_from_lookup()
def make_tdp_old(df_original):
    df = df_original.copy()

    amd_tdps = get_amd_tdps().set_index('Model').TDP
    intel_tdps = get_intel_tdps().set_index('Model').TDP

    df["TDP"] = float('nan')

    is_amd = df.CPUMake == "amd"
    is_intel = df.CPUMake == "intel"
    df.loc[is_amd, "TDP"] = df.loc[is_amd, "CPUName"].map(amd_tdps)
    df.loc[is_intel, "TDP"] = normalize_intel_model(df.loc[is_intel, "CPUName"]).map(intel_tdps)

    return df

# Fills the TDP of the CPUs that are in no spec sheet. See the README on how the file is maintained.
def add_tdp_from_lookup(df_original):
    df = df_original.copy()

    lookup = pd.read_csv("../data-updates/cpu_tdp_lookup.csv")
    assert lookup.CPUName.is_unique, f"Duplicate CPUs in the TDP lookup: {lookup[lookup.CPUName.duplicated()].CPUName.tolist()}"
    assert lookup[lookup.TDP.notna() & lookup.Source.isna()].empty, f"TDP without Source in the TDP lookup: {lookup[lookup.TDP.notna() & lookup.Source.isna()].CPUName.tolist()}"

    in_spec_sheets = lookup[lookup.CPUName.isin(df[df.TDP.notna()].CPUName)].CPUName.tolist()
    assert not in_spec_sheets, f"These CPUs are in the spec sheets now. Please remove them from the TDP lookup: {in_spec_sheets}"

    df["TDP"] = df.TDP.fillna(df.CPUName.map(lookup.set_index("CPUName").TDP))

    new_cpus = df[df.TDP.isna() & ~df.CPUName.isin(lookup.CPUName)].CPUName.unique()
    print(f"\nCPUs that are in no spec sheet and not in cpu_tdp_lookup.csv yet: {len(new_cpus)}")
    for cpu in new_cpus:
        print(cpu)

    return df

def report_missing_tdp(df):
    missing = df[df.TDP.isna()]

    print(f"\nTDP is missing for {len(missing)} of {len(df)} results")

    print("\nBy year of hardware availability:")
    by_year = df.groupby("Hardware_Availability_Year").TDP.agg(total="size", matched="count")
    by_year["missing"] = by_year.total - by_year.matched
    print(by_year.to_string())

    print("\nBy CPU make:")
    by_make = df.groupby("CPUMake").TDP.agg(total="size", matched="count")
    by_make["missing"] = by_make.total - by_make.matched
    print(by_make.to_string())

    print("\nCPUs without TDP (name, number of results):")
    print(missing.CPUName.value_counts().to_string())

# Currently not used. It scrapes Wikipedia, which needs network access.
def make_tdp_wikipedia(df_original):
    df = df_original.copy()

    cpus = pd.DataFrame(columns=["ModelNumber", "TDP"])

    urls = {
        "opteron" : "https://en.wikipedia.org/wiki/List_of_AMD_Opteron_processors",
        "core" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Core-based)",
        "nehalem" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Nehalem-based)",
        "sandybridge" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Sandy_Bridge-based)",
        "ivybridge" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Ivy_Bridge-based)",
        "haswell" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Haswell-based)",
        "broadwell" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Broadwell-based)",
        "skylake" :"https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Skylake-based)",
        "kabylabe" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Kaby_Lake-based)",
        "coffeelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Coffee_Lake-based)",
        "cascadelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Cascade_Lake-based)",
        "cometlake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Comet_Lake-based)",
        "icelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Ice_Lake-based)",
        "rocketlake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Rocket_Lake-based)",
        "tigerlake" : "https://en.wikipedia.org/wiki/Tiger_Lake#List_of_Tiger_Lake_CPUs",
        "epyc" : "https://en.wikipedia.org/wiki/Epyc",
        "cooperlake" : "https://en.wikipedia.org/wiki/Cooper_Lake_(microprocessor)#List_of_Cooper_Lake_processors",
        "netburst" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(NetBurst-based)",
    }

    for name, url in urls.items():
        print(name)
        tables = pd.read_html(url)

        for table in tables:

            # normalize different header names
            table = table.rename({'Model number': 'ModelNumber', 'TDP(W)': 'TDP'}, axis=1)
            table = table.rename({'Modelnumber': 'ModelNumber', 'TDP (W)': 'TDP'}, axis=1)
            table = table.rename({'Model': 'ModelNumber'}, axis=1)
            table = table.rename({'Modelnumber[7]': 'ModelNumber'}, axis=1)

            if 'ModelNumber' in table.columns:
                table.columns = table.columns.get_level_values(0)
                # print("Found Table", table.iloc[0], table.columns)
                cpus = pd.concat([table.loc[:, ["ModelNumber", "TDP"]], cpus], ignore_index=True, axis=0, join="outer")

    # Remove header columns where ModelNumber = TDP
    cpus = cpus.drop(cpus[cpus.ModelNumber == cpus.TDP].index)

    cpus_save = cpus.copy()
    cpus = cpus_save.copy()



    cpus[cpus.TDP.astype(str).str.contains(",")] # DEBUG
    cpus[cpus.ModelNumber.astype(str).str.contains(r"\[",regex=True)].to_dict() # DEBUG


    # Unique replacements without pattern
    cpus.TDP = cpus.TDP.str.replace("^80,20W$", "80", regex=True)
    cpus.TDP = cpus.TDP.str.replace(r"^\s*80\s*,\s*120\s*W$", "120", regex=True)
    cpus.TDP = cpus.TDP.str.replace(r"^\s*150\s*,\s*120\s*W$", "150", regex=True)
    cpus.TDP = cpus.TDP.str.replace("^92.6 68$", "92.6", regex=True)

    # Replacements with spotted pattern
    cpus.TDP = cpus.TDP.str.replace(r"^\s*\d+\s*/(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace(r"^\s*\d+\s*W\s*(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace(r"^\s*\d+\s*-\s*(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace(r"^\s*\d+\s*–\s*(\d+)\s*\s*$", r"\1",regex=True) # Note this is a UTF-8 hyphen!


    #replace weird bracketing, but only for 24 knowns
    assert cpus[cpus.ModelNumber.astype(str).str.contains(r"\[",regex=True)].shape[0] == 24, "More than 24 brackets in ModelNumber. Please manually verify that new ones are also OK"
    cpus.ModelNumber = cpus.ModelNumber.str.replace(r"\[\d*\]", "",regex=True)


    # normalizing
    cpus.ModelNumber = cpus.ModelNumber.str.replace(r"\s*", "",regex=True).str.lower()
    cpus.TDP = cpus.TDP.str.replace(r"\s*W\s*", "",regex=True, flags=re.IGNORECASE)

    unknown_cpus_selector = cpus.TDP.astype(str).str.contains("?", regex=False)
    assert cpus.loc[unknown_cpus_selector].shape[0] == 2, f"More than two unknown processors with ? in TDP found: {cpus.loc[unknown_cpus_selector]}"
    cpus = cpus.drop(cpus[unknown_cpus_selector].index, axis=0)


    assert cpus.ModelNumber.isna().sum() == 0, "ModelNumber contained more than 0 NAs!"
    assert cpus.TDP.isna().sum() == 10, f"TDPcontained more than 10 NAs: {cpus[cpus.TDP.isna()]}" # 10 NA is ok

    # For these 10 the TDP we just don't have ...
    cpus = cpus.dropna()


    cpus.TDP = cpus.TDP.astype(float)


    # Fix the known processors where we have confilicting values by setting to the highes
    # TDP value we know
    cpus["TDP"] = cpus.groupby(["ModelNumber"]).TDP.transform("max")
    # now remove the duplicates
    cpus = cpus.drop_duplicates(subset=["ModelNumber"])

    clean_names = df.CPUName.str.replace(r"opteron", "", regex=True)
    for i, clean_name in clean_names.items():
        if cpus[cpus.ModelNumber == clean_name].empty:
            print("No match for", clean_name)
            continue
        found = cpus[cpus.ModelNumber == clean_name]
        assert len(found) < 2, f"Found multiple TDPs: {cpus[cpus.ModelNumber == clean_name]}"

        df.loc[i,'TDP'] = found.iloc[0].TDP # Insert TDP in any case

    return df


""" This function is just a helper function which is used during analysing
the SUT_BIOS and SUT_Notes columns.

The functionality to create new columns from that knowledge has been coded
into def make_feature_columns()

This function should only be used when new data to SPECPower is added

"""
def helper_for_bios_and_notes(df):
    df = pd.read_csv("./../data/spec_data_cleaned_unmelted.csv")

    # Prints the settings that the regexes do not classify. They need a manual look if a new setting is relevant
    def check_classified(name, c_new, a, b):
        print(f"\n{name} not classified:", sorted(c_new.difference(set(a.index).union(set(b.index)))))


    mylist = df.SUT_BIOS.tolist()
    mylist += df.SUT_Notes.tolist()
    items = []
    for item in mylist:
        if pd.isna(item): continue
        items.extend(item.split(";;;"))
    item_series = pd.Series(items).value_counts()
    pd.set_option('display.max_rows', None)

    item_series.index.nunique() # 1243 items ... this is too much too inspect


    # manual visual checking beforhand
    # We limit down to the ones with more than 5 occurences and manually try to find interesting ones
    item_series[item_series.values > 5].index.tolist()

    # Back from manual checking.
    # We found very many interesting settings that deserve the creation of
    # a dummy variable.


    #'Memory Frequency set to DDR3-1333MHz.',
    #'Set "DDR Performance = Power balanced" in BIOS.',
    #'DRAM Controller Power Down: Enabled',
    #'DRAM Power Down Enable = Enabled',
    #'Memory clock speed = 1333 MHz',
    #'SMEE = Disabled', -> Secure Memory Encryptoion Enable
    item_series[item_series.index.str.match(r".*(memory|ddr|dram|smee)", case=False)].shape


    #'Intel HT Technology -enabled (default).',
    #'Hyper Threading Technology: Enabled',
    #'HT Technology: enabled',
    a = item_series[item_series.index.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*enabled", case=False)]
    b = item_series[item_series.index.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*disabled", case=False)]
    c = item_series[item_series.index.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)", case=False)] #unknown status
    c_new = set(c.index)
    check_classified("Hyper Threading", c_new, a, b)



    #'Intel Virtualization (Intel VT): Disabled',
    #'SVM disabled' -> AMD equivalent
    #'VT-x: Disabled'
    a = item_series[item_series.index.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*enable", case=False)]
    b = item_series[item_series.index.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*disable", case=False)]
    c = item_series[item_series.index.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)", case=False)]
    c_new = set(c.index)
    c_new.discard("Memory Patrol Scrubbing: DisabledVirtualization Options") # This one is known bogus

    check_classified("Virtualization", c_new, a, b)


    'Intel Turbo Boost enabled<C1E enabled<C States enabled',
    'Set &quot;Intel Turbo Boost Technology = Disabled&quot; in BIOS.',
    'Set "Turbo = Disabled" in BIOS.',
    'Turbo Boost was disabled in BIOS.',
    'AMD Fmax Boost Limit Control: Manual',
    'Core Performance Boost = Disabled',
    'Turbo mode Disabled.',
    'AMD Core Performance Boost: Disabled',


    a = item_series[item_series.index.str.match(r".*(Turbo\s*Boost)[^,.<;]*enabled", case=False)]

    b = item_series[item_series.index.str.match(r".*(Turbo\s*Boost)[^,.<;]*(disabled|disable$)", case=False)]
    b2 = item_series[item_series.index.str.match(r".*(Manual Boost FMax set to 2200)", case=False)]
    b3 = item_series[item_series.index.str.match(r".*disable.*boost", case=False)]
    b4 = item_series[item_series.index.str.match(r".*boost.*limit", case=False)]
    b5 = item_series[item_series.index.str.match(r".*boost fmax set to manual", case=False)]
    b6 = item_series[item_series.index.str.match(r"Core Performance Boost: Disable</UL>", case=False)]
    b7 = item_series[item_series.index.str.match(r"Set &quot;Intel Turbo Boost Technology = Disable&quot; in BIOS.", case=False)]
    b8 = item_series[item_series.index.str.match(r".*(Turbo Mode)[^,.<;]*disabled", case=False)]
    b9 = item_series[item_series.index.str.match(r".*Disable(d)? \"?Turbo", case=False)]
    b10 = item_series[item_series.index.str.match(r"&quot;Turbo Mode&quot; was disabled in BIOS.", case=False)]
    b11 = item_series[item_series.index.str.match(r"Turned off &quot;TURBO mode&quot; in BIOS.", case=False)]

    b = pd.concat([b, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11])
    c = item_series[item_series.index.str.match(r".*(Turbo\s*Boost|Turbo Mode)", case=False)] #unknown status
    c_new = set(c.index)
    c_new.discard("Turbo Boost Technology ") # This one is known bogus

    check_classified("Turbo Boost", c_new, a, b)


    'Package C State: No Limit',
    'C-State Efficiency Mode: Enabled',
    'Data Fabric C-State Enable: Force Enabled',
    'C States enabled',
    'Enhanced Halt State'
    r'C\d+'
    'Package C State limit set to No Limit.'
    a = item_series[item_series.index.str.match(r".*(C.State)[^,.<;]*(enabled|enable[\".\s]*|no limit|auto|c3|c6)", case=False)]
    a2 = item_series[item_series.index.str.match(r"Enable \"*CPU C-states\"*", case=False)]
    a = pd.concat([a, a2])

    b = item_series[item_series.index.str.match(r".*(C.State)[^,.<;]*disabled", case=False)]

    c = item_series[item_series.index.str.match(r".*(C6)", case=False)] #unknown status
    c_new = set(c.index)

    check_classified("C States", c_new, a, b)


    # P-states are a power feature. P-State = 1 is the base frequency
    # Setting P-states to off will set P-State to max non-turbo (aka 1) (https://www.thomas-krenn.com/en/wiki/Disable_CPU_Power_Saving_Management_in_BIOS)
    # All P-States greater than 1 are power efficient states: https://www.thomas-krenn.com/en/wiki/Processor_P-states_and_C-states
    "SOC P-states: P3"
    item_series[item_series.index.str.match(r".*(P.State)[^,.<;]*(P2|P3)", case=False)]




     #"Hardware Prefetcher = Disabled"
     #Adjacent Cache Line Prefetch
     #MLC Spatial Prefetcher
     #Spatial prefetch
     #MLC Streamer
     #Data Reuse Prefetcher
     #Adjacent Cache Line Prefetch
     #DCU Prefetcher
     #L1 Stream HW Prefetcher
     #Adjacent Sector Prefetch = Disable

    a = item_series[item_series.index.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*disable", case=False)]
    b = item_series[item_series.index.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*enable", case=False)]


    c = item_series[item_series.index.str.match(r".*prefetch", case=False)]
    c_new = set(c.index)
    c_new.discard('Disable L1 Cache Stream Prefetchers')
    c_new.discard('HW Prefetcher')
    c_new.discard('DCU Stream Prefetcher')
    c_new.discard('Disable L2 Cache Stream Prefetchers')
    c_new.discard('Disable Processor Data Prefetch')
    c_new.discard('Adjacent Sector Prefetch')
    c_new.discard('Disabled Adjacent Cache Line Prefetch in BIOS.')
    c_new.discard('LLC Prefetcher''Disabled DCU Streamer Prefetcher in BIOS.')
    c_new.discard('XPT Prefetcher')
    c_new.discard('Disabled Hardware Prefetcher in BIOS.')
    c_new.discard('DCU IP Prefetcher')
    c_new.discard('Sub-NUMA Clustering: EnabledProcessor Prefetcher Options')
    c_new.discard('Disable "Processor Data Prefetch"')
    c_new.discard('LLC Prefetcher')
    c_new.discard('Disabled DCU Streamer Prefetcher in BIOS.')

    check_classified("Prefetchers", c_new, a, b)


def make_bios_features(df_original):

    df = df_original.copy()

    df.loc[df.SUT_BIOS.isna(), "SUT_BIOS"] = "--" # Move none to empty string so we can make operations on them
    df.loc[df.SUT_Notes.isna(), "SUT_Notes"] = "--" # Move none to empty string so we can make operations on them


    df["BIOS_Memory_Setting_Changed"] = None
    df.loc[df.SUT_Notes.str.match(r".*(dram|memory|ddr)\s*frequency", case=False), "BIOS_Memory_Setting_Changed"] = True

    df.loc[df.SUT_BIOS.str.match(r".*(memory|ddr|dram|smee)", case=False), "BIOS_Memory_Setting_Changed"] = True
    # There is no category for "False" since no infos are give like "memory timings default". So we resort to None as fallback
    df["BIOS_Memory_Setting_Changed"].count()


    df["BIOS_HT_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*enabled", case=False), "BIOS_HT_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*disabled", case=False), "BIOS_HT_Enabled"] = False

    df.loc[df.SUT_BIOS.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*enabled", case=False), "BIOS_HT_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*(Intel Hyper|Intel HT|Hyper.*Thread|HT Tech)[^,.<;]*disabled", case=False), "BIOS_HT_Enabled"] = False
    df["BIOS_HT_Enabled"].count()


    df["BIOS_VT_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*enable", case=False), "BIOS_VT_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*disable", case=False), "BIOS_VT_Enabled"] = False

    df.loc[df.SUT_BIOS.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*enable", case=False), "BIOS_VT_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*(AMD-V|SVM|VT|VT-x|Virtualization)[\s:=]*(Technology)?\s*disable", case=False), "BIOS_VT_Enabled"] = False
    df["BIOS_VT_Enabled"].count()


    df["BIOS_Turbo_Boost_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*(Turbo\s*Boost)[^,.<;]*enabled", case=False), "BIOS_Turbo_Boost_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r".*(Turbo\s*Boost)[^,.<;]*(disabled|disable$)", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*(Manual Boost FMax set to 2200)", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*disable.*boost", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*boost.*limit", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*boost fmax set to manual", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r"Core Performance Boost: Disable</UL>", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r"Set &quot;Intel Turbo Boost Technology = Disable&quot; in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*(Turbo Mode)[^,.<;]*disabled", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disable(d)? \"?Turbo", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r"&quot;Turbo Mode&quot; was disabled in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r"Turned off &quot;TURBO mode&quot; in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False

    df.loc[df.SUT_BIOS.str.match(r".*(Turbo\s*Boost)[^,.<;]*enabled", case=False), "BIOS_Turbo_Boost_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*(Turbo\s*Boost)[^,.<;]*(disabled|disable$)", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*(Manual Boost FMax set to 2200)", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*disable.*boost", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*boost.*limit", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*boost fmax set to manual", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r"Core Performance Boost: Disable</UL>", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r"Set &quot;Intel Turbo Boost Technology = Disable&quot; in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*(Turbo Mode)[^,.<;]*disabled", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disable(d)? \"?Turbo", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r"&quot;Turbo Mode&quot; was disabled in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r"Turned off &quot;TURBO mode&quot; in BIOS.", case=False), "BIOS_Turbo_Boost_Enabled"] = False
    df["BIOS_Turbo_Boost_Enabled"].count()


    df["BIOS_C_States_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*(C.State)[^,.<;]*(enabled|enable[\".\s]*|no limit|auto|c3|c6)", case=False), "BIOS_C_States_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r"Enable \"*CPU C-states\"*", case=False), "BIOS_C_States_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r".*(C.State)[^,.<;]*disabled", case=False), "BIOS_C_States_Enabled"] = False

    df.loc[df.SUT_BIOS.str.match(r".*(C.State)[^,.<;]*(enabled|enable[\".\s]*|no limit|auto|c3|c6)", case=False), "BIOS_C_States_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r"Enable \"*CPU C-states\"*", case=False), "BIOS_C_States_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*(C.State)[^,.<;]*disabled", case=False), "BIOS_C_States_Enabled"] = False
    df["BIOS_C_States_Enabled"].count()


    df["BIOS_P_States_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*(P.State)[^,.<;]*(P2|P3)", case=False), "BIOS_P_States_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*(P.State)[^,.<;]*(P2|P3)", case=False), "BIOS_P_States_Enabled"] = True
    # There is no category for "False" since no infos are give like "P-States default". So we resort to None as fallback as we do not know the status
    # Most likey it is on, since this is the default. But also the CPU might not support it ...
    df["BIOS_P_States_Enabled"].count()


    df["BIOS_Prefetchers_Enabled"] = None
    df.loc[df.SUT_Notes.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*enable", case=False), "BIOS_Prefetchers_Enabled"] = True
    df.loc[df.SUT_Notes.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*disable", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disable L1 Cache Stream Prefetchers", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disable L2 Cache Stream Prefetchers", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disable Processor Data Prefetch", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disabled Adjacent Cache Line Prefetch in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disabled DCU Streamer Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disabled Hardware Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disable \"Processor Data Prefetch\"", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_Notes.str.match(r".*Disabled DCU Streamer Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False

    df.loc[df.SUT_BIOS.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*enable", case=False), "BIOS_Prefetchers_Enabled"] = True
    df.loc[df.SUT_BIOS.str.match(r".*prefetch(er)?s?( was)?( set to)?[\"'=\s:-]*disable", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disable L1 Cache Stream Prefetchers", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disable L2 Cache Stream Prefetchers", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disable Processor Data Prefetch", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disabled Adjacent Cache Line Prefetch in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disabled DCU Streamer Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disabled Hardware Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disable \"Processor Data Prefetch\"", case=False), "BIOS_Prefetchers_Enabled"] = False
    df.loc[df.SUT_BIOS.str.match(r".*Disabled DCU Streamer Prefetcher in BIOS.", case=False), "BIOS_Prefetchers_Enabled"] = False
    df["BIOS_Prefetchers_Enabled"].count()

    return df

def main():
    pd.set_option("display.max_rows", 100)
    pd.set_option("display.max_columns", 20)
    pd.set_option('display.max_colwidth', None)

    df = pd.read_csv("./../data/spec_data.csv", sep="|", index_col=False, na_values=["None"])

    # Hashing cause we want to identify columns later on based on initial uniqueness
    df['hash'] = pd.util.hash_pandas_object(df)
    #assert(df.hash.nunique() == df.shape[0]) # no duplicate hashes

    ## Cleaning

    helper.visual_check(df.dtypes.to_dict(), "Are all data types ok?")

    df = remove_unneeded_columns(df)

    df = split_hardware_availabilty(df)
    assert df.Hardware_Availability_Year.min() >= 2018, "Results older than 2018 should have been cut off in create_data_csv.py"

    df = create_cpu_make(df)

    df = create_cpu_name(df)

    df = create_turbo_boost(df)

    df = make_cpu_cores(df)
    df = make_cpu_chips(df)

    df = make_hardware_threads(df)

    df = split_psu(df)

    df = make_cpu_family(df)

    df = make_l2_cache(df)

    df = make_l3_cache(df)

    df = make_tdp_old(df)
    df = add_tdp_from_lookup(df)
    report_missing_tdp(df)

    # Deactivated for now. The TDP comes from the spec sheets and cpu_tdp_lookup.csv
    # df = make_tdp_wikipedia(df)

    df = make_bios_features(df)

    df["AvgPower"] = df.loc[:,['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
           '60_AvgPower', '50_AvgPower', '40_AvgPower', '30_AvgPower',
           '20_AvgPower', '10_AvgPower', 'ActiveIdle']].mean(axis=1)

    df.to_csv("./../data/spec_data_cleaned_unmelted.csv")


    df = df.drop("AvgPower", axis=1)

    df = melt_power_and_load(df) # spread columns to rows
    df = clean_power_and_load(df) # move 100_AvgPower => 100 as int

    df.to_csv("./../data/spec_data_cleaned.csv")


    r'''
    ## Now do the same, but with HW_CPUChars column
    x = df.loc[df['HW_CPUChars'].str.match(r".*\(.*Boost.*\)"), 'HW_CPUChars']
    y = df.loc[df['HW_CPUChars'].str.match(r".*\(.*up to (.*)GHz.*"), 'HW_CPUChars']
    ## What's different?
    pd.concat([x,y]).drop_duplicates(keep=False)
    #A: (Max Boost Clock up to 3.5 GHz)
    #df.iloc[445]
    # I googled that CPU, its the same thing as Turbo Boost


    ### Merge (actually fillna()) the two TurboBoostGHz columns
    turbo_from_chars = df['HW_CPUChars'].str.extract(r'.*\(.*up to (?P<TurboBoostGHz>.*)GHz.*')
    turbo_from_chars.count()      # 91
    df['TurboBoostGHz'].count()   # 41
    df['TurboBoostGHz'] = df['TurboBoostGHz'].fillna(turbo_from_chars['TurboBoostGHz'])
    df['TurboBoostGHz'].count()  # 132, looks good considering duplicates

    # Strip TurboBoost from CPU Chars
    df['HW_CPUChars'] = df['HW_CPUChars'].str.replace(r"\(.*up to (.*)GHz.*\)", "", regex=True)

    ## Make sure type is correct
    df["TurboBoostGHz"] = df["TurboBoostGHz"].astype(float)
    df.dtypes.to_dict()

    # HW_CPUName
    # @ X.X GHz -> this should be able to be safely removed, as the info already
    # exists in the HW_CPUFreq column

    df.loc[df['HW_CPUName'].str.match(r".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName']
    df.loc[df['HW_CPUName'].str.match(r".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName'].count()
    df.loc[df['HW_CPUName'].str.match(r".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName'].unique()


    ## Compare the freq extract vs the freq in column, make sure they're ==
    freq_from_name = df.HW_CPUName.str.extract(r".*(\d+\.\d*)\s*GHz.*", expand = False, flags=re.IGNORECASE).dropna()
    freq_from_column = df.loc[freq_from_name.index]
    freq_from_name = freq_from_name.astype('float') * 1000
    freq_from_column.HW_CPUFreq = freq_from_column.HW_CPUFreq.astype('float')
    ### What's a simple way to see everywhere this fails?
    #x = freq_from_column.loc[~freq_from_name.eq(freq_from_column.HW_CPUFreq)]
    #df.loc[x.index, x.hash] == df.hash
    #assert(freq_from_name.eq(freq_from_column.HW_CPUFreq).all()

    #z = freq_from_name.eq(freq_from_column) ### Line 484 is false
    # 484 in freq_from_name is 2933
    # 484 in freq_from_column is 2930
    # oh its a rounding error. hmm. what do here. could just drop. not best long
    # thinking though.
    # TODO: for now this is fine, it means we can safely remove these values,
    # but I want to turn this assert back on
    # clean line 484 manually, then use the assert :-)
    # hash the row



    # TODO: HW_Vendor
    # just basic cleaning, standardize how companies are written
    # etc.
    vendors = df.loc[df['HW_Vendor'].str.contains('Hewlett'), 'HW_Vendor'].unique()
    #df.HW_Vendor = df.HW_Vendor.str.replace('HEPYCEPYCewlett\s?-?\s?Packard\s?(Enterprise|Company)', '', regex=True, case=False)
    '''






    # test code
    # a_archs_t = pd.DataFrame({'XeonPeon':['CoolProcessorWon 1234', 'CoolProcessorToo 4321', None, None],'OptimusPrime':[None, None, 'CoolProcessorTree', 'CoolProcessorFore'],})
    # a_df_t = pd.DataFrame({'CPU': ['CoolProcessorWon 1234', 'Totally Not In DataSet','CoolProcessorWon', 'CoolProcessorFore', 'CoolProcessor']})
    # a_t = a_df_t.CPU.isin(a_archs_t.XeonPeon)

    ## Disk Drive, size + type (SSD or HDD)






if __name__ == "__main__":
    main()
