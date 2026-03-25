# Nucleic Acid Extraction Using 1.5mL Tubes

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Nucleic Acid Extraction

## Description
This protocol is a custom nucleic acid extraction that begins with the samples in 1.5mL tubes. This protocol utilizes the [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) and the [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) for this extraction.  
The protocol begins by adding 500µL of Buffer 1 to all tubes that will contain samples on the temperature module. Once complete, 500µL of sample is transferred from 1.5mL tubes in an [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) to the tubes containing Buffer 1.
After a heating step, DNA and Magnetic Beads are added to the sample tubes on the temperature module and the samples are transferred to a deepwell plate on the magnetic module.
Once on the magnetic module, the magnet is engaged and after the beads settle, the supernatant is removed. Using Buffer 2, three consecutive wash steps occur with the samples on the magnetic module.  
At this point, the user will be prompted to replace the tube(s) in the Tube Rack with Buffer 3 and the Reaction Mix (more info on this below). Buffer 3 will then be added to the beads, mixed with the beads, then transferred back to the temperature module for a 5 minute incubation at 65C.  
Post-incubation, the samples will be moved back to the deepwell plate on the magnetic module, but in a new, clean well. The magnet will engage after all of the samples have been transferred. Following this, the reaction mix will be distributed to all of destinations in PCR strips. The elution will then be transferred to a clean PCR strip, before 5µL gets transferred to two tubes containing the reaction mix.  
This concludes the OT-2 portion of the protocol and the user will be prompted to move the samples to 65c for a 20 minute incubation to complete the protocol.  

Adjust the parameters and download the protocol below.  

*Note*: This protocol is still a work in progress and will likely need further optimizations; please keep this in mind when using this protocol.  


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) (left mount)
* [P300 or P1000 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) (right mount)
* [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* Opentrons Filters Tips for [P300](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) or [P1000](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips)
* [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons Temperature Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [NEST 96-Deepwell Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [NEST 1.5mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* PCR Strips
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Layout**  

**Slot 1**: [Opentrons 96-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) with PCR Strips  
A1: Magnetic Beads  
B1: DNA  
Columns 2-4: Elution Destination (empty to begin)  
Columns 7-12: Reaction Mix + Elution Destination (empty to begin)  

**Slot 2**: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)  

**Slot 3**: Opentrons Filters Tips for [P300](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) or [P1000](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips) (Tiprack 3)  

**Slot 4**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [NEST 1.5mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)  
*Note*: At the beginning of the protocol, samples should be loaded in the tube rack. Once transferred:  
A1: Buffer 3  
A4: Reaction Mix  

**Slot 5**: [Opentrons 20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)  

**Slot 6**: Opentrons Filters Tips for [P300](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) or [P1000](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips) (Tiprack 2)  

**Slot 7**: [Opentrons Temperature Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with [Opentrons 24-Well Aluminum Block]((https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) containing [NEST 1.5mL Centrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)  

**Slot 8**: [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)  
A1: Buffer 1  
A2: Buffer 2 (Wash 1, Samples 1-12)  
A3: Buffer 2 (Wash 1, Samples 13-24)  
A4: Buffer 2 (Wash 2, Samples 1-12)  
A5: Buffer 2 (Wash 2, Samples 13-24)  
A6: Buffer 2 (Wash 3, Samples 1-12)  
A7: Buffer 2 (Wash 3, Samples 13-24)  

**Slot 9**: Opentrons Filters Tips for [P300](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) or [P1000](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-1000ul-filter-tips) (Tiprack 1)  

**Slot 10**: [Opentrons Magnetic Module, GEN2](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Deepwell Plate, 2mL](https://shop.opentrons.com/collections/verified-labware/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)  

**Slot 11**: [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml) (for liquid waste)  

**Using the customizations field (below), set up your protocol.**
* **Pipette & Tip Combo**: Select which pipette (right mount) and corresponding tips are being used in this protocol.
* **Number of Samples (1-24)**: Specify the number of samples to run (1-24).


### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Specify your parameters on this page.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support article](https://support.opentrons.com/ot-2/getting-started-software-setup/deck-calibration).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact [protocols@opentrons.com](mailto:protocols@opentrons.com).

###### Internal
1eeb01
