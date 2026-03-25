# CleanPlex NGS library preparation

## Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS
	* Paragon Genomics CleanPlex NGS Panel Kit

## Description
This protocol performs the [CleanPlex® NGS Panel](https://www.paragongenomics.com/wp-content/uploads/2021/01/UG1001-08-CleanPlex-NGS-Panel-User-Guide-v2.pdf) for up to 96 samples.

The protocol is broken down into 6 main parts:
* `1A`: Multiplex PCR (mPCR) reaction
* `1B`: Post-mPCR Purification
* `2A`: Digestion Reaction
* `2B`: Post-Digestion Purification
* `3A`: Second PCR Reaction
* `3B`: Post-Second PCR Purification

Explanation of complex parameters below:
* Test parameters
    * `DRYRUN`: The default setting is `False` . If set to `True`, the protocol will be in dry run testing mode. The pipette will return the tip to the tiprack after each liquid transfer.
	* `TEST_MODE_BEADS`: The default setting is `False` . If set to `True`, the protocol will be in beads testing mode. The beads incubation and magnet engaging time will be in unit of seconds rather than minutes. Meanwhile, the pipette will return the tip to the tiprack after each liquid transfer.
* Timer parameters
    * `timer_h`: Set up the time for hours
	* `timer_m`: Set up the time for minutes
* Flow rate parameters
    * `water_rate`: Set up the flow rate of transferring water liquids, unit: folds of the default speed, 1.2 means 120 % of the default speed while 0.6 indicates 60% of the default speed
	* `buffer_mmx_primer_rate`: Set up the flow rate of transferring buffer/mastermix/primer liquids, unit: the same as above
    * `sample_rate`: Set up the flow rate of transferring sample-related liquids, unit: folds of the default speed
	* `beads_rate`: Set up the flow rate of transferring bead liquids, unit: the same as above
	* `ethanol`: Set up the flow rate of transferring ethanol liquids, unit: the same as above
* beads mixing parameters
    * `beads_mix_reps`: The frequencies that robot will mix the beads
	* `beads_mix_rate`: The flow rate that the robot will mix the beads, the same as `Flow rate parameters`
* Magnetic Module parameters
    * `magdeck_engage_height`: The height of magnet that will engage, in `mm`
	* `ethnaol_dis_zoffset`: The height of dispensing ethanol from the top of the well during ethanol washing, in `mm`
	* `incubation_time`: The time it takes for DNA binding before engaging the magnet, unit in `minutes` when `TEST_MODE_BEADS` is `False`
    * `beads_engaging_time`: The time it takes for beads binding after engaging the magnet, unit in `minutes` when `TEST_MODE_BEADS` is `False`
	* `airdry_time`: The time it takes for airdrying after removing the enthanol, unit in `minutes` when `TEST_MODE_BEADS` is `False`
	* `ethanol_wash_time`: The time it takes for ethanol washing after adding it in the well, unit in `minutes` when `TEST_MODE_BEADS` is `False`

---

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/.hardware-modules/products/magdeck)

### Labware
* [Bio-Rad 96 Well Plate 200 uL PCR](https://labware.opentrons.com/biorad_96_wellplate_200ul_pcr?category=wellPlate)
* [NEST 96 Deepwell Plate 2mL](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 12-Well Reservoir, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)

### Pipettes
* [Opentrons P20 GEN2 multi-channel electronic pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P300 GEN2 multi-channel electronic pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
* `Slot 1`: Magnetic Module + Bio-Rad 96 Well Plate 200 uL PCR (mag_plate)
* `Slot 2`: Bio-Rad 96 Well Plate 200 uL PCR (sample_plate) for calibration purposes. This labwared will be transferred among Slot 2, Slot 1, and external thermocycler after.
* `Slot 3`: Temperature Module + Bio-Rad 96 Well Plate 200 uL PCR (reagent_plate)
* `Slots 4/7/6`: Opentrons 96 Filter Tip Rack 200 uL
* `Slots 9/8/5`: Opentrons 96 Filter Tip Rack 20 uL
* `Slot 10`: NEST 12-Well Reservoir, 15 mL (reagent_reservoir)
* `Slot 11`: NEST 12-Well Reservoir, 15 mL (waste_reservoir)

![Deck Setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0eaeb5/456.PNG)

### Reagent Setup
![Reagent Summary](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0eaeb5/1.PNG)

* reagent_plate, slot 3, filled at the beginning or during certain transition step
   ```
    mPCR_mix_5x:      Column1, A1
    mPCR_primers:     Column2, A2
    stop:             Column3, A3
    digest_mmx:       Column4, A4
    second_PCR_mmx:   Column5, A5
    index_primers:    Column6, A6
   ```
![Reagent Plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0eaeb5/2.PNG)   

* reagent_reservoir, slot 10, filled at the beginning or during certain transition step
   ```
    water:           Column1, A1
    TE:              Column2, A2
    beads:           Column3, A3
    ethanol:         Column4, A4
   ```
![Reagent Reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0eaeb5/3.PNG)   

* waste_reservoir, slot 11, empty
   ```
   All 12 columns will collect the waste one by one
   ```
---

### Process
1. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
2. Set up your deck and liquids according to the deck and reagent map.
3. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
4. Hit 'Run'.

### Additional Notes
1. A customized function, `pause_attention`, will pause the protocol, flash the light, and show reminder messages
   * at the very beginning of the protocol running---->remind the user to set up the correct timer for all steps
   * at the transition steps ----> remind the user to trasnfer the sample plate to external instrumentation for the next step and refill the empty tipracks (both types)
   * when either 20 ul or 200 ul filter tips are ran out ----> remind the user to refill empty tipracks (both types)
2. Reagents could be filled at the beginning or during certain transition step
3. Tip changing pattern will be summarized in a separate Excel file for the users to review
4. If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
0eaeb5
