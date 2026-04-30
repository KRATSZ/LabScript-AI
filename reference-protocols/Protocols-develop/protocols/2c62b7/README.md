# Omega Bio-tek Mag-Bind Environmental DNA 96 Kit

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Nucleic Acid Extraction & Purification
    * Omega Mag-Bind Environmental DNA 96 Kit

## Description
This protocol automates the Soil Protocol from the [Mag-Bind® Environmental DNA 96 Kit](https://www.omegabiotek.com/product/mag-bind-environmental-dna-kit/?cn-reloaded=1) from Omega Bio-tek.

The protocol on the OT-2 begins at Step 14 with the addition of the XP1 Buffer and Mag-Bind® Particles RQ. These two reagents should be prepared as a master mix (referred to as Master Mix 2) in the OT-2 protocol. The first 13 steps of the protocol should be prepared and performed manually. Please refer to the protocol steps section below for corresponding OT-2 steps.

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [NEST 2 mL 96-Well Deep Well Plate](https://shop.opentrons.com/collections/lab-plates/products/nest-0-2-ml-96-well-deep-well-plate-v-bottom)
* [NEST 96 Well Plate 100 µL PCR Full Skirt](https://shop.opentrons.com/collections/lab-plates/products/nest-0-1-ml-96-well-pcr-plate-full-skirt)
* [Opentrons 96-well Aluminum Block](https://shop.opentrons.com/collections/racks-and-adapters/products/aluminum-block-set)
* [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
* [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)
* [Opentrons 200uL Filter Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-200ul-filter-tips)
* [P300 8-Channel Electronic Pipette (GEN2)](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette?variant=5984202489885)
* [Mag-Bind® Environmental DNA 96 Kit](https://www.omegabiotek.com/product/mag-bind-environmental-dna-kit/?cn-reloaded=1)

For more detailed information on compatible labware, please visit our [Labware Library](https://labware.opentrons.com/).

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

**Deck Setup**
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2c62b7/MagBind_Environment_Layout_New.png)

**Note**: The **Tip Isolator** is simply an empty Opentrons tip rack that is filled with water. The water should be filled up to the level that is enough for the tips to be slightly touching the surface of the water. The top of a standard Opentrons ti rack is detachable from the base (looks like a deep well plate). The tip isolator is used to conserve tips at specific steps.

**Reagent Setup**

* This section can contain finer detail and images describing reagent volumes and positioning in their respective labware. Examples:
* Reservoir 1: Slot 5
![Reservoir 1](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2c62b7/res1_20210623.png)
* Reservoir 2: Slot 2  
![Reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2c62b7/res2_20210623.png)

**Reagent Steps**
**Note**: Steps 1-13 are performed manually as instructed in the [kit manual](https://ensur.omegabio.com/ensur/contentAction.aspx?key=Production.4023.S2R4E1A3.20190920.67.4679917). The protocol starts on the OT-2 from step 14 and has modified steps that are written below.

14. Add 1 volume XP1 Buffer and 20 µL Mag-Bind® Particles RQ (Prepared as Master Mix 2). Mixing is performed 10 times thoroughly, referred to as `tip mixing` (start mixing from the middle, then the bottom, then back to the top)

**Note**: The master mix is thoroughly mixed and then transferred to 3 columns at a time. It is then mixed again to prevent the beads from settling in the reservoir (repeats every 3 columns of samples)

15. Incubate at Room Temp for 10 minutes while mixing (increase yields). Each column is mixed 2 times via tip mixing. Park tips in the Tip Isolator.

16. Engage Magnetic Module and Delay for 5 minutes (settling time parameter) to allow mag beads to settle on the walls. 

17. Aspirate supernatant and discard without touching the magnetic beads. Reuse tips from step 15 and discard tips.

18. Disengage Magnetic Module

19. Add max volume (300uL on P300 Pipette) of VHB Buffer to NEST 2 mL 96-Well Deep Well Plate, V Bottom (Dispensed at a fast rate to agitate the beads).

20. Tip Mixing is performed and tips are conserved in the tip isolator. (Vortexing steps are substituted with Tip Mixing)

21. Engage Magnetic Module and Delay for 5 minutes.

22. Aspirate supernatant and discard without touching the magnetic beads.

23. Disengage Magnetic Module

24. Add 500 uL of 70% Ethanol to NEST 2 mL 96-Well Deep Well Plate, V Bottom

25. Tip Mixing is performed (reuse tips from step 20).

26. Engage Magnetic Module and Delay for 5 minutes.

27. Aspirate supernatant and discard without touching the magnetic beads. 

28. Repeat 23-27 for a second ethanol wash

29. While the plate is on top of the Magnetic Module and is engaged, delay 1 minute and then remove any liquid.

30. While Magnetic Module is engaged, delay for 10 minutes to allow mag beads to dry.

31. Transfer Elution buffer from A12 of Reservoir 1 to plate on temperature module. Heat elution buffer to 70C on the Temperature Module, then transfer 100 uL of elution buffer to samples.

32. Tip Mixing is performed (Tips are discarded).

33. Engage Magnetic Module and Delay for 2 minutes to allow mag beads to settle on the walls.

34. Transfer 100 uL of  clear supernatant containing purified DNA to NEST 0.1 mL 96 Well PCR Plate, Full Skirt.

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes

If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2c62b7