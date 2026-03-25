# KingFisher Flex Magnetic Particle Processing Plate Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol automates preparation of plates that will be used in the Magnetic Particle Processing protocol on the KingFisher Flex.

This protocol is still a work in progress and will be updated.


Explanation of complex parameters below:
* **Number of Samples**: Specify the number of samples to be run (1-96).
* **Pipette Mount**: Select which mount the [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette) is attached to.


---


### Labware
* [Opentrons 200µL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [Opentrons 4-in-1 Tube Rack (with 24 Well Insert)](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1)
* Reservoirs for Wash Buffers (like the [NEST 1-Well Reservoir, 195mL](https://shop.opentrons.com/collections/verified-labware/products/nest-1-well-reservoir-195-ml))
* Reservoir for Elution Buffer (like the [NEST 12-Well Reservoir, 15mL](https://shop.opentrons.com/collections/verified-labware/products/nest-12-well-reservoir-15-ml))
* [1.5mL Mictrocentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes)
* [KingFisher 96-Deepwell Plate](https://www.thermofisher.com/order/catalog/product/A48305?SID=srch-hj-a48305#/A48305?SID=srch-hj-a48305)
* [KingFisher 96-Well Microplate](https://www.thermofisher.com/order/catalog/product/97002540?SID=srch-srp-97002540#/97002540?SID=srch-srp-97002540)

### Pipettes
* [P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)

### Reagents
* Wash Buffer 1
* Wash Buffer 2
* Elution Buffer
* Proteinase K

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/743f54/743f54_deck.png)

### Reagent Setup
**Reservoir (Deck Slot 7):**</br>
Wash Buffer 1 (500µL per sample)</br>
</br>
**Reservoir (Deck Slot 8):**</br>
Wash Buffer 2 (1000µL per sample)</br>
</br>
**Reservoir (Deck Slot5):**</br>
Elution Buffer (50µL per sample)</br>
</br>
**[Opentrons Tube Rack](https://shop.opentrons.com/collections/verified-labware/products/tube-rack-set-1) with [1.5mL Mictrocentrifuge Tube](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) (Deck Slot 6):**</br>
A1: Samples 1-24 (140µL in tube)</br>
B1: Samples 25-48 (140µL in tube)</br>
C1: Samples 49-72 (140µL in tube)</br>
D1: Samples 73-96 (140µL in tube)</br>
</br>

---

### Protocol Steps
1. The pipette ([P300 Single-Channel Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)) will pick up a new tip, transfer 500µL (175/175/150) of Wash Buffer 1 to user-specified number of wells in the [KingFisher 96-Deepwell Plate](https://www.thermofisher.com/order/catalog/product/A48305?SID=srch-hj-a48305#/A48305?SID=srch-hj-a48305) in slot 4, then drop tip in the trash.
2. The pipette  will pick up a new tip, transfer 1000µL (200 x5) of Wash Buffer 2 to user-specified number of wells in the [KingFisher 96-Deepwell Plate](https://www.thermofisher.com/order/catalog/product/A48305?SID=srch-hj-a48305#/A48305?SID=srch-hj-a48305) in slot 1, then drop tip in the trash.
3. The pipette  will pick up a new tip, aspirate 200µL of Elution Buffer and dispense 50µL to user-specified number of wells (aspirating 200µL more whenever needed) in the [KingFisher 96-Deepwell Plate](https://www.thermofisher.com/order/catalog/product/A48305?SID=srch-hj-a48305#/A48305?SID=srch-hj-a48305) in slot 2, return any remaining Elution Buffer in the tip to the source, and finally drop the tip in the trash.
4. The pipette  will pick up a new tip, aspirate 140µL of Proteinase K and dispense 5µL to user-specified number of wells (in groups of 24) in the [KingFisher 96-Well Microplate](https://www.thermofisher.com/order/catalog/product/97002540?SID=srch-srp-97002540#/97002540?SID=srch-srp-97002540) in slot 3, then drop tip in the trash.


### Process
1. Input your protocol parameters above.
2. Download your protocol.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions), if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
743f54
