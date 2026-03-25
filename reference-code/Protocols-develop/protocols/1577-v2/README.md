# Custom Chip PCR Preparation

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description
This protocol performs PCR preparation on a custom 3x8 membrane chip on 6 PCR strips. Ensure that the chip is seated so that the wells of the second (middle) row are slightly offset to the **top** of the first and third rows as shown in 'Additional Notes' below. **Please calibrate the custom chip so that the pipette tip lands lands just barely above the membrane**-- this will ensure accurate liquid transfer without disturbing the eggs or crashing into the chip. For reagent setup, see 'Additional Notes' below.

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [P10 Multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5978967113757)
* [10µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [P50 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette?variant=5984549077021)
* [300µl Pipette tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 4-in-1 tube rack set](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [Tempassure 200ml PCR strips (seated)](https://www.usascientific.com/0.2ml-flex-free-pcr-8-tube-attached-clear-flat-caps.aspx)
* 1.7ml Eppendorf tubes
* Custom 3x8 offset membrane chip on shaker (mounted on OT-2 deck)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

4x6 tuberack for 2ml Eppendorf tubes:
* tube A1: nanopure H2O
* tube B1: reaction buffer
* tube C1: primer
* tube D1: DNA polymerase
* tube A2: mastermix tube (loaded empty)

Seated PCR strips:
* strip column 12: nanopure H2O (for additions with P10-multi channel pipette)

### Robot
* [OT-2](https://opentrons.com/ot-2)

### Reagents
* [MyTaq DNA Polymerase](https://www.bioline.com/us/mytaq-dna-polymerase.html)
* [MyTaq Reaction Buffer](https://www.bioline.com/us/mytaq-dna-polymerase.html)
* Nanopure H2O

## Process
1. Download your protocol.
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
5. Hit "Run".
6. Master mix is created in an empty tube through combining 15.5ul nanopure H2O, 5ul MyTaq Reaction Buffer, 10ul primer mix, and 0.25ul MyTaq DNA Polymerase per sample. Although 24 samples are being processed, 28 samples-worth of master mix is created to ensure sufficient volume. The contents of the tube are mixed after the final transfer to ensure homogeneity.
7. Each sample of the chip is transferred to the the PCR strips. Each of the 3 rows of the chip is transferred to a new PCR strip (strips 1-3). Samples moving across the row to the right move down the strip.
8. 21.75ul of master mix from step 6 is transferred to each well of PCR strips 4-6.
9. 3ul of each sample from strips 1-3 is transferred to its corresponding well in strips 4-6 (strip 1 well 1 to strip 4 well 1, strip 1 well 2 to strip 4 well 2, etc.). The contents of the destination well are mixed 10x after the transfer.

### Additional Notes
Chip Alignment on Shaker:
![Chip Alignment](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1577/chip2.png)

Reagent setup for 4x6 tube rack:
![Tube Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/1577/tube_setup.png)

If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
yYlOorFh
1577
