# Verogen ForenSeq DNA Signature Prep Kit Part 1/5: PCR1 Setup

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Verogen ForenSeq DNA Signature Prep Kit

## Description

Links:  
* [Part 1](./17d210)
<br><br />
* [Part 2](./17d210-part-2)
<br><br />
* [Part 3](./17d210-part-3)
<br><br />
* [Part 4](./17d210-part-4)
<br><br />
* [Part 5](./17d210-part-5)

This custom PCR1 Setup protocol is part 1/5 of the [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE). In this protocol, mastermix is pre-added to a clean PCR plate. Then, samples from up to 4 source plates specified in the `.csv` file are transferred to the plate containing mastermix and mixed (optionally).

The .csv file should be formatted as shown below (**including header line**):
```
volume,source plate # (1-4),source column (1-12),destination column(1-12)
8,1,2,1
8,2,3,2
8,2,12,3
```

---

### Labware
* Amplifyt 96 Well Plate 200 µL
* [Opentrons 20µl Tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 96 Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with Generic PCR Strip 200 µL

### Pipettes
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)

### Reagents
* [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/17d210/deck1-2.png)

---

### Protocol Steps
1. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot is also specified, as well as aspiration height from the bottom of the well.
2. Pipette will dispense this volume into user-specified labware and well according to the imported csv file. Slot is also specified.
3. Steps 1 and 2 repeated over the duration of the CSV.

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
17d210
