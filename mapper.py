import argparse
import xmltodict
import pandas as pd
import sys

def get_indices(doc):
    """
    Given a dictionary with the .mzid file, go through every
    SpectrumIdentificationResult and match the mgf TITLE to the initial part of
    the Percolator index. Save these correspondences in a dictionary
    """
    index_map = {}
    for i in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'])):
        if type(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem']) is list:
            for j in range(len(doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]['SpectrumIdentificationItem'])):
                spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
                hit = spectrum['SpectrumIdentificationItem'][j]
                # perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
                perc_id = hit['@id']
                title = spectrum['cvParam']['@value']
                index_map[perc_id] = title
        else:
            spectrum = doc['MzIdentML']['DataCollection']['AnalysisData']['SpectrumIdentificationList']['SpectrumIdentificationResult'][i]
            hit = spectrum['SpectrumIdentificationItem']
            # perc_id = hit['@id'] + '_' + hit['@chargeState'] + '_' + hit['@rank']
            perc_id = hit['@id']
            title = spectrum['cvParam']['@value']
            index_map[perc_id] = title

    return index_map

def fix_pin_tabs(path):
    """
    Takes a pin file and re-writes it, replacing the tabs that separate the
    Proteins column with pipes
    """
    f = open(path)
    rows = f.readlines()
    outfile = path.rstrip('.pin') + '_fixed.pin'
    out = open(outfile, 'w+')

    for i, row in enumerate(rows):
        if i == 0:
            numcol = len(row.split('\t'))
        elif i < 2:
            out.write(row)
        else:
            r = row.split('\t')
            tmp = []
            for j in range(numcol):
                tmp.append(r[j])
            tmp.append(';'.join(r[numcol:]))
            out.write('\t'.join(tmp))
    return None

def map_mgf_title(pin, mzid, decoy_mzid=None):
    """
    Add the TITLE column to the pin file. Processes the MzIdentML file (one if
    the search was concatenated, two if the target and decoy searches were ran
    separately).
    """
    pin['TITLE'] = [None] * len(pin)
    # parse mzid file: xmltodict imports it as a dictionary
    # concatenated searches yield one mzid
    if not decoy_mzid:
        with open(mzid) as fd:
             doc = xmltodict.parse(fd.read())

        # Use get_indices() to get a dictionary that corresponds each percolator
        #  SpecId to its mgf TITLE
        title_map = get_indices(doc)
        # Adding mgf "TITLE" column.
        for i in range(len(pin)): # because index starts at 1
            k = '_'.join(pin.loc[i, 'SpecId'].split('_')[-6:-3])
            if k in title_map.keys():
                pin.loc[i, 'TITLE'] = title_map[k]
            else:
                continue

    # for separate target-decoy there are two mzid
    else:
        with open(mzid) as fd:
             doc = xmltodict.parse(fd.read())
        title_map_targets = get_indices(doc)

        with open(decoy_mzid) as fd:
             doc = xmltodict.parse(fd.read())
        title_map_decoys = get_indices(doc)

        for i in range(len(pin)):
            k = '_'.join(pin.loc[i, 'SpecId'].split('_')[-6:-3])
            if pin.loc[i, 'Label'] == "-1":
                if k in title_map_decoys.keys():
                    pin.loc[i, 'TITLE'] = title_map_decoys[k]
                else:
                    sys.stdout.write('oops\n')
                    continue
            elif pin.loc[i, 'Label'] == "1":
                if k in title_map_targets.keys():
                    pin.loc[i, 'TITLE'] = title_map_targets[k]
                else:
                    sys.stdout.write('oops\n')
                    continue
    return pin

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take pin file built with Percolator's msgf2pin and add the 'TITLE' from the mgf file")
    parser.add_argument('-m', dest='mzid', help='Path to single mzid file (concatenated search)')
    parser.add_argument('-t', dest='targets', help='Path to target search mzid file')
    parser.add_argument('-d', dest='decoys', help='Path to decoy search mzid file')
    parser.add_argument('-p', dest='pin', help='Path to pin file')

    args = parser.parse_args()

    # open percolator features; add column with mgf title
    sys.stdout.write('Fixing tabs on pin file... ')
    sys.stdout.flush()
    fix_pin_tabs(args.pin)
    sys.stdout.write('Done! \n')
    sys.stdout.flush()

    sys.stdout.write('Parsing pin file... ')
    sys.stdout.flush()
    pin = pd.read_csv(args.pin.rstrip('.pin') + '_fixed.pin', header=0, skiprows=[1], sep='\t')
    sys.stdout.write('Done! \n')
    sys.stdout.flush()

    sys.stdout.write('Mapping spectrum TITLE on to pin file... \n')
    sys.stdout.flush()
    if args.decoys:
        pin = map_mgf_title(pin, args.targets, args.decoys)
    else:
        pin = map_mgf_title(pin, args.mzid)
    sys.stdout.write('Done! \n')
    sys.stdout.flush()

    sys.stdout.write('Saving pin file... ')
    sys.stdout.flush()
    pin.to_csv(args.pin, sep='\t', index=False)
    sys.stdout.write('Done! \n')
    sys.stdout.flush()
