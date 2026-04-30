# IDT Normalase

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* IDT Normalase

## Description
This is the Normalase protocol that follows the Normalase PCR that is done after the usual fragmentation, End-Repair, A-tailing, and Ligation. The Ligation would have been performed with either a full length adapter ligation using the Normalase Reagent R5, or a stubby universal adapter followed by the barcoded stubby Normalase adapters in the PCR. This protocol follows that modified PCR that can be adapted into other NGS Library preps, before starting the prepared, amplified libraries should be cleaned and quantified, samples must be at least 5ul of 12nM for efficient Normalization. See the IDT Normalase protocol for more information.

# EXAMPLE PROTOCOL SETUP
This is an example setup for 24 samples that will be pooled into 3 pools of 8 samples each. The first step is a reaction on the thermocycler, afterwards the plate is transferred to Pos 1 and a new plate for pooled samples and additional reactions goes on the thermocycler. This protocol will pool 5ul of each sample individually with a single channel pipette according to
the setup below. The sample setup is configured for 1, 2, or 3 columns of samples into 3 pools, but the configuration can be adjusted for different pooling amounts or number of pools.

* ![example-protocol-setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-idt-normalase/example+protocol+setup.png)

* [c setup](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-idt-normalase/example+protocol+csv.png)


Explanation of complex parameters below:
* `.CSV File`: Provide csv formatted as seen in documentation to specify how many samples per pool is desired. 
* `Number of Samples`: Specify number of samples for this run.
* `Dry Run`: Yes will return tips, skip incubation times, shorten mix, for testing purposes.
* `Use Modules?`: Yes will not require modules on the deck and will skip module steps, for testing purposes, if `Dry Run` is set to `Yes`, then this variable will automatically set itself to `No`.
* `Use protocol specific z-offsets?`: Sets whether to use protocol specific z offsets for each tip and labware or no offsets aside from defaults
* `Use NGS Magnetic Block?"`: Sets whether there is the Magnetic Block on the Deck (for post-NGS Setup)
* `P20 Single-Channel Mount`: Specify which mount (left or right) to mount the P20 single-channel pipette.
* `P20 Multi-Channel Mount`: Specify which mount (left or right) to mount the P20 multi-channel pipette.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Thermocycler Module](https://shop.opentrons.com/collections/hardware-modules/products/thermocycler-module)

### Labware
* 2x Eppendorf 96 well plate full skirt
* 1x Nest 96 well plate full skirt
![labware](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-idt-normalase/labware+table.png)

### Pipettes
* [P20 Single-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-idt-normalase/deck+setup.png)

* Left: Initial Plate Setup, Right: After Moving the Sample plate to Pos 1 and Pooling the samples on a new plate on the
Thermo.

# PLATE MOVING
The script requires manually transferring the sample plate between the Thermocycler and Magnet. NOTE: In the script
the two positions are handled as sample_plate_mag and sample_plate_thermo; during calibration use an empty plate of
the same labware as the sample plate on the magnet position to calibrate that position.

# REAGENT PLATE
Prepare the reagents in the Reagent Plate according to the table below. If available, prepare extra volume to account for
overage. Following the instructions from the IDT Normalase protocols, reagent mixes for Norm II and Inactivation are
made for at least 24x samples even if fewer samples are run due to the low volumes.

* [reagent plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/sci-idt-normalase/reagent+plate+setup.png)


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
sci-idt-normalase
