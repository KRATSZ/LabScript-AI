# Media Aliquoting

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Aliquoting

## Description
This protocol performs sample aliquoting from a single-channel reservoir to up to 24 custom cryotubes. The sample order is down columns and then across rows (A1, B1, C1, D1, A2, B2, etc.)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [NEST 1 Well Reservoir 195 mL](https://labware.opentrons.com/nest_1_reservoir_195ml)
* [Opentrons P1000 GEN2 single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549142557)
* [Opentrons 96 Tip Rack 1000 µL](https://labware.opentrons.com/opentrons_96_tiprack_1000ul)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the number of samples to process (1-24), the transfer volume (in µl), and the mount side for your P1000 GEN2 single-channel pipette.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
53134e
