import argparse
import xmltodict
import pandas as pd

# Arguments: percolator features, .MzIdentML
parser = argparse.ArgumentParser(description="Take pin file built with Percolator's msgf2pin and add the 'TITLE' from the mgf file")
parser.add_argument('-m', dest='mzml', help='Path to mzml file')
parser.add_argument('-p', dest='pin', help='Path to pin file')

args = parser.parse_args()

# parse mzid file: xmltodict imports it as a dictionary
with open(args.mzml) as fd:
     doc = xmltodict.parse(fd.read())

mapper = {}

# going through each SpectrumIdentificationResult. There may be more than one hit. "mapper" will correspond each perc_id with the mgf file "TITLE" for the spectrum
for i in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'])):
    if type(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem']) is list:
        for j in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem'])):
            spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
            hit = spectrum['SpectrumIdentificationItem'][j]
            perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
            title = spectrum['cvParam']['@value']
            mapper[perc_id] = title
    else:
        spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
        hit = spectrum['SpectrumIdentificationItem']
        perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
        title = spectrum['cvParam']['@value']
        mapper[perc_id] = title

# open percolator features; add column with mgf title
# perc[perc['SpecId'].str.contains("perc_id")]
def lazy_pin_parser(path):
    """
    To parse the pin file. In some rows, the "Proteins" column contains
    tab-separated values. For this normal parsers don't work too well. This is a
     lazily built parser that addresses this
    """
    f = open(path)
    rows = f.readlines()
    for i, row in enumerate(rows):
        if i == 0: data = pd.DataFrame(columns=row.split('\t')); n_rows = len(row.split('\t'))
        if i == 1: continue # row 1 is initial direction
        else:
            r = row.split('\t')
            tmp = []
            for j in range(n_rows-1):
                tmp.append(r[j])
            tmp.append('|'.join(r[n_rows-1:]).rstrip('\n'))
            data.loc[i-1] = tmp
    return data
