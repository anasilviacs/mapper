import xmltodict

# parse mzid file: xmltodict imports it as a dictionary
with open('data/velos_pyr_entrapment_decoys.mzid') as fd:
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
        
