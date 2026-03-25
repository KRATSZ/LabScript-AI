# Staining Cell-Based Assay Plates

### Author

[Opentrons](https://opentrons.com/)



## Categories

* Sample Prep
    * Staining

## Description

This protocol automates the staining of cell-based 384 well assay plates. It performs various washes with PBS, 4% PFA, Perm Buffer, including Primary and Secondary Antibody solutions. The protocol utilizes various reservoirs and keeps track of reagent and waste volumes.

Explanation of parameters below:

- `P300 Multi GEN2 Mount`: Specify which mount (left or right) to load the P300 multi channel pipette.
- `Number of Plates`: Total number of plates being run (Max: 6). Please follow the placement order in the deck layout below.
- `New Tip per Plate`: Everytime a plate is completed, you can either use a new tip (Always) or continue using the same tip (Never).
- `Dispense Flow Rate`: The flow rate in uL/s as liquid is dispensed throughout the protocol. The default dispense rate of a P300 Multichannel is 94 uL/s.
- `Aspiration Height from Well Bottom`: The dispensing height from the bottom of the well in (mm). A value of 0.5 means, 0.5 mm from the very bottom of the well.

---

### Labware

- [Perkin Elmer Cell Carrier Ultra 384 well plates](https://www.perkinelmer.com/product/cellcarrier-384-ultra-lid-50x1b-6057300)
- [NEST 12-Well Reservoirs, 15 mL](https://shop.opentrons.com/collections/reservoirs/products/nest-12-well-reservoir-15-ml)
- [Opentrons 300uL Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

### Pipettes

- [P300 GEN2 Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

---

### Deck Setup

![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5520f0/5520f0_deck_new.png)

### Reagent Setup

- Reservoir: Slot 8

![reservoir 2](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/5520f0/reagent_resv.png)

**Volumes Used Per Plate**:

- PBS: 172.8 mL
- PFA: 19.2 mL
- Perm: 19.2 mL
- Primary Antibody: 9.6 mL
- Secondary Antibody: 9.6 mL

**Volumes Used for 6 Plates**:

- PBS: 1,036.8 mL
- PFA: 115.2 mL
- Perm: 115.2 mL
- Primary Antibody: 57.6 mL
- Secondary Antibody: 57.6 mL

---

### Protocol Steps

- Pick up tip

1. Remove 45uL media
2. Add 50uL of PBS
3. Remove 50uL of PBS
4. Add 50uL of PBS
5. Remove 50uL of PBS
6. Add 50uL of 4% PFA
7. Pause for 20 minutes
8. Remove 50uL of 4%PFA
9. Add 50uL of perm buffer
10. Pause for 15 minutes
11. Remove 50uL of perm buffer
12. Add 50uL of PBS
13. Remove 50uL of PBS
14. Add 50uL of PBS
15. Remove 50uL of PBS
16. Add 25uL primary antibody solution
17. Pause for 60 minutes
18. Remove 25uL of primary antibody solution
19. Add 50uL of PBS
20. Remove 50uL of PBS
21. Add 50uL of PBS
22. Remove 50uL of PBS
23. Add 25uL secondary antibody + other stains cocktail
24. Pause for 30 minutes
25. Remove 25uL secondary antibody + other stains cocktail
26. Add 50uL of PBS
27. Remove 50uL of PBS
28. Add 50uL of PBS
29. Remove 50uL of PBS
30. Add 50uL of PBS

- Drop Tip

### Process

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

5520f0
