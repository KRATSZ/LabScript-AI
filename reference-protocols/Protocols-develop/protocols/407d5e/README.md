# Protein  Labeling with Incubation

### Author
[Opentrons](http://www.opentrons.com/)



## Categories
* Proteins & Proteomics
    * Assay

## Description
This workflow is comprised of a protein labelling protocol that begins by adding several reagents to samples and then incubating at 37C for several days (up to 4) and aliquoting 20µL of the incubating samples. For more information about this protocol, including materials needed and customizable parameters, please see below before downloading.</br>
</br>

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons Temperature Module with Aluminum Blocks](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [P300 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [P20 Single-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes/products/single-channel-electronic-pipette)
* [Opentrons 300µl Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 20µL Pipette Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [NEST 96-Well PCR Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [NEST 1.5mL Microcentrifuge Tubes](https://shop.opentrons.com/collections/verified-consumables/products/nest-microcentrifuge-tubes) & Tubes for Samples
* Reagents
* Samples


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Using the customizations field (below), set up your protocol.**
* **Number of Samples (1-19)**: Specify the number of samples to run (1-19).
* **Number of Incubations**: Specify the number of incubations. The protocol will transfer 20µL to the destination plate and repeat the process, up to three times, at the 1, 2, and 4 day mark.
* **Labware Containing Samples**: Select the type of tube that will be used to contain the samples. This tube should be place in the 24-Well Aluminum Block.
* **Temperature Module**: Select which generation of the Temperature Module will be used.
* **Reset Tipracks?**: This protocol can save the state of the tipracks after each run for the P300 and the P20. If this is set to "Yes" (or the protocol is run for the first time on the robot), the protocol will begin picking up tips from the A1 of Tiprack 1 for each pipette. If set to "No", the saved tip state from the previous run will be accessed and the pipette will begin using tips where the previous protocol run left off. The user will be prompted to replace the corresponding tip racks.
</br>
</br>

**Deck Layout**</br>
</br>
**Slot 1**: Destination Plate ([NEST 96-Well PCR Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)) - 20µL of sample aliquots will be transferred here. This should be replaced for transfer after incubation(s).</br>
</br>
**Slot 2**: [24-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) containing Tubes (specified by user) with Samples</br>
</br>
**Slot 3**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips) (Tiprack 3)</br>
</br>
**Slot 4**: [Opentrons Temperature Module](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck) with 96-Well Aluminum Block and [NEST 96-Well PCR Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)</br>
</br>
**Slot 5**: [NEST 96-Well PCR Plates](https://shop.opentrons.com/collections/verified-labware/products/nest-0-1-ml-96-well-pcr-plate-full-skirt) (Empty, for mixing)</br>
</br>
**Slot 6**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips) (Tiprack 2)</br>
</br>
**Slot 7**: [24-Well Aluminum Block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set) containing 1.5mL NEST Tubes with Reagents</br>
</br>
**Slot 8**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (Tiprack 1)</br>
</br>
**Slot 9**: [Opentrons 20µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips) (Tiprack 1)</br>
</br>
**Slot 10**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (Tiprack 3)</br>
</br>
**Slot 11**: [Opentrons 300µL Tiprack](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips) (Tiprack 2)</br>
</br>

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
If you have any questions about this protocol, please contact protocols@opentrons.com.

###### Internal
407d5e
