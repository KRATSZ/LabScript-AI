# NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* NEBNext Ultra II

## Description
This protocol automates the [NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®](https://www.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information) on the OT-2.

This protocol was developed internally by Opentrons for use on the OT-2 and provides several options. Users can select how many samples to prepare, whether or not to use on-deck modules (like our thermocycler), and whether or not to perform certain steps in the process. Additionally, users can select to enable a "Test Mode" that is great for performing a dry run of the protocol.

For a more detailed explanation of this protocol, including deck setup and reagent setup, please see this guide: [link to guide](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-neb-next-ultra/NEBNext+Ultra+II+-+Protocol+Library+Readme.pdf)

Explanation of complex parameters below:
* **Number of Samples**: Select the number of samples to prepare
* **Test Mode (dry run)**: Select whether to perform a dry run (Yes) instead of a sample run
* **Use Modules**: Select whether or not you are using our Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) and [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* **Reuse Tips**: Select whether or not to reuse tips for certain steps (selecting yes will reuse tips in a sterile way, saving on the amount of tips used and eliminating the need to replace tips during the run)
* **Use Thermocycler**: Select whether or not you will use our on-deck GEN1 thermocycler module. If not using (select "No"), the user will be prompted to move the sample plate to an off-deck thermocycler.
* **Use Opentrons Offsets**: Select whether to use Z offsets used by the Opentrons Science Team ("Yes") or use the default Z heights of the labware ("No")
* **Perform ERAT Step**: Select whether or not to perform the ERAT step.
* **Perform Ligation Step**: Select whether or not to perform the Ligation step.
* **Perform Post-Ligation Step**: Select whether or not to perform the Post-Ligtion step.
* **Perform PCR Step**: Select whether or not to perform the PCR step.
* **Perform Post-PCR Step**: Select whether or not to perform the Post-PCR step.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* Thermocycler Module (GEN1). Note: this protocol has only been verified with our GEN1 Thermocycler.


### Labware
* [NEST 96-Well PCR Plates](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/) or [NEST 96-Well Deepwell Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/) (for more information, please see [this guide](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-neb-next-ultra/NEBNext+Ultra+II+-+Protocol+Library+Readme.pdf))
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Pipettes
[P300 8-Channel Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/) (**Left mount**)</br>
[P20 8-Channel Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/) (**Right mount**)


### Reagents
[NEBNext® Ultra™ II DNA Library Prep Kit for Illumina®](https://www.neb.com/products/e7645-nebnext-ultra-ii-dna-library-prep-kit-for-illumina#Product%20Information)


---

### Deck Setup
Please see our guide for a detailed explanation of deck setup. [Link to guide](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-neb-next-ultra/NEBNext+Ultra+II+-+Protocol+Library+Readme.pdf)

### Reagent Setup
Please see our guide for a detailed explanation of reagent setup. [Link to guide](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-neb-next-ultra/NEBNext+Ultra+II+-+Protocol+Library+Readme.pdf)

---

### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
sci-neb-next-ultra
