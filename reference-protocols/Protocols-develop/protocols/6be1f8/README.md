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

* Serial dilution of antibody from stock
* 96 well block prepped with diluent and mAb207 antibodies
* 96 well block prepped with diluent and mAb210 antibodies
* Transfer of antibody to 3, 384 well control plates

Explanation of complex parameters below:
* `Mix repetitions`: Specify the number of mix repetitions.
* `Initial volume diluent tubes`: Specify the initial volume in both diluent tubes. This is used for liquid height tracking.
* `P1000 aspirate/dispense flow rate`: Specify the p1000 aspirate and dispense flow rates.
* `P1000 aspiration/dispense bottom clearance (mm)`: Specify the aspiration and dispense clearance from the bottom of the well for the P1000 pipette (to avoid plate pick up). The default value is 1mm from the bottom of the well.
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
* Sample diluent
* mAb 210 (monoclonal antibody)
* mAb 207 (TF positive calibrant control)
* Sigma negative

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6be1f8/Screen+Shot+2021-06-14+at+11.59.48+AM.png)

### Reagent Setup

* Tube Rack: Slot 8
![](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6be1f8/Screen+Shot+2021-06-14+at+11.59.34+AM.png)


---

### Protocol Steps
1. Transfer diluent to mAb210 100ug/ml tube
2. Transfer  mAb210 stock to mAb210 100ug/ml tube
3. Mix mAb210 100ug/ml tube x10
4. Repeat steps (1-3) for mAb210 20ug/ml and 2ug/ml
5. Transfer diluent to 'A1', 'A2', 'B1', 'B2', 'C1', 'G1', 'C2', 'E2', 'D1', 'D2', 'E1', 'F1', 'G1', 'G2', 'H1', 'H2'
6. Transfer mAb207 to same wells
7. Transfer diluent and mAb210 to column 3 of masterblock.
8. Transfer 180ul A1, B1, C1, D1, E1, F1, G1 and H1 masterblock to A1, C1, E1, G1, I1, K1, M1, O1 control plate 1 and control plate 2
9. Transfer 80ul A1, B1, C1, D1, E1, F1, G1 and H1 masterblock to A1, C1, E1, G1, I1, K1, M1, O1 control plate 3
10. Transfer 180ul A2, B2, C2, D2, E2, F2, G2 and H2 masterblock to B1, D1, F1, H1, J1, L1, N1, P1 control plate 1 and control plate 2
11. Transfer 80ul A2, B2, C2, D2, E2, F2, G2 and H2 masterblock to B1, D1, F1, H1, J1, L1, N1, P1 control plate 3
12. Transfer 180ul A3, B3, C3, D3, E3, F3, G3 and H3 masterblock to A2, C2, E2, G2, I2, K2, M2, O2 control plate 1 and control plate 2
13. Transfer 80ul A3, B3, C3, D3, E3, F3, G3 and H3 masterblock to A2, C2, E2, G2, I2, K2, M2, O2 control plate 3
14. Transfer 180ul A3, B3, C3, D3, E3, F3, G3 and H3 masterblock to B2, D2, F2, H2, J2, L2, N2, P2 control plate 1 and control plate 2
15. Transfer 80ul A3, B3, C3, D3, E3, F3, G3 and H3 masterblock to B2, D2, F2, H2, J2, L2, N2, P2 control plate 3


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
6be1f8
