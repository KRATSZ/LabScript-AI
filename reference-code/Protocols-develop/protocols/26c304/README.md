# Sample Prep for ELISA Test of Monoclonal Antibodies

### Author
[Opentrons](https://opentrons.com/)

### Partner
[Partner Name](partner website link)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol preps 3, 384 well control plates for further testing of antibodies as part of a larger ELISA protocol. The protocol can be considered in 3 main parts:

* Serial dilution of antibody.
* 96 well block prepped with diluent and antibody.
* Transfer of antibody to 3, 384 well control plates.

Explanation of complex parameters below:
* `Mix repetitions`: Specify the number of mix repetitions.
* `Mix volume`: Specify the mix volume in microliters.
* `Initial volume diluent tubes`: Specify the initial volume in both diluent tubes. This is used for liquid height tracking.
* `P1000 aspiration/dispense bottom clearance (mm)`: Specify the aspiration and dispense clearance from the bottom of the well for the P1000 pipette (to avoid plate pick up). The default value is 1mm from the bottom of the well.
* `Mix height clearance`: Specify the height from the bottom of the well to mix (to prevent overflowing).
* `P1000 aspirate/dispense flow rate`: Specify the p1000 aspirate and dispense flow rates.
* `Touch tip radius`: Describes the proportion of the target well’s radius. When radius=1.0, the pipette tip will move to the edge of the target well; when radius=0.5, it will move to 50% of the well’s radius. Default: 1.0 (100%)
* `Touch tip v-offset`:  Specify the offset in mm from the top of the well to touch tip A positive offset moves the tip higher above the well, while a negative offset moves it lower into the well Default: -1.0 mm
* `Touch tip speed`:Specify the speed for touch tip motion, in mm/s. Default: 60.0 mm/s, Max:80.0 mm/s, Min: 20.0 mm/s
* `P20 Pipette Mount`: Specify which mount (left or right) to load your pipette.
* `P1000 Pipette Mount`: Specify which mount (left or right) to load your pipette.

---

### Labware
* Greiner 384 well plate 200ul
* Opentrons 4-in-1 tube rack - 2x3 grid with Appleton 50mL tubes
* Opentrons 4-in-1 tube rack - 4x6 grid with Axygen 1.7mL tubes
* Greiner 96 well plate 2000ul
* [Opentrons 20ul tip rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons 1000ul tip rack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)


### Pipettes
* [P1000 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)
* [P20 Single Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/single-channel-electronic-pipette)

### Reagents
* CR3022 (monoclonal antibody)
* mAb45 (Oxford – monoclonal antibody)
* mAb269 (monoclonal antibody)
* TF mAb45 (TF positive calibrant control)
* Sigma negative (negative serum sample, H6914)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6be1f8/Screen+Shot+2021-06-14+at+12.24.54+PM.png)

### Reagent Setup

* Note: Diluent tubes are switched after 1350ul of diluent is transferred to wells A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, B5, B6, C1, C2, C3, C4, C5, C6, D1, and D2 of the masterblock. Thus, at least 29mL of diluent should be in diluent tube A1, and 23mL of diluent should be in tube 2 for each run.

* Tube Rack: Slot 8
![](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6be1f8/Screen+Shot+2021-06-14+at+12.25.09+PM.png)


---

### Protocol Steps
1. Transfer diluent to 300ug/mL tubes for CR3022, mAb45, mAb269 antibodies.
2. Step down to 30ug/mL, 10ug/mL.
3. Dispense diluent to A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, B5, B6, C1, C2, C3, C4, C5, C6, D1, D2, D6, E1, G1, F1, H1, E2, E3, E4, E5, F2, F3, F4, F5, G2, G3, G4, G5, H2, H3, H4 and H5
4. Dispense 30ug/mL and 10ug/mL CR3022, mAb45, and mAb269 into masterblock
5. Add negative to masterblock
6. Add TF to masterblock
7. Mix and transfer solutions across masterblock (x4)
8. Transfer 180ul A1, B1, C1, D1 masterblock to A1, C1, E1, G1 and I23, L23, M23 and O23 of control plates 1, 2 and 3
9.  Transfer 180ul A2, B2, C2, D2 masterblock to B1, D1, F1, H1 and J23, K23, N23 and P23 of control plates 1, 2 and 3
10.  Transfer 180ul A3 and B3 masterblock to A2, C2 and L24, N24 of control plates 1, 2 and 3
11.  Transfer 180ul A3 and B3 masterblock to A2, C2 and L24, N24 of control plates 1, 2 and 3

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
26c304
