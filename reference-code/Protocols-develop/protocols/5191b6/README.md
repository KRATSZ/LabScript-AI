# High-Throughput Synthesis

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Cherrypicking


## Description
This protocol performs a custom cherrypicked high-throughput synthesis. It requires a CSV input for the mapping of the wells and vials on the tube racks. It also requires a CSV for high-throughput synthesis which contains the dispending volumes from each reservoir.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P1000 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P300 single-channel GEN2 electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Tube Racks](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

* [Vial Map CSV Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5191b6/vial_map.csv)
* [High-Throughput CSV Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5191b6/htp_multi_rack.csv)

Deck Setup
* P1000 Tips (Slot 1)
* P300 Tips (Slot 2)
* Reagent Reservoirs (Use High-Throughput CSV)
* Opentrons Tube Racks (Use Vial Map CSV)

Example of the Vial Map CSV [Download Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5191b6/vial_map.csv):

```
Well Number,Labware,Slot,Well Position
1,opentrons_24_tuberack_nest_2ml_screwcap,4,A1
2,opentrons_24_tuberack_nest_2ml_screwcap,4,A2
3,opentrons_24_tuberack_nest_2ml_screwcap,4,A3
...
96,opentrons_24_tuberack_nest_2ml_screwcap,7,D6
```

The Vial Map CSV can be used to place custom labware and different tube racks from the labware library. It also allows mapping of the well positions of each vial on a tube rack corresponding to the well number in the high-throughput synthesis protocol.

Example of the High-Throughput Synthesis Protocol CSV [Download Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5191b6/htp_multi_rack.csv)

```
*Note numbering starts from top left to top right,Reservoir 1,Reservoir 2,Reservoir 3,Reservoir 4,Reservoir 5,Reservoir 6,Reservoir 7,Reservoir 8,Reservoir 9,Reservoir 10,Reservoir 11,Reservoir 12,Reservoir 13,Reservoir 14,Reservoir 15,
Labware,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,rssrack_15_tuberack_2500ul,
Slot,3,3,3,3,3,3,8,8,8,8,8,9,9,9,9,
Well Position,A1,B1,C1,A2,B2,C2,A3,B3,C3,A4,B4,C4,A5,B5,C5,
Well Number,Metal Salt Stock Soln 1 (1 M) (uL),Metal Salt Stock Soln 2 (1 M) (uL),Metal Salt Stock Soln 3 (1 M) (uL),Metal Salt Stock Soln 4 (1 M) (uL),Organic Linker Stock Soln 1 (1 M) (uL),Organic Linker Stock Soln 2 (1 M) (uL),Organic Linker Stock Soln 3 (1 M) (uL),Organic Linker Stock Soln 4 (1M) (uL),Extra Solvent 1 (uL),Extra Solvent 2 (uL),Extra Solvent 3 (uL),Extra Solvent 4 (uL),,,,Total Volume (uL)
1,270,270,270,150,150,150,150,150,64,64,150,150,270,150,270,1088
2,27,270,270,150,150,150,150,150,48,48,150,150,27,150,27,813
3,34,270,270,150,150,150,150,150,48,48,150,150,34,150,34,821
```

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Upload Vial Map CSV and High-Throughput Synthesis Protocol CSVs. Choose pipette tips, pipette tip rack slots, pipette mounts, and aspiration/dispense heights.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
5191b6
