# AlphaLISA

### Author
[Opentrons](https://opentrons.com/)




## Categories
* Sample Prep
	* Plate Filling

## Description
This protocol performs an AlphaLISA [Perkin Elmer AlphaLISA](https://resources.perkinelmer.com/lab-solutions/resources/docs/GDE_Quick_AlphaLISA_conversion.pdf) based on the attached experimental protocol with user determined parameters (described below).



---



### Labware
* Opentrons Tips for P20 ([Standard](https://shop.opentrons.com/opentrons-300ul-tips-1000-refills/))
* 96-Well Low-Binding Corning Costar Microplate 3363
* 384-Well Perkin Elmer OptiPlate ([Example](https://shop.opentrons.com/nest-0-1-ml-96-well-pcr-plate-full-skirt/))


### Pipettes
[P20 8-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

### Reagents
see attached experimental protocol

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-deck-statementofwork.png)
</br>
</br>
**Slot 1**: 384-Well Perkin Elmer OptiPlate </br>
![slot 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-slot1-statementofwork.png) </br>
**Slot 2**: 384-Well Perkin Elmer OptiPlate </br>
![slot 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-slot2-statementofwork.png) </br>
**Slot 3**: 96-Well Low-Binding Microplate </br>
![slot 3](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-slot3-statementofwork.png) </br>
**Slot 5**: 96-Well Low-Binding Microplate </br>
![slot 5](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-slot5-statementofwork.png) </br>
**Slot 6**: 96-Well Low-Binding Microplate </br>
![slot 6](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/76174b/screenshot-slot6-statementofwork.png) </br>
**Slots 4,7,8,9**: Opentrons 20 uL Tips


---

### Protocol Steps
1. Use the p20 multi to transfer 8 uL sample serial dilution from slot 3 A1-A12 to slot 1 A1-A12.
2. Use the p20 multi to transfer 8 uL sample serial dilution from slot 3 A1-A12 to slot 1 B1-B12.
3. Use the p20 multi to transfer 8 uL sample serial dilution from slot 3 A1-A12 to slot 1 A13-A24.
4. Use the p20 multi to transfer 8 uL sample serial dilution from slot 3 A1-A12 to slot 1 B13-B24.
5. Use the p20 multi to transfer 4 uL ligand 1 from slot 5 A1 to slot 1 A1-A24, then B1-B24. Similarly, use the p20 multi to transfer 4 uL ligand 2 to the plate in slot 2.
6. Pause and wait for user to resume.
7. Use the p20 multi to transfer 4 uL anti-ligand from slot 6 A1 to slot 1 A1-A24.
8. Use the p20 multi to transfer 4 uL anti-ligand from slot 6 A1 to slot 1 B1-B24.
9. Use the p20 multi to transfer 4 uL anti-ligand from slot 6 A2 to slot 2 A1-A24.
10. Use the p20 multi to transfer 4 uL anti-ligand from slot 6 A2 to slot 2 B1-B24.
11. Use the p20 multi to transfer 4 uL acceptor from slot 6 A3 to slot 1 A1-A24.
12. Use the p20 multi to transfer 4 uL acceptor from slot 6 A3 to slot 1 B1-B24.
13. Use the p20 multi to transfer 4 uL acceptor from slot 6 A4 to slot 2 A1-A24.
14. Use the p20 multi to transfer 4 uL acceptor from slot 6 A4 to slot 2 B1-B24.
15. Pause and wait for user to resume.
16. Use the p20 multi to transfer 4 uL donor from slot 6 A5 to slot 1 A1-A24.
17. Use the p20 multi to transfer 4 uL donor from slot 6 A5 to slot 1 B1-B24.
18. Use the p20 multi to transfer 4 uL donor from slot 6 A6 to slot 2 A1-A24.
19. Use the p20 multi to transfer 4 uL donor from slot 6 A6 to slot 2 B1-B24.

### Process
1. Input your protocol parameters using the parameters section on this page, then download your protocol.
2. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
76174b
