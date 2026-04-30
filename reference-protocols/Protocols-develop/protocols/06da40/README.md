# Normalization and ddPCR Setup


### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Normalization & PCR Prep


## Description
This protocol prepares plates for ddPCR with a normalization step beforehand.

Based on a user-supplied CSV, the protocol begins by performing a normalization from the plate in deck slot 4 to the plate in deck slot 5 (allowing one to preserve their original samples).

After the normalization step, there is an optional reaction mix creation step. Once reaction mix is ready, each well of the destination plate(s) receive 18µL of reaction mix.

The protocol finishes by adding 4µL of each sample to a well containing reaction mix, per replicate. For example, if 3 replicates are selected, 4µL of the normalized sample in A1 would be dispensed in A1, B1, and C1 of the destination plate, followed by 4µL of normalized sample from A2 to D1, E1, F1, etc.

**Explanation of complex parameters below:**
* **.CSV Input File**: Upload CSV file. Should include a header row and the first three rows: Well (A1), Sample Volume (µL), Dilutent Volume (µL)
* **Automate Reaction Mix Creation**: Select whether to automate the creation of Reaction Mix.
* **Number of Replicates**: Specify the number of replicates

### Labware
* [NEST 96-Well PCR Plate 100µL](https://shop.opentrons.com/nest-0-2-ml-96-well-pcr-plate-full-skirt/)
* [Opentrons 24 Tube Rack with Eppendorf 1.5mL Safe-Lock Snapcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [Opentrons Tip Rack, 20µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [Opentrons Tip Rack, 300µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* Semi-skirted Plate on Aluminum Block


### Pipettes
* [Opentrons P20 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/06da40/Screen+Shot+2023-01-04+at+10.07.20+AM.png)


### Reagent Setup
![reagents2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/06da40/Screen+Shot+2023-01-04+at+9.59.50+AM.png)
![reagents1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/06da40/Screen+Shot+2023-01-04+at+10.00.02+AM.png)



### Protocol Steps
0. (User) Ensure that all necessary reagents are loaded with appropriate volumes.
1. Dilutent is transferred to all wells of Normalization Plate.
2. Samples are individually transferred to Normalization Plate.
3. (Optional) Reaction Mix is created.
4. 18µL of Reaction Mix is distributed to each well of the Destination Plate(s).
5. 4µL of Normalized Sample is added (in replicate) to the Destination Plate(s).


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `Labware` > `Import`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/s/article/How-positional-calibration-works-on-the-OT-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
06da40
