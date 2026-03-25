# Normalization and Barcode Addition


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling


## Description
* This protocol normalized a 96 well plate with samples and water, then moves them to a barcode plate along with two buffers for further processing. A csv is uploaded to the protocol in which the destination well in the final plate should be column 1 (source well and destination well are the same, so should be 1:1), the water transfer volume should be in column 5, and the dna transfer volume should be in column 4. Note: if "top half of plate" or "bottom half of plate" is selcted, then the multi-channel pipette will pick up four tips and will always aspirate from the top 4 rows of the final plate on slot 3 to dispense into the barcode plate, either in the top or bottom half (always from top half to either top or bottom half). The csv will run for as many rows as there are, and there should only be one row at the top for the header.

* For water addition to the plate, if the tranfser volume is greater or equal to 5ul, it will transfer 5ul.

* For DNA addition to plate, the pipette will transfer 6ul if the transfer volume is greater than 6ul. It will also transfer 1 if the transfer volume is less than 1ul.

* A slow aspiration rate and delay is employed for Buffer B, since it is a viscous liquid. 


### Labware
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* [Bio-Rad 96 Well Plate 200 µL PCR #hsp9601](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* Opentrons 96 Filter Tip Rack 20 µL


### Pipettes
* [Opentrons P20 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P20 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/onsite_galatea/magbind/norm.png)




### Protocol Steps
1. Water added to final plate on 3 depending on csv
2. DNA added to final plate on 3 depending on csv
3. Sample added to barcode plate (top, bottom, or full)
4. Buffer A added to barcode plate
5. Buffer B added to barcode plate
6. Samples from column 2-6 pooled into column 1, samples from column 7-11 pooled in column 12


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
onsite_galatea_normalization
