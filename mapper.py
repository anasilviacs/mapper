import argparse
import xmltodict
import pandas as pd
import sys

def get_indices(doc):
    """
    Given a dictionary with the .mzml file, go through every
    SpectrumIdentificationResult and match the mgf TITLE to the initial part of
    the Percolator index. Save these correspondences in a dictionary
    """
    mapper = {}
    for i in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'])):
        if type(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem']) is list:
            for j in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem'])):
                spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
                hit = spectrum['SpectrumIdentificationItem'][j]
                # perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
                perc_id = hit['@id']
                title = spectrum['cvParam']['@value']
                mapper[perc_id] = title
        else:
            spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
            hit = spectrum['SpectrumIdentificationItem']
            # perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
            perc_id = hit['@id']
            title = spectrum['cvParam']['@value']
            mapper[perc_id] = title

    return mapper

def lazy_pin_parser(path):
    """
    To parse the pin file. In some rows, the "Proteins" column contains
    tab-separated values. Because of this normal parsers don't work too well.
    This is a lazily built parser that addresses this.
    """
    f = open(path)
    rows = f.readlines()
    for i, row in enumerate(rows):
        if i == 0:
            data = pd.DataFrame(columns=[r.translate({'"': None}).rstrip('\n') for r in row.split('\t')])
            n_rows = len(row.split('\t'))
        elif i == 1: continue # row 1 is initial direction
        else:
            r = row.split('\t')
            tmp = []
            for j in range(n_rows-1):
                tmp.append(r[j])
            tmp.append('|'.join(r[n_rows-1:]).rstrip('\n'))
            data.loc[i-1] = tmp
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take pin file built with Percolator's msgf2pin and add the 'TITLE' from the mgf file")
    parser.add_argument('-m', dest='mzml', help='Path to single mzml file (concatenated search)')
    parser.add_argument('-t', dest='targets', help='Path to target search mzml file')
    parser.add_argument('-d', dest='decoys', help='Path to decoy search mzml file')
    parser.add_argument('-p', dest='pin', help='Path to pin file')

    args = parser.parse_args()

    # open percolator features; add column with mgf title
    sys.stdout.write('Parsing pin file... ')
    sys.stdout.flush()
    pin = lazy_pin_parser(args.pin)
    pin['TITLE'] = [None] * len(pin)
    sys.stdout.write('Done! \n')
    sys.stdout.flush()
    # parse mzid file: xmltodict imports it as a dictionary
    # concatenated searches yield one mzml
    if args.mzml:
        sys.stdout.write('Concatenated search results; parsing .mzml... ')
        sys.stdout.flush()
        with open(args.mzml) as fd:
             doc = xmltodict.parse(fd.read())

        # Adding mgf "TITLE" column
        mapper = get_indices(doc)
        sys.stdout.write('Done! \n')
        sys.stdout.flush()

        sys.stdout.write('Adding "TITLE" to pin file... ')
        sys.stdout.flush()
        for i in range(1, len(pin)+1): # because index starts at 1
            k = '_'.join(pin.loc[i, 'SpecId'].split('_')[-6:-3])
            if k in mapper.keys():
                pin.loc[i, 'TITLE'] = mapper[k]
            else:
                continue
        sys.stdout.write('Done! \n')
        sys.stdout.flush()

    # for separate target-decoy there are two mzml
    elif args.targets and args.decoys:
        sys.stdout.write('Separate target and decoy search; \n')
        sys.stdout.flush()

        sys.stdout.write('parsing targets .mzml... ')
        sys.stdout.flush()
        with open(args.targets) as fd:
             doc = xmltodict.parse(fd.read())

        mapper_targets = get_indices(doc)
        sys.stdout.write('Done! \n')
        sys.stdout.flush()

        sys.stdout.write('parsing decoys .mzml... ')
        sys.stdout.flush()
        with open(args.decoys) as fd:
             doc = xmltodict.parse(fd.read())

        mapper_decoys = get_indices(doc)
        sys.stdout.write('Done! \n')
        sys.stdout.flush()

        sys.stdout.write('Adding "TITLE" to pin file... ')
        sys.stdout.flush()
        for i in range(1, len(pin)+1): # because index starts at 1
            k = '_'.join(pin.loc[i, 'SpecId'].split('_')[-6:-3])
            if pin.loc[i, 'Label'] == "-1":
                if k in mapper_decoys.keys():
                    pin.loc[i, 'TITLE'] = mapper_decoys[k]
                else:
                    sys.stdout.write('oops\n')
                    sys.stdout.flush()
                    continue
            elif pin.loc[i, 'Label'] == "1":
                if k in mapper_targets.keys():
                    pin.loc[i, 'TITLE'] = mapper_targets[k]
                else:
                    sys.stdout.write('oops\n')
                    sys.stdout.flush()
                    continue

        sys.stdout.write('Done! \n')
        sys.stdout.flush()


    sys.stdout.write('Saving pin file... ')
    sys.stdout.flush()
    pin.to_csv(args.pin, sep='\t', index=False)
    sys.stdout.write('Done! \n')
    sys.stdout.flush()
