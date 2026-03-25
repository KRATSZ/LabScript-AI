# Magnetic Bead Purification + PCR


### Author
[Opentrons](https://opentrons.com/)




## Categories
* PCR
	* PCR


## Description
The protocol begins with a bead-based cleanup. Note: each well for the ethanol in the reservoir is per 24 samples. That is, for 48 samples, load two wells of ethanol. For 48-72 samples, 3 wells of ethanol, so on and so forth. The ethanol should be distributed evenly among all wells (volume is the same in each well). The protocol will automatically pause when the tips are depleted, asking the user to resume the protocol.

Since this protocol uses a custom plate on the magnetic module, please ensure that the magnetic height variable down below is set to the correct height - the user will have to adjust this number to what's best for their plate. Ideally, the top of the magnet is to come just below, but not touching the bottom of the plate when engaged. The reagent rack should be placed on the temperature module which will be at 4C to keep the mastermix cool.

The last 4 wells of the reservoir are used for trash.


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* Abgene™ 96 Well 0.8mL Thermo Scientific #AB0859
* [NEST 12 Well Reservoir 15 mL #360102](http://www.cell-nest.com/page94?_l=en&product_id=102)
* [NEST 96 Well Plate 100 µL PCR Full Skirt #402501](http://www.cell-nest.com/page94?_l=en&product_id=97&product_category=96)
* Opentrons 96 Filter Tip Rack 200 µL


### Pipettes
* [Opentrons P300 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ca318/Screen+Shot+2023-04-03+at+2.31.47+PM.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/0ca318/Screen+Shot+2023-04-03+at+2.52.58+PM.png)


### Protocol Steps
1. Centrifuge the Amplicon PCR plate at 1,000 × g at 20°C for 1 minute to collect condensation, then carefully remove seal.
2. [Optional - for use with shaker for mixing] Using a multichannel pipette set to 25 µl, transfer the entire Amplicon PCR product from the PCR plate to the MIDI plate/96-well PCR plate. Change tips between samples.
3. Vortex the AMPure XP beads for 30 seconds to make sure that the beads are evenly dispersed. Add an appropriate volume of beads to a trough depending on the number of samples processing.
4. Using a multichannel pipette, add 20 µl of AMPure XP beads to each well of the
Amplicon PCR plate. Change tips between columns.
5. Gently pipette entire volume up and down 10 times if using a 96‐well PCR plate
6. Incubate at room temperature without shaking for 5 minutes.
7. Place the plate on a magnetic stand for 2 minutes or until the supernatant has cleared.
8. With the Amplicon PCR plate on the magnetic stand, use a multichannel pipette to
remove and discard the supernatant. Change tips between samples.
9. With the Amplicon PCR plate on the magnetic stand, wash the beads with freshly prepared 80% ethanol as follows:
a Using a multichannel pipette, add 200 µl of freshly prepared 80% ethanol to each sample well.
b Incubate the plate on the magnetic stand for 30 seconds.
c Carefully remove and discard the supernatant.
10. With the Amplicon PCR plate on the magnetic stand, perform a second ethanol wash as follows:
a Using a multichannel pipette, add 200 µl of freshly prepared 80% ethanol to each sample well.
b Incubate the plate on the magnetic stand for 30 seconds.
c Carefully remove and discard the supernatant.
d Use a P20 multichannel pipette with fine pipette tips to remove excess ethanol.
11. With the Amplicon PCR plate still on the magnetic stand, allow the beads to air‐dry for 10 minutes.
12. Remove the Amplicon PCR plate from the magnetic stand. Using a multichannel pipette, add 52.5 µl of 10 mM Tris pH 8.5 to each well of the Amplicon PCR plate.
13. Gently pipette mix up and down 10 times, changing tips after each. Make sure that beads are fully resuspended.
14. Incubate at room temperature for 2 minutes.
15. Place the plate on the magnetic stand for 2 minutes or until the supernatant has cleared.
16. Using a multichannel pipette, carefully transfer 50 µl of the supernatant from Amplicon PCR plate to a new 96‐well PCR plate. Change tips between samples to avoid cross‐contamination.


### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".


### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).


###### Internal
0ca318
