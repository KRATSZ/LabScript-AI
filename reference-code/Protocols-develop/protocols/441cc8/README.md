# Prepare Stock Plates for Indexing with Universal Illumina Primers

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
     * PCR Prep

## Description
This protocol uses a p300 multi-channel pipette to suspend a column of indexing primers (contained in a 96-well PCR plate) in master mix (contained in a reagent reservoir) and then distributes 14 ul of this mixture to the corresponding column of each of 9 PCR plates (in order as shown in the attached deck map). This process is repeated for all columns of the primer plate to fill all columns of the 9 PCR plates.

The liquid handling method used for the master mix includes the following features:

slow flow rate for aspiration and dispense
wait for liquid to finish moving after aspiration and dispense
avoid introducing air into liquid (avoid complete dispenses)
dispense to a surface
withdraw tip slowly from liquid

Links:
* [Deck Layout](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-04-29/ic13rvh/deck_layout_v2.pdf)
* [Process Steps](https://s3.amazonaws.com/pf-upload-01/u-4256/0/2021-04-29/zs03rlp/Opentrons%20-%20protocol%20development%20Quiagen%20multiplex%20plus%201.pdf)

With this protocol, your robot can prepare stock plates containing master mix and indexing primers to be used for the indexing step of an NGS library prep workflow.

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [QIAGEN Multiplex PCR Kit](https://www.qiagen.com/us/shop/pcr/qiagen-multiplex-pcr-kit/)
* [Illumina primers](https://support.illumina.com/bulletins/2020/06/illumina-adapter-portfolio.html)

## Process
1. Input your reduced pipetting flow rate for the master mix (in ul/sec), delay times for aspirate and dispense (in seconds), well bottom clearances (in millimeters), and labware choice for 200 ul tips, reagent reservoir and pcr plates.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map below.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

###### Internal
441cc8
