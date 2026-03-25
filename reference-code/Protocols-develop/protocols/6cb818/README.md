# Anti-CD154 Labeling of Peptide- and PMA-Stimulated Cells

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
     * Staining

## Description

This protocol uses a p20 single-channel pipette to transfer 5 uL anti-CD154 from a 1.5 mL screw-cap tube to wells A1 and A2 (already containing 200 uL of suspended cells) of a 96-well culture plate. The cells are then mixed and aliquoted into wells B1-E1 and B2-E2 of the culture plate. Wells B1-B2, C1-C2, D1-D2 and E1-E2 are then treated with either one of three peptides or PMA-Ca. Finally, well volumes are optionally adjusted to 100 uL total by addition of culture medium.

Links:
* [experimental protocol](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6cb818/Protocol_ForCustom_Opentrons_9-21-21.docx)


This protocol was developed to mix anti-CD154 with cultured cells suspended in culture medium and then aliquot the cells to wells of a 96-well culture plate where the cells are treated either with one of three different peptides or PMA-Ca. Volumes are optionally adjusted to 100 uL total by addition of culture medium.

## Protocol Steps

Set up: Place each of these items in your selected deck slot locations on the OT-2 deck: Your selected (regular or filtered) Opentrons 20 ul tips, Selected 96-well culture plate with cells suspended in a 200 uL volume, Opentrons 24-Tube Rack with 1.5 mL Snap Cap Tubes containing your specified starting volumes of peptides 1-3 and PMA-Ca, Opentrons 24-Tube Rack with 1.5 mL Screw Cap Tubes containing your specified starting volumes of anti-CD154 and culture medium.

The OT-2 will perform the following steps:
1. Use the p20 single to mix 5 uL of anti-CD154 with the suspended cells in A1 and A2 of the culture plate. Mix.
2. Use the p20 single to mix the suspended cells and then aliquot 40 uL to B1-E1 and B2-E2 of the culture plate.
3. Use the p20 single to add peptide 1 to B1-B2, peptide 2 to C1-C2, peptide 3 to D1-D2, and PMA-Ca to E1-E2.
4. Optionally use the p20 single to add 60 uL of culture medium to A1-E1 and A2-E2 to bring the total volume per well to 100 uL.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Single-Channel p20 Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons Regular and Filter Tips for the p20](https://shop.opentrons.com/collections/opentrons-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6cb818/layout_6cb818.png)
![reagents in 1.5 mL snap cap tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6cb818/Reagents+in+1.5+ML+Snap+Cap+Tubes.png)
![reagents in 1.5 mL screw cap tubes](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6cb818/Reagents+in+1.5+ML+Screw+Cap+Tubes.png)
![cells in culture plate](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/6cb818/Cells+in+Culture+Plate.png)

* Opentrons 20 ul filter or regular tips (selected deck slot)
* 96-Well Culture Plate with Cells in A1 and A2 (selected deck slot)
* Opentrons 24-Tube Rack Containing 1.5 mL Snap Cap Tubes (containing peptides 1-3 and PMA-Ca) (selected deck slot)
* Opentrons 24-Tube Rack Containing 1.5 mL Screw Cap Tubes (containing anti-CD154 and culture medium) (selected deck slot)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Use the protocol parameter settings on this page to specify starting volumes of culture medium and reagents, labware for the culture plate and tips, deck slot locations for the items on the OT-2 deck, and well bottom clearances.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
6cb818
