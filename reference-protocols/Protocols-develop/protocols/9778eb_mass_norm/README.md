# Normalization with CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol uses values in a CSV to normalize samples in a 96 well plate. The CSV requires starting and finishing concentrations broken up into mass/moles and volumes. This allows for minimal user calculations before loading samples. Additionally, units can be different from run to run and even sample to sample provided the starting and finishing units are the same. E.g. sample A1 is nanograms/uL and will be diluted to a set concentration in well A1 in the normalized plate while sample B1 is moles/uL and will be diluted to a set molarity in well B1.

This protocol also checks if normalization is possible with the given concentrations and will list the failed wells at the end of the protocol run. E.g. C1 starting concentration is 15 ng/uL and the stated final concentration target is 20 ng/uL so C1 will be added to the 'failed well' list at the protocol end.

Explanation of complex parameters below:
* `Volume of Water in Falcon Tube`: Starting volume of nuclease free water in the on-deck tube rack. This is in mL and will be used to track liquid height
* `Source Plate Type`: 96 well plate samples will start the protocol in
* `Destination Plate Type`: 96 well plate samples will end the protocol in
* `P20 Single GEN2 Mount`: Defines which side the P20 single pipette will be mounted on. The P300 single pipette will be mounted on the opposite side
* `Transfer .csv File`: Here, you should upload a .csv file formatted [like the example CSV located here](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/csv/example_norm.csv)
---

### Labware
* [Opentrons 6 Tube Rack with Falcon 50 mL Conical](https://shop.opentrons.com/4-in-1-tube-rack-set/)
* [NEST 96 Deepwell Plate 2mL](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [NEST 100uL 96 Well Plate](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/)
* [Thermofisher Semi-Skirted on Adapter 96 Well Plate](https://www.thermofisher.com/order/catalog/product/AB1400L)

### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

### Reagents
* Nuclease Free Water (for diluent)

---

### Deck Setup
* Reagent Color Code
![color code](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/csv/color_code.png)

* Starting deck layout with reagents
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/9778eb/csv/deck_layout.png)

### Reagent Setup
* Slot 1, sample plate
* Slot 2, normalized plate
* Slot 3, 96 Filter Tip Rack 20 uL
* Slot 4, tube A1, Nuclease free water
* Slot 5, 96 Filter Tip Rack 200 uL
* Slot 6, 96 Filter Tip Rack 20 uL
* Slot 7, 96 Filter Tip Rack 200 uL

---

### Protocol Steps
1. Both pipettes pick up tips in preparation for diluent addition
2. A calculated amount of nuclease free water is added to each specified well in slot 2 from tube A1 in slot 4, using the same tip for each addition and swapping pipettes based on transfer volume
3. A calculated amount of each sample in slot 1 is added to the same well in slot 2 and mixed. A new tip is used for each sample and the pipette used is based on the transfer volume for efficient transfers
4. A list of non-normalizable wells is listed at the end of the protocol run

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
9778eb_mass_norm
