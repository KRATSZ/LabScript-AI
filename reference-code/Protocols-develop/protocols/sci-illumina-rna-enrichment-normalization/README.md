# Illumina RNA Prep with Enrichment: Normalization

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Illumina RNA Prep with Enrichment

## Description

This protocol performs normalization for the [Illimuina RNA Prep with Enrichment](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/rna-prep-enrichment.html) protocol. Normalization is the method of adding buffer to a set of samples so that their concentrations are uniform. This is usually so that they can be treated uniformly in subsequent steps. For example, after NGS library prep of multiple samples, the samples are normalized to the same concentration, so that the same volume of each sample can be pooled, and each sample is represented in equal proportions. A requirement for this Normalization protocol is that the concentrations and volumes are known i.e. previously quantified by Picogreen and aliquoted into a plate at a set volume, and formatted
in a .csv file as input.

You should upload a .csv file formatted in the following way, being sure to include the header line:

```
Sample_Plate,Sample_well,InitialVol,InitialConc,TargetConc
sample_plate,A1,20,2.3,2
sample_plate,B1,20,3.99,2
sample_plate,C1,20,4.39,2
sample_plate,D1,20,3.95,2
sample_plate,E1,20,4.16,2
sample_plate,F1,20,3.81,2
sample_plate,G1,20,3.96,2
sample_plate,H1,20,3.41,2
```

---

### Labware
* [NEST 0.1 mL 96-Well PCR Plate, Full Skirt](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [Opentrons 4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/) with 15+50ml Falcon tube insert
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
* [P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* [Illumina RNA Prep with Enrichment](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/rna-prep-enrichment.html)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-illumina-rna-enrichment-normalization/deck.png)

---

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-illumina-rna-enrichment-normalization
