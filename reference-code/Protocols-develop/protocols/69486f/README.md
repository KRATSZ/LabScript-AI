# NGS Library Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* KAPA HiFi

## Description

This custom protocol performs part 2 of the [KAPA HiFi NGS Library Prep kit](https://sequencing.roche.com/en/products-solutions/products/sample-preparation/library-amplification/kapa-hifi-kits.html). The protocol can accommodate up to 8 samples. The operator is prompted to perform PCR and normalization off-deck.

The number of samples and subsamples should be specified in a .csv file formatted as follows:

```
sample index,# subsamples
1,1
2,2
```

You can also access a template file [here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69486f/ex.csv).

---

### Labware
* [Agilent AriaMx 96 Well PCR Plates 200ul #401490](https://www.agilent.com/store/en_US/Prod-401490/401490)
* [Opentrons 24 Tube Rack](https://shop.opentrons.com/4-in-1-tube-rack-set/) with [Eppendorf 1.5 mL Safe-Lock Snapcap Tubes](https://online-shop.eppendorf.us/US-en/Laboratory-Consumables-44512/Tubes-44515/Eppendorf-Safe-Lock-Tubes-PF-8863.html)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)

### Pipettes
* [Opentrons P20 Single- or 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 Single- or 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
* [KAPA HiFi NGS Library Prep kit](https://sequencing.roche.com/en/products-solutions/products/sample-preparation/library-amplification/kapa-hifi-kits.html)

---

### Deck Setup

Note that these deck states depict a combination of the maximum number of PCR 1 forward primers.

Starting state (showing normalization for <= 28 sample + subsample product):  
![deck1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69486f/deck1-5.png)  
* green on slot 1: starting samples according to above example .csv
* clear on slot 7 (tubes A1-D2): empty tubes for PCR 1 mix creation
* orange on slot 7 (A3-D4): unique PCR 1 forward primers (in column order)
* clear on slot 7 (tubes A5-D6): empty tubes for PCR 2 mix creation
* blue on slot 8 (A1): water
* pink on slot 8 (B1): PCR mastermix
* purple on slot 8 (C1): PCR 1 reverse primer
* purple on slot 8 (D1): PCR 2 reverse primer
* dark blue on slot 8 (A2-D3): tubes for normalized pools
* orange on slot 8 (A4-D5): unique PCR 1 forward primers (in column order)
* light blue on slot 8 (A6): normalization binding buffer
* light purple on slot 8 (B6-C6): normalization wash buffer
* green on slot 8 (D6): normalization elution buffer

Starting state (showing normalization for <= 28 sample + subsample product):  
![deck2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/69486f/deck2-4.png)
* green on slot 1: starting samples according to above example .csv
* clear on slot 7 (tubes A1-D2): empty tubes for PCR 1 mix creation
* orange on slot 7 (A3-D4): unique PCR 1 forward primers (in column order)
* clear on slot 7 (tubes A5-D6): empty tubes for PCR 2 mix creation
* blue on slot 8 (A1): water
* pink on slot 8 (B1): PCR mastermix
* purple on slot 8 (C1): PCR 1 reverse primer
* purple on slot 8 (D1): PCR 2 reverse primer
* dark blue on slot 8 (A2-D3): tubes for normalized pools
* orange on slot 8 (A4-D5): unique PCR 1 forward primers (in column order)
* light blue on slot 11 (A1): normalization binding buffer
* light purple on slot 11 (A2): normalization wash buffer
* green on slot 11 (A3): normalization elution buffer

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
69486f
