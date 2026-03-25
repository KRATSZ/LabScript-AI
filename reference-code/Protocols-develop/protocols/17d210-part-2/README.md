# Verogen ForenSeq DNA Signature Prep Kit Part 2/5: Indexing

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

This custom indexing protocol is part 2/5 of the [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE). In this protocol, indexes are transferred to their corresponding wells in a PCR plate containing samples. Then, PCR2 buffer is added to each sample and mixed using fresh tips for each transfer.

---

### Labware
* Abgene Midi 96 Well Plate 800 µL
* Amplifyt 96 Well Plate 200 µL
* [Opentrons 20µl and 300µl Tipracks](https://shop.opentrons.com/collections/opentrons-tips)

### Pipettes
* [P20 Multi GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Multi GEN2 Pipette](https://opentrons.com/pipettes/)

### Reagents
* [Verogen ForenSeq DNA Signature Prep kit](https://verogen.com/products/forenseq-dna-signature-prep-kit/?utm_term=&utm_campaign=Product+Campaigns&utm_source=adwords&utm_medium=ppc&hsa_acc=2964416997&hsa_cam=12070402317&hsa_grp=115534580817&hsa_ad=544522374879&hsa_src=g&hsa_tgt=dsa-19959388920&hsa_kw=&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gclid=CjwKCAjw4qCKBhAVEiwAkTYsPP4JakJA06WcfvubM80x5gzv7kIFucad6jw9WrACitcG6qERBSAU1xoCaOEQAvD_BwE)

---

### Deck Setup
* blue: PCR2 buffer  
* pink: samples  
* green: indexes  
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/17d210/deck2-2.png)

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
17d210
