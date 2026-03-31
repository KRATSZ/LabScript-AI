# PCR Prep and Pooling with 384 Plates - Stage 1


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR Prep

## Description
This protocol is Stage 1 of a 3 part PCR Prep protocol. Parts 2 and 3 can be found below. For detailed protocol details, please reference the "Protocol Steps" section. This protocol pools 4 plates one at a time into a fresh 384 well plate with water. Each PCR plate is pooled in order A1, A2, B1, B2 to A1 pool, then A3, A4, B3, B4 to A3 pool, etc. The next plate will pool all of the same source wells, but the destination wells of the pool will start at B1, skipping every other well. PCR plate 3 will start pooling at B1, and PCR plate wills start pooling at B2.

[Stage 2 Protocol](https://protocols.opentrons.com/protocol/08fd01-pt2)
[Stage 3 Protocol](https://protocols.opentrons.com/protocol/08fd01-pt3)

---

### Labware
* Nest 12 Well Reservoir](https://shop.opentrons.com/consumables/
* Opentrons 20ul Filter tips
* Custom 384 well plate

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)


---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/08fd01/deck+setup+new+version+optimization.png)


---

### Protocol Steps
1. 12ul of water is added to all wells in pool plate (same tip).
2. 3ul of sample is pooled onto pool plate one plate at a time beginning in slot 1 (fresh tip).

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
08fd01
