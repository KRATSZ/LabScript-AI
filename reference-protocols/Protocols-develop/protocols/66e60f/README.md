# Normalization protocol from CSV

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Normalization

## Description
This protocol performs a custom sample normalization from one or two source plate(s) to one or two final plate(s), diluting with water from a 12 well reservoir on slot 11 based on an input csv file. After normalization the protocol samples 5 µL from each well from the final plate(s) and dispenses it into a DNA pool tube on the tuberack on slot 5 (the tube in position A2). Sample and diluent volumes are specified via the .csv file in the following format, including the header line (empty lines ignored, also note that this is just an example and that any number of lines less than and up to 2x96 may be specified):

```
Plate, Well, SampleID, Concentration, VolumeToDispense
A, A1, Sample1, 3.28, 12.52,
...
A, H12, Sample96, 5.30, 9.70,
B, A1,  Sample97, 6.34, 8.60,
...
B, H12,  Sample192, 7.34, 5.60,
```
The plate is either A (to Final plate slot 6 from DNA plate slot 9) or B (to Final plate slot 4 from DNA plate slot 7)

**Update (Jan 28, 2022)**: This protocol has been updated. The user can now select between the [Opentrons P300 GEN2 Single-Channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) or the [Opentrons P300 GEN2 8-Channel pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette).

Parameters:
* `.csv input file`: Input file (see above)
* `Source plate type`: Opentrons compatible 96 well plate containing DNA samples
* `Destination plate type`: Opentrons compatible 96 well plates where DNA samples are diluted with water
* `Tuberack/tubes`: Tuberack/tube combination for DNA and water bins and DNA pool.
* `P300 type`: Single or multichannel: Only used for the initial water distribution
* `Air gap volume`: Volume of air for all air gaps, default is 10 µL

---

![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Labware
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [An Opentrons compatible 96-well sample source plates](https://labware.opentrons.com/?category=wellPlate)
* [An Opentrons compatible 96-well target plates](https://labware.opentrons.com/?category=wellPlate)

### Pipettes
* [P300 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/) or
* [P300 multi-Channel (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [P20 single-Channel (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)

**Tip racks**

* [Opentrons 200 µL filter tiprack](https://shop.opentrons.com/opentrons-200ul-filter-tips/)
* [Opentrons 20 µL filter tiprack](https://shop.opentrons.com/opentrons-20ul-filter-tips/)

### Reagents
NEST 12-channel reservoir (slot 11)
* channel 1: Water for dilution
* channel 2: Water waste destination for initial water distribution
Tuberack with 1.5 mL tubes  
* Tubes in position A1, B1: Water waste tubes for removing water before DNA addition
* Tubes in position C1, D1: DNA waste tubes after DNA distribution

---

### Deck Setup
Slots:
1. 20 µL filter tip-rack (B)
2. Empty
3. 20 µL filter tip-rack (A)
4. Final Plate B
5. Tuberack
6. Final Plate A
7. DNA Plate B
8. Empty
9. DNA Plate A
10. 200 µL filter tip-rack
11. Water reservoir
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/66e60f/deck.jpg)

### Reagent Setup
* Water Reservoir: slot 11
![Water reservoir on 11](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/66e60f/water_res.jpg)
* Tuberack: slot 5  
![Tuberack](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/66e60f/tuberack.jpg)

### Protocol Steps
1. The protocol distributes water to each column that has a well in the inout csv file using the 300 µL multi-channel pipette to the final plate (A and B). These tips blow out into the water reservoir well 2 and are then discarded.
2. A volume of water equal to the DNA volume in the csv line is removed from the well and dispensed into tube A1 or B1 on the tuberack with a blow out and touch tip.
3. The same volume of DNA is transferred from DNA plate A or B to final plate A or B using the same tip. An air gap is added to prevent contamination of other samples.
4. The tip touches the sides of the destination well.
5. The tip blows out into tube C1 or D1.
6. The tip is parked for reuse.
7. Step 2 to 6 are repeated for each well.
8. Reusing each parked tip in turn 5 µL of diluted DNA sample is transferred, with an air gap, to the DNA pooling tube in position in position A2. Finally the tip is discarded

## Process
1. Input the normalization .csv file
2. Select your source plate containing DNA samples (A: located on 9, B: located on slot 7)
3. Select your destination plate where samples will be mixed with water (located on A: slot 6, B: slot 4)
4. Select your tuberack/tube type on slot 5
5. Decide on any other parameter
6. Download your protocol.
7. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
8. Set up your deck according to the deck map.
9. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
8. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

##### Internal
66e60f
