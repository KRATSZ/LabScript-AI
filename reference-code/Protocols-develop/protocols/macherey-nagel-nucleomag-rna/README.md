# MACHEREY-NAGEL NucleoMag® RNA


### Author
[MACHEREY-NAGEL](https://www.mn-net.com/us)

### Partner
[Opentrons](https://opentrons.com/)




## Categories
* Nucleic Acid Extraction & Purification
	* MACHEREY-NAGEL NucleoMag® RNA


## Description
![MACHEREY-NAGEL](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/macherey-nagel/MN_Logo_50.jpeg)

This protocol automates the NucleoMag® RNA kit for flexible magnetic bead based isolation of RNA from tissue and cell samples.

Before beginning the protocol on the OT-2, the following preparation steps are needed.
1. Perform the lysis accoding to the NucleoMag® RNA user manual.
2. Prepare the rDNase reaction mixture according to the NucleoMag® RNA user manual.
3. Fill the 12-Well Buffer Reservoir according to the table below.
4. Resuspend the NucleoMag B-Beads by vortexing and place them in Position A1 of the 2mL Tube Rack.
5. Load the instrument deck according to the displayed positions.
6. Place the Square-well Block containing the lysates on the Magnetic Module and start the run.

You can access the full descripition of this workflow on the OT-2 by visiting this link: [link](https://insights.opentrons.com/hubfs/Partners/Macherey-Nagel/NucleoMag%20RNA%20on%20OT-2%20Protocol%20Info.pdf)


### Modules
* [Opentrons Magnetic Module (GEN2)](https://shop.opentrons.com/magnetic-module-gen2/)


### Labware
* 96 Well PCR Plate
* [Opentrons 96 Tip Rack 300 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 24 Tube Rack with Generic 2 mL Screwcap](https://shop.opentrons.com/collections/opentrons-tips/products/tube-rack-set-1)
* [USA Scientific 12 Well Reservoir 22 mL #1061-8150](https://www.usascientific.com/12-channel-automation-reservoir.aspx)
* [Opentrons 96 Tip Rack 1000 µL](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-tips)
* 96 Deepwell Plate 2mL
* [Agilent 1 Well Reservoir 290 mL #201252-100](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)


### Pipettes
* [Opentrons P300 8 Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/8-channel-electronic-pipette/)
* [Opentrons P1000 Single Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/single-channel-electronic-pipette-p20/)


### Deck Setup
![deck](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/macherey-nagel/deck.png)


### Reagent Setup
![reagents](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/macherey-nagel/reagents.png)


### Protocol Steps
1. Binding Step
2. rDNase Digestion
3. Wash 1
4. Wash 2
5. Wash 3
6. Elution
</br>
</br>
* Note
The default values for all volumes, incubation times and mix repetitions were pretested and validated.
We do not recommend to change them. If you still decide to change them please scale all volumes proportionally.
For change recommendations please contact automation-bio@mn-net.de
</br>
</br>

**Process**
1. Input your protocol parameters below.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit "Run".
</br>
</br>
**Additional Notes**
</br>
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
</br>
**Disclaimer**: MACHEREY-NAGEL GmbH & Co. KG makes every effort to include accurate and up-to-date information within this publication; however, it is possible that omissions or errors might have occurred. MACHEREY-NAGEL GmbH & Co. KG cannot, therefore, make any representations or warranties, expressed or implied, as to the accuracy or completeness of the information provided in this publication. Changes in this publication can be made at any time without notice. For technical details and detailed procedures of the specifications provided in this document please contact your MACHEREY-NAGEL representative. This publication may contain reference to applications and products which are not available in all markets. Please check with your local sales representative.
All mentioned trademarks are protected by law. All used names and denotations can be brands, trademarks, or registered labels of their respective owner – also if they are not special denotation. To mention products and brands is only a kind of information (i.e., it does not offend against trademarks and brands and can not be seen as a kind of recommendation or assessment). Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise, does not necessarily constitute or imply its endorsement, recommendation, or support by MACHEREY-NAGEL GmbH & Co. KG or Opentrons. Any views or opinions expressed herein by the authors' do not necessarily state or reflect those of MACHEREY-NAGEL or the Eppendorf AG. NucleoMag® is a registered trademark of MACHEREY-NAGEL GmbH & Co. KG, Düren, Germany. Opentrons OT-2 is a device from Opentrons, New York, USA.
</br>
* The Download links includes all Protocols in their respective subfolders as well as the .json files for the two labware files.


###### Internal
macherey-nagal-nucleomag-rna
