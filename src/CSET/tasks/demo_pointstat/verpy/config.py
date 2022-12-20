"""
Set up choices of CSET verification configuration, e.g. thresholds etc. Should
be aligned with operational verification and configuration from METplus apps
"""

# Settings below here are relevant for the verification part of CSET

# VerPy default settings, first Scale Series plots. Defaults chosen are suitable
# for use over the UK. SS prefix => scale statistics options (fractional
# statistics, e.g. Fractions Skill Score). For fractional statistics, set the
# thresholds and neighbourhood scale sizes required.
SS_SCALES = [1, 5, 25, 51, 101]
SS_THRESH = [0.5, 1.0, 4.0, 8.0, 16.0, 32.0, 64.0]
SS_FREQS = ["20%", "10%", "5%"]

# GS prefix => options for general statistics plots ('traditional' verification)
# For categorical parameters, set lists of thresholds.
GS_LINESTYLES = ["-", "--", "-.", ":"]
GS_THRESH_WIND_CON = [-5.0, -2.5, 0, 2.5, 5.0]
GS_THRESH_WIND = ["> 5.0", "> 10.0", "> 13.0", "> 17.5"]
GS_THRESH_CLOUD_FRAC = ["> 0.3125", "> 0.5625", "> 0.8125"]
GS_THRESH_CLOUD_BASE = ["<= 100.0", "<= 300.00", "<= 500.00", "<= 1000.0", "<= 1500.0"]
GS_THRESH_VIS = ["<= 200.0", "<= 1000.0", "<= 4000.0", "<= 5000.0"]
GS_THRESH_PRECIP = [
    "> 0.1999",
    "> 0.4999",
    "> 0.9999",
    "> 3.9999",
    "> 7.9999",
    "> 15.9999",
]

# HIRA prefix => HIgh Resolution Assessment Framework options
HIRA_SCALES = [1, 3, 7, 11]
HIRA_LS = ["-", "--", "-.", ":"]
HIRA_THRESH_WIND = [
    ">= 2.06",
    ">= 3.60",
    ">= 5.65",
    ">= 8.74",
    ">= 11.31",
    ">= 14.39",
    ">= 17.48",
    ">= 21.07",
    ">= 24.67",
    ">= 60.",
]
HIRA_THRESH_CLOUDFRAC = [
    ">=0.0625",
    ">=0.1875",
    ">=0.3125",
    ">=0.4375",
    ">=0.5625",
    ">=0.6875",
    ">=0.8125",
    ">=0.9375",
]
HIRA_THRESH_CLOUDBASE = [
    "<50.0",
    "<100.0",
    "<200.0",
    "<500.0",
    "<1000.0",
    "<1500.0",
    "<2000.0",
    "<2500.0",
    "<5000.0",
]
HIRA_THRESH_VIS = [
    "<50",
    "<100",
    "<200",
    "<500",
    "<1000",
    "<2000",
    "<3000",
    "<4000",
    "<5000",
    "<7500",
]
HIRA_THRESH_PRECIP = [
    ">=0.25",
    ">=0.5",
    ">=1",
    ">=2",
    ">=4",
    ">=8",
    ">=16",
    ">=32",
    ">=64",
]
