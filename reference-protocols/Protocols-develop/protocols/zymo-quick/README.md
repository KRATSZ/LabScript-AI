# Zymo Quick-DNA/RNA Viral Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
	* Zymo Kit


## Description
This protocol automates nucleic acid purification with the [Zymo Quick-DNA/RNA Viral MagBead Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead).</br>
</br>
Using the P300 Multi-Channel Pipette and a Single-Channel Pipette, this protocol can accommodate up to 48 samples per run and can be configured to run any multiple of 8 up to 48. Starting with 400µL of sample in a deepwell plate, the entire process is automated and ends with 60µL of elution containing nucleic acid dispensed into a 96-well PCR plate. The elution is then ready for RT/qPCR, Next-Gen Sequencing, hybridization, etc.</br>
</br>
This kit can be used for Station B (RNA extraction) of our [COVID Workstation](https://blog.opentrons.com/how-to-use-opentrons-to-test-for-covid-19/).

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Magnetic Module, GEN1](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Opentrons P300 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/8-channel-electronic-pipette)
* (5) [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips) (recommended) or [Opentrons 300µL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons P20 (or P10) Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 10/20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)
* [NEST 96-Deep Well Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate)
* [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml)
* [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml)
* [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* [1.5mL Centrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [Zymo Quick-DNA/RNA Viral MagBead Kit](https://www.zymoresearch.com/collections/quick-dna-rna-viral-kits/products/quick-dna-rna-viral-magbead)
* Samples
* 15mL Falcon Tube



---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Reagent Preparation**</br>
Prepare all reagents according to Zymo manual.</br>
</br>
![Reagents in 12-Well Reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/zymo-rna-extraction/zymo_reservoir.png)
</br>
</br>
**Proteinase K**: In 1.5mL centrifuge tube, placed in "D1" in [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with 24-slot top.</br>
**Viral DNA/RNA Buffer + MagBinding Beads**: In slots 1, 2, and 3 in the 12-well reservoir. For every column (8 samples), 7mL of Viral DNA/RNA Buffer should be combined with 175µL of MagBinding Beads. Up to two columns (16 samples) worth of buffer+beads can be prepared in one Falcon Tube at a time. Each slot of the 12 well reservoir can accommodate volume for 2 columns/16 samples and should be loaded sequentially (ex. if running 24 samples, slot 1 would get 14mL buffer + 350µL beads, slot 2 would get 7mL buffer + 175µL beads, slot 3 would be empty).</br>
**MagBead DNA/RNA Wash 1**: In slots 4 and 5 in the 12-well reservoir. Each slot can accommodate enough volume for 24 samples (3 columns). Each slot would get 13.5mL if running 48 samples and would be scaled back if running less (ex. if running 24 samples, slot 4 would get 13.5mL, slot 5 would be empty).</br>
**MagBead DNA/RNA Wash 2**: In slots 6 and 7 in the 12-well reservoir. Each slot can accommodate enough volume for 24 samples (3 columns). Each slot would get 13.5mL if running 48 samples and would be scaled back if running less (ex. if running 24 samples, slot 6 would get 13.5mL, slot 7 would be empty).</br>
**Ethanol Wash 1**: In slots 8 and 9 in the 12-well reservoir. Each slot can accommodate enough volume for 24 samples (3 columns). Each slot would get 13.5mL if running 48 samples and would be scaled back if running less (ex. if running 24 samples, slot 8 would get 13.5mL, slot 9 would be empty).</br>
**Ethanol Wash 2**: In slots 10 and 11 in the 12-well reservoir. Each slot can accommodate enough volume for 24 samples (3 columns). Each slot would get 13.5mL if running 48 samples and would be scaled back if running less (ex. if running 24 samples, slot 10 would get 13.5mL, slot 11 would be empty).</br>
**Nuclease-Free Water**: In slot 12 in the 12-well reservoir. To accommodate 24 samples or less, 4mL of water should be used. For more than 24 samples, 4.5-5mL of water can be used.</br>
</br>
**Deck Layout**</br>
![Deck Layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/zymo-rna-extraction/zymo_deck_layout.png)
</br>
**Slot 1:**: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 2:**: [NEST 12-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml) with Zymo Kit Reagents</br>
**Slot 3:**: [NEST 96-Well PCR Plate](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
**Slot 4:**: [Opentrons Magnetic Module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck) with [NEST 96-Deep Well Plate, 2mL](https://labware.opentrons.com/nest_96_wellplate_2ml_deep?category=wellPlate) loaded with 400µL of sample in **odd columns**</br>
**Slot 5:**: [Opentrons 10/20µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-20ul-filter-tips)</br>
**Slot 6:**: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 7:**: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 8:**: [Opentrons 4-in-1 Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with Proteinase K in "D1"</br>
**Slot 9:**: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 10:**: [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)</br>
**Slot 11:**: [NEST 1-Well Reservoir](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml), empty for liquid waste</br>
</br>
*Note about tips*: Each column of samples (8) requires ten columns of tips for this extraction. For 48 samples, all the tips in the five tip racks will be used; if running less than 48 samples, less tips/tipracks will be used and the tipracks will be accessed in this slot order: 1, 6, 9, 7, 10.</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Number of Samples**: Select the number of samples to run
* **P300-Multi Generation**: Select which generation P300-Multi is being used
* **Single Channel Pipette**: Select which single channel pipette is being used



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tipracks, and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
zymo-quick
